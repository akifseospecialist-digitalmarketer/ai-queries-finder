# Changelog

## 1.0.0 - 2026-10-22

First release.

- `SKILL.md`: browser workflow for Google Search Console using direct URLs (`metrics=`, `num_of_months=`, `breakdown=page`, `query=~regex`), the Generative AI features report, sign-in detection, table reading, single families past the 1,000-row cap and a live check of who AI cites.
- `regex-library.json`: 12 AI-query regex families plus a master regex, tested against RE2 and on a live property. Includes AI Mode follow-ups (R11) and AI-agent searches (R12); "near me" is deliberately not matched.
- `find_ai_queries.py`: reads GSC web-UI `.zip`/`.xlsx` exports and CSV/TSV, keeps queries seen in several exports once, scores each query 0-100, tags intent, clusters topics, separates AI Mode follow-ups and agent searches, flags likely AI Overview click loss, maps Generative AI report pages to topics, estimates extra clicks. `--gsc-urls`, `--print-regex`, `--check-regex`.
- `build_report.py`: 9-tab Excel working sheet (incl. AI Feature Pages) with live formulas, priorities, status dropdowns and a markdown summary.
- `verify_workbook.py`: recalculates with LibreOffice, checks formula errors, RE2 safety of every regex and 40-60 word answer blocks.
- Playbooks: GSC browser workflow, regex library, AI visibility playbook with a 7/30/90-day fast-track order.
- Fictional sample data (Gold Coast epoxy flooring) and a finished sample report.
