# Changelog

## 1.0.0 - 2026-10-22

First release.

- `SKILL.md`: browser workflow for Google Search Console (Web, last 3 months, all four metrics, site totals), master regex first, single families past the 1,000-row cap, page mapping for the top topics, live check of who AI cites.
- `regex-library.json`: 10 AI-query regex families plus a master regex, all tested against RE2 and under GSC's 4,096-character limit.
- `find_ai_queries.py`: reads GSC web-UI `.zip`/`.xlsx` exports and CSV/TSV (with or without a page column), keeps queries seen in several exports once, scores each query 0-100, tags intent, clusters topics, flags likely AI Overview click loss, estimates extra clicks. `--print-regex` and `--check-regex`.
- `build_report.py`: 8-tab Excel working sheet with live formulas, priorities, status dropdowns and a markdown summary.
- `verify_workbook.py`: recalculates with LibreOffice, checks formula errors, RE2 safety of every regex and 40-60 word answer blocks.
- Playbooks: GSC browser workflow, regex library, AI visibility playbook with a 7/30/90-day fast-track order.
- Fictional sample data (Gold Coast epoxy flooring) and a finished sample report.
