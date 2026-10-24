# Validation

This is a new independent repository built from reusable discovery, history and posting-verification components. It contains a fresh search configuration and dataset; no prior person's job-search records or private profile are included.

Local matching, preference extraction, privacy, deduplication and rendering tests are recorded during setup. Source health and per-posting dates show live retrieval results. GitHub-hosted execution must succeed before the daily workflow is called tested. A scheduled run must occur independently before scheduling itself is considered demonstrated.

Benefits and other terms detected in text are advertised signals, not employer-confirmed entitlements. A matching posting page is not proof of a current vacancy or applicant eligibility. Initial discovery searches six weeks back with capped query results. Real-browser visual testing is separate from functional viewer tests.

## Local setup checks

- 29 Python tests passed for preference extraction, negation, schedule conflicts, geography, salary treatment, privacy, history and posting verification.
- The searchable viewer passed a Node DOM harness for sorting, benefit states, French/bilingual signals, workplace and text search. This is functional testing, not a real-browser visual test.
- Six-week discovery returned 206 unique filtered leads in the initial local run. Health/dental signals were present in 66. Source-reported evidence is not employer confirmation.
- The initial University of Toronto request was blocked and recorded as failed; other discovery queries and the City of Toronto adapter returned data. See current source health for later results.

- Local posting checks examined 45 pages. Resulting statuses: {"Posting verified": 35, "Unverified": 171}. These checks do not confirm candidate qualifications or benefit eligibility.

## GitHub execution

The full [GitHub refresh run 40128738960](https://github.com/aremuc/do-tracker/actions/runs/40128738960) succeeded: Python tests, viewer tests, live collection, posting checks and publishing all passed. It produced 271 active leads with 68 matching posting pages verified. All 15 source entries reported successful retrieval; LinkedIn warned that its remote-only parameter was ignored. These counts are a setup snapshot, not permanent totals.

The final scope regression adds an industry-neutral office/customer-service case while keeping licensed pharmacist roles excluded. The final test suite has 29 Python tests. Ordinary code pushes exercise tests and rendering. The first independent scheduled run is still pending.

## Website upgrade

- Added a GitHub Pages workflow, called directly after a successful refresh so bot-generated commits do not need to trigger a second push event.
- The publishing artifact contains only validated HTML and `.nojekyll`. It rejects unrendered templates, private fields and unsafe application links.
- The interface includes simplified responsive cards, search, filters, pagination, device-local saved jobs and a short help section. Saved jobs are not uploaded.
- Browser preview, functional checks and deployment status are recorded after verification. The live Pages site requires the repository Source setting to be switched to GitHub Actions.

- Website validation: 32 Python tests and expanded viewer functional tests passed. Real-browser checks confirmed combined filters, saving a job, saved-job persistence after reload, and removing a saved job. A 390px browser iframe check showed no horizontal overflow.
- The local Pages package contains only `index.html` and `.nojekyll`. Live GitHub Pages publication is pending the one-time repository Source setting; a prepared artifact is not a deployed site.
