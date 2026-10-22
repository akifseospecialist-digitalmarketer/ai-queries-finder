# Contributing

Ideas, bug reports and pull requests are welcome.

- **A regex that catches more AI-style queries (or fewer false positives)?** Edit `references/regex-library.json`, then run `python scripts/find_ai_queries.py --check-regex` (must print `RESULT: PASS`: RE2-safe, under 4,096 characters). Regenerate `references/regex-library.md` and update the master regex in the README. Say in the PR which real query shapes it adds, anonymised.
- **Bug in a script?** Open an issue with the command you ran, the error, and (if you can) a few anonymised rows showing the column names.
- **Better playbook rules?** The strategy rules live in `references/ai-visibility-playbook.md`. Keep them specific and testable ("answer block 40-60 words"), and only add claims you can back up.
- **GSC interface changed?** Update `references/gsc-browser-workflow.md` with the new labels.

Before opening a PR, run the sample end to end (commands in the README "Without Claude" section) and make sure `verify_workbook.py` prints `RESULT: PASS`.

Please never commit real client GSC exports or reports. The `.gitignore` blocks `.csv`/`.xlsx`/`.zip` outside `examples/` for that reason.
