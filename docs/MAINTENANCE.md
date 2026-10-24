# Maintenance

[Home](../README.md)

## Use

Open **https://aremuc.github.io/do-tracker/** after Pages is enabled. No account, downloads or repository navigation is needed. Search, filter, save jobs in the current browser, and apply on the original posting. Saved jobs are not uploaded or synced; personal application notes belong in a private document.

## Enable GitHub Pages once

1. Open repository **Settings → Pages**.
2. Under **Build and deployment → Source**, choose **GitHub Actions**.
3. Open **Actions → Publish website → Run workflow** using `main`.

No personal token or secret is needed. The GitHub connector cannot change the Pages administration setting, so this switch must be made in GitHub. Once enabled, the refresh workflow automatically publishes the exact refreshed commit. Ordinary code changes regenerate and publish the website without a live job search. The dedicated Publish website workflow can also publish existing data on demand.

The build packages only validated `index.html` and `.nojekyll`, not source files or working directories. Before Pages is enabled, packaging still runs and the deployment is explicitly skipped with setup instructions in the run summary.

## Refresh

Actions → Refresh job tracker → Run workflow. Select backfill for six weeks; normal daily lookback is seven days. The first collection automatically uses six weeks. Results per board/query are capped; a lookback is not complete coverage.

Daily schedule: 13:23 UTC. Ordinary code pushes run tests and render existing jobs. A code-change commit containing `[refresh-jobs]` requests collection. `contents: write` lets the bot publish generated listings. No external notification, login or application submission occurs.

## Local commands (Python 3.12)

```sh
python -m venv .venv
# Activate the environment using your operating system's instructions.
python -m pip install -r requirements-lock.txt
python -m unittest discover -s tests -v
python -m tracker.update --backfill
```

Use `python -m tracker.update --render-only` to regenerate views without requests. It does not advance discovery/source timestamps. `--skip-verification` can speed up collection troubleshooting while leaving postings unverified.

## Configure

Edit `config.json` for titles, query budget, salary preferences and cities. Title matching is not proof of qualification. Banking/insurance and non-permanent jobs are fallbacks. Benefits, workplace, schedules and support use text patterns; inspect evidence and confirm with employers.

Salary ranking uses explicit annual figures. Missing salary remains unknown; no take-home pay or hourly-to-annual conversion is guessed. Hybrid outranks office-based work in the preference score; remote remains eligible. A French/bilingual signal does not establish the precise language standard.

`Priority` requires full-time/permanent and health/dental benefit signals, hybrid/office arrangements, no detected weekend/shift requirement, and no known salary below the target. Missing schedule, salary, or conditional eligibility may still need review. The optional preference sort is not an AI qualification score.

## Reliability

Listings persist in `data/jobs.json` with first/last seen and check dates. Deduplication uses normalized application/source URLs and supported employer identifiers; some cross-board duplicates can remain. Distinct requisitions are not merged just because titles match.

`Posting verified` requires matching posting structure or title, description and Apply control. HTTP 200 alone is insufficient. Blocked pages remain unverified. Explicit closure, observed expired deadlines or repeated missing pages can close a posting. Missing from search results only makes it stale after 14 days.

Checks rotate within a page/time budget. Deferred checks remain labelled with their prior dates. Source failures preserve existing listings. Total collection failure reports a failed run; check `docs/SOURCES.md` and logs. Partial failure is reported even when the run can publish useful results.

The updater writes a temporary raw discovery checkpoint under ignored `tmp/` during searches. It is for local troubleshooting and is never committed. Public exports allow only job metadata fields.

## Privacy

Do not commit candidate names, contact details, résumés, immigration status/dates, personal application notes or credentials. Public history can retain deleted data. This repository contains general search preferences only. The field allowlist discards unexpected personal-tracking fields but cannot detect personal details typed into permitted listing fields.

## Dependencies and sources

Discovery uses [SpeedyApply JobSpy](https://github.com/speedyapply/JobSpy) and configured employer career pages. It is not the SpeedyApply Job Seeker Agent and does not apply to jobs. No paid service or LLM key is required by this code. Access and coverage may change.

Update locked dependencies deliberately, rerun tests and a small live query. If a portal layout changes, fix its adapter rather than treating missing markup as a successful empty feed.
