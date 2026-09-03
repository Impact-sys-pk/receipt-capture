# Brief: commit the second refresh pass on the two step 10d briefs

**Written 2026-09-02 by the consultant session, 17:05 BST.** Documentation only.

**Report to `C:\LastingImpact\receipt_capture\2026-09-02_REPORT_claude_code_commit_175.md`.**

**No amendment.** Your three findings were all in the refreshed numbers rather than in the design document, so nothing in `2026-07-25_CONSOLE_DESIGN.md` changes.

---

## Task 1. Starting state

```
git --no-optional-locks status --porcelain
git --no-optional-locks log --oneline -2
```

**Expected HEAD `7e037c3`. Two modified tracked files and two untracked**, being your report from `7e037c3` and this brief.

| File | Bytes | md5 |
|---|---|---|
| `PROMPT_claude_code_2026-09-01_step10d_pipeline.md` | 34,659 | `e0f97e9ae6818fb5409f5ba24c4fab86` |
| `PROMPT_intellibooks_2026-09-01_step10d_desktop.md` | 24,633 | `7c271be43628d66c78ab1f87af3fba6b` |

---

## Task 2. What changed, and all three of your findings are taken

**Your first: the seventh `config.py` citation.** The `mkdir` written as a bare `:95` is now `:113`. **You were right that the grep that found six could not find it.** The pipeline brief's note now says seven and says why the first pass missed one.

**Your second: the four self-contradicting sentences.** Rather than patching those four, **every three and four digit number in the Desktop brief was enumerated and each Desktop line reference re-derived** by taking the line out of `IntelliBooks\App\IntelliBooks-Desktop-v3.html.bak-before-intellibooks-parent` and finding that exact line in the saved file. **Twenty-three more numbers moved**, so the four you found were less than a quarter of it: 671, 690, 718, 703, 983, 1165, 1181, 1201, 1206, 1208, 1209, 1210, 1688, 1702, 1706, 1793, 1819, 1978, 2475, 2847, 3105, 3167, 3203, 3204, 3210 and 3216. **All thirty-eight references were then asserted against the saved file and none mismatched.**

**Your third: the `2606` in section M is put back.** It is what sub-step 10d.38 of the design document cites, not a line in the current file, and the first pass renumbered it wrongly.

**And your note on the hash boundary is right.** The rule that reproduces 3,056 bytes and `0d0dda57d858577da806dea2e3c3e45f` is: **take from the `## A.` line inclusive to the line before the next `## B.` line, join with `\n`, no trailing newline, encode UTF-8.** **Flagged, not fixed: none of the three briefs states that rule**, and each tells its reader to stop if section A differs. It should be added to all three, which is a change to section A itself, so it is one edit repeated identically rather than a tidy-up and it is not in this commit.

---

## Task 3. Commit and push

```
docs: the step 10d briefs' line numbers, second pass

Claude Code found three faults in the first pass and all three are taken.

A seventh config.py citation in the pipeline brief was missed because it is
written as a bare :95 after the filename rather than as config.py:95, so the
grep that enumerated the set could not match one of its members while the
sentence claimed the set was complete. It is the mkdir at 10d.37 and it is
now :113.

The Desktop brief had four sentences holding one refreshed number beside
stale neighbours. Rather than patching those four, every three and four
digit number in the brief was enumerated and each line reference re-derived
from the pre-10a.2 copy against the saved file. Twenty-three more numbers
moved. All thirty-eight were then asserted against the saved file and none
mismatched.

The 2606 in section M is put back: it is what sub-step 10d.38 of the design
document cites, not a line in the current file.

Section A stays byte-identical across all three briefs at 3,056 bytes.
PROMPT_phoneapp_2026-09-01_step10d.md is unchanged; its numbers are the
phone app's index.html.

Files: PROMPT_claude_code_2026-09-01_step10d_pipeline.md,
PROMPT_intellibooks_2026-09-01_step10d_desktop.md,
2026-09-02_REPORT_claude_code_commit_174.md,
PROMPT_claude_code_2026-09-02_commit_175.md
```

**Every figure in that message enumerated before committing**, per amendment 174.

---

## Task 4. Verify, and quote every output

1. **Status after the commit.** Expected empty.
2. **Section A in all three briefs**, using the boundary rule above, stated with the result. **Expected 3,056 bytes and `0d0dda57d858577da806dea2e3c3e45f` for all three.**
3. **Every `config.py` line reference in the pipeline brief, in both forms.** Match `config\.py:[0-9]+` **and** a bare `` `:[0-9]+` `` anywhere in the file, print both sets, and say how many each returned. **Expected six and one.** Then print what each of the seven lines now holds.
4. **Every three and four digit number in the Desktop brief**, printed whole with its context, and your judgement on which are line references and which are dates, byte counts, amendment numbers or tax years. **You cannot check the line references against the file and are not asked to**; what is wanted is whether any sentence still holds two numbers that cannot both be right.
5. **The design document is not in this commit.** Confirm `2026-07-25_CONSOLE_DESIGN.md` is unmodified and that the amendment record still ends at 174.

---

## Task 5. Stop and ask about

- Any file other than the two named in task 1.
- Anything under the practice root or `C:\Intellibills\`.
- A starting state that does not match.
