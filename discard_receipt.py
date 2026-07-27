#!/usr/bin/env python3
"""
Discard a receipt that is never going to be filed.

A thin CLI over worker/resolution/service.py's discard_receipt(), per design
document 4.4. Discarding a failed receipt had been done by hand three times before
this existed, which is why it deserves a command.

Nothing is deleted. The original file stays on disk, every extraction row stays in
the database, and the status becomes 'discarded'. The reason is required and is
stored on the audit row: it is the difference between "duplicate of r-x" and "the
client sent a bank statement by mistake".

Usage:
    python discard_receipt.py <receipt_id> --reason "confirmed duplicate of <id>"
"""

import argparse
import logging
import sys

import config
from worker.database.repository import Repository
from worker.database.schema import init_db
from worker.logging_setup import attach_log_handler
from worker.resolution.service import discard_receipt, get_resolution_view

# One definition of "who is running this" and one of the console-encoding guard,
# shared with the resolve CLI rather than copied.
from resolve_receipt import default_actor, make_output_safe

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Discard a receipt. Deletes nothing; sets its status to discarded."
    )
    parser.add_argument('receipt_id', help='Receipt ID to discard')
    parser.add_argument(
        '--reason',
        required=True,
        help='Why it is being discarded. Recorded on the audit row.',
    )
    parser.add_argument(
        '--actor',
        default=None,
        help='Who to record against this discard (default: the OS user)',
    )
    return parser


def main():
    make_output_safe()
    attach_log_handler("discard")
    args = build_parser().parse_args()

    actor = args.actor or default_actor()

    init_db()
    repo = Repository(config.DB_PATH)

    try:
        view = get_resolution_view(repo, args.receipt_id)
        if view is None:
            print(f"ERROR: Receipt not found: {args.receipt_id}")
            return 1

        print(f"\nReceipt {view.receipt['receipt_id']}")
        print(f"  Status: {view.receipt['status']}")
        print(f"  File: {view.receipt['filename']}")
        if view.receipt.get('filed_path'):
            print(f"  Filed at: {view.receipt['filed_path']}")
            print("  Note: discarding does not remove the filed copy.")
        print()

        outcome = discard_receipt(
            repo, args.receipt_id, args.reason, actor=actor, source="cli",
        )

        if outcome.outcome == "discarded":
            print(f"✓ {outcome.message}")
            return 0
        print(f"✗ {outcome.message}")
        return 1

    except KeyboardInterrupt:
        print("\nAborted.")
        return 1
    finally:
        repo.close()


if __name__ == '__main__':
    sys.exit(main())
