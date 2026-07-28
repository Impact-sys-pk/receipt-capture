#!/usr/bin/env python3
"""
Manually resolve a needs_review, failed, or possible_duplicate receipt.

A thin CLI over worker/resolution/service.py, per design document 4.1 and 4.4.
Everything here is argparse, rendering and prompts. Validation, categorisation,
filing, locking and the audit row all live in the service, which the console and
the resolution back-feed call too. Four callers, one implementation: three
independent implementations of resolution is what caused the divergence the design
exists to fix.

Usage:
    python resolve_receipt.py <receipt_id>
    python resolve_receipt.py <receipt_id> --supplier "Corrected Supplier" --gross 100.00
    python resolve_receipt.py <receipt_id> --duplicate-decision file  # or "discard"
"""

import argparse
import getpass
import logging
import sys

import config
from worker.categorisation.engine import CategorisationEngine
from worker.database.repository import Repository
from worker.database.schema import init_db
from worker.logging_setup import attach_log_handler
from worker.resolution.service import (
    CORRECTABLE_FIELDS,
    ResolutionView,
    discard_receipt,
    get_resolution_view,
    parse_corrections,
    resolve_receipt,
)

logger = logging.getLogger(__name__)

# 4.4: filed and discarded are 0, everything else 1.
_SUCCESS_OUTCOMES = ("filed", "discarded")


def exit_code_for(outcome: str) -> int:
    """Map a ResolutionOutcome to a shell exit code. Anything unrecognised is 1."""
    return 0 if outcome in _SUCCESS_OUTCOMES else 1


def make_output_safe():
    """Stop the tick and cross characters killing the process on a cp1252 console.

    Pre-existing, not introduced by the move to the service: the previous CLI
    printed the same characters, and a Windows console defaulting to cp1252 raises
    UnicodeEncodeError on them. That crash lands *after* the receipt has been
    filed, so the work succeeds and the operator sees a traceback. Degrade the
    characters rather than change them, so nothing about the output changes where
    the console can encode them.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass  # not a reconfigurable stream, e.g. a StringIO under test


def default_actor() -> str:
    """Who to record for a CLI resolution. The console supplies a logged-in user."""
    try:
        return getpass.getuser()
    except Exception:
        return "cli-user"


def show_receipt_state(view: ResolutionView):
    """Display current receipt state to staff."""
    receipt = view.receipt
    extraction = view.extraction or {}

    print(f"\n{'=' * 80}")
    print(f"Receipt ID: {receipt['receipt_id']}")
    print(f"Status: {receipt['status']}")
    print(f"File: {receipt['filename']}")
    print(f"{'=' * 80}")

    if receipt['status'] == 'possible_duplicate':
        dup_id = receipt.get('duplicate_of', 'unknown')
        print(f"⚠️  POSSIBLE DUPLICATE of {dup_id}")
        print(f"   (supplier/date/amount match)")

    print("\nCurrent extraction:")
    print(f"  Supplier: {extraction.get('supplier_name') or '(not extracted)'}")
    print(f"  Date: {extraction.get('invoice_date') or '(not extracted)'}")
    print(f"  Net: {extraction.get('net_amount') or '(not extracted)'}")
    print(f"  VAT: {extraction.get('vat_amount') or '(not extracted)'}")
    print(f"  Gross: {extraction.get('gross_amount') or '(not extracted)'}")
    print(f"  Ref/Ticket: {extraction.get('receipt_ref_number') or '(not extracted)'}")
    print(f"  Time: {extraction.get('receipt_time') or '(not extracted)'}")

    if receipt['status'] in ('needs_review', 'failed'):
        notes = extraction.get('validation_notes', '(none)')
        print(f"\nValidation issue: {notes}")

    print()


def confirm_duplicated_action(receipt: dict) -> str:
    """Ask staff to confirm duplicate decision.

    Called for every `possible_duplicate` receipt that arrives without a
    `--duplicate-decision` flag, before any correction is read. Resolving a
    `possible_duplicate` is the "file it anyway" path, per design document 4.3 as
    amended, so skipping this question is the CLI filing a duplicate silently.
    """
    while True:
        choice = input(
            "Is this a genuine duplicate? (file/discard): "
        ).strip().lower()
        if choice in ('file', 'discard'):
            return choice
        print("Invalid choice. Enter 'file' or 'discard'.")


def get_corrections_interactive(extraction: dict) -> dict:
    """Interactively ask staff for corrected values.

    Returns raw text, keyed by field name, with blank answers omitted so they
    keep the existing value. Coercion is parse_corrections' job, not this
    function's: returning strings straight into validate() is what crashed the
    interactive path (design document 3.3).
    """
    corrections = {}

    fields = [
        ('supplier_name', 'Supplier name'),
        ('invoice_date', 'Invoice date (YYYY-MM-DD)'),
        ('net_amount', 'Net amount'),
        ('vat_amount', 'VAT amount'),
        ('gross_amount', 'Gross amount'),
        ('receipt_ref_number', 'Reference/ticket number'),
        ('receipt_time', 'Time (HH:MM)'),
    ]

    print("\nEnter corrected values (blank = keep existing):")
    for field, label in fields:
        current = extraction.get(field)
        prompt = f"  {label}"
        if current:
            prompt += f" [current: {current}]"
        prompt += ": "

        value = input(prompt).strip()
        if value:
            corrections[field] = value

    return corrections


def _raw_from_flags(args) -> dict:
    """Corrections supplied as flags, by key presence.

    `--vat 0` is a real correction and must not be mistaken for "no flags given",
    which is what design document 3.2 was about.
    """
    supplied = {
        'supplier_name': args.supplier,
        'invoice_date': args.invoice_date,
        'net_amount': args.net,
        'vat_amount': args.vat,
        'gross_amount': args.gross,
        'receipt_ref_number': args.ref_number,
        'receipt_time': args.time,
    }
    return {k: v for k, v in supplied.items() if v is not None}


def _report(outcome) -> int:
    """Print the outcome for an operator and return its exit code."""
    if outcome.outcome == "filed":
        print(f"✓ {outcome.message}")
        if outcome.category_code:
            print(f"  Category: {outcome.category_code} ({outcome.category_confidence})")
    elif outcome.outcome == "discarded":
        print(f"✓ {outcome.message}")
    elif outcome.outcome == "already_filed":
        # Not a failure. The operator needs to know where the file is.
        print(f"• {outcome.message}")
    else:
        print(f"✗ {outcome.message}")

    return exit_code_for(outcome.outcome)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manually resolve a receipt that needs review or confirmation."
    )
    parser.add_argument('receipt_id', help='Receipt ID to resolve')
    parser.add_argument('--supplier', help='Corrected supplier name')
    parser.add_argument('--invoice-date', help='Corrected invoice date (YYYY-MM-DD)')
    # Amounts are text and coerced by parse_corrections, so the flags path, the
    # prompts and the console form all apply the same rules and report the same
    # errors. argparse's type=float would be a second, more permissive
    # implementation: it accepts 'nan' and 'inf'.
    parser.add_argument('--net', help='Corrected net amount')
    parser.add_argument('--vat', help='Corrected VAT amount')
    parser.add_argument('--gross', help='Corrected gross amount')
    parser.add_argument('--ref-number', help='Receipt reference/ticket number')
    parser.add_argument('--time', help='Receipt time (HH:MM)')
    parser.add_argument(
        '--duplicate-decision',
        choices=['file', 'discard'],
        help='For possible_duplicate: file it anyway or discard',
    )
    parser.add_argument(
        '--actor',
        default=None,
        help='Who to record against this resolution (default: the OS user)',
    )
    return parser


def main():
    make_output_safe()
    attach_log_handler("resolve")
    args = build_parser().parse_args()
    actor = args.actor or default_actor()

    init_db()
    repo = Repository(config.DB_PATH)
    engine = CategorisationEngine(repo)

    try:
        view = get_resolution_view(repo, args.receipt_id)
        if view is None:
            print(f"ERROR: Receipt not found: {args.receipt_id}")
            return 1

        show_receipt_state(view)

        # A possible_duplicate is decided before anything else is asked. The state
        # is shown first because the answer depends on seeing it, and the two
        # receipts are named in that output.
        duplicate_decision = args.duplicate_decision
        if view.receipt['status'] == 'possible_duplicate' and duplicate_decision is None:
            duplicate_decision = confirm_duplicated_action(view.receipt)

        if view.receipt['status'] == 'possible_duplicate' and duplicate_decision == 'discard':
            return _report(discard_receipt(
                repo, args.receipt_id,
                reason="confirmed duplicate via CLI",
                actor=actor, source="cli",
            ))

        raw = _raw_from_flags(args)
        if not raw:
            if view.extraction is None:
                print("ERROR: This receipt has no extraction to correct.")
                return 1
            raw = get_corrections_interactive(view.extraction)

        corrections, field_errors = parse_corrections(raw)
        if field_errors:
            print("✗ Corrections rejected:")
            for field_name, message in field_errors.items():
                print(f"  {field_name}: {message}")
            print("Nothing was written. Re-run with corrected values.")
            return 1

        return _report(resolve_receipt(
            repo, engine, args.receipt_id, corrections,
            actor=actor, source="cli",
        ))

    except KeyboardInterrupt:
        print("\nAborted.")
        return 1
    finally:
        repo.close()


if __name__ == '__main__':
    sys.exit(main())
