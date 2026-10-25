# Source health

[Home](../README.md) · Latest collection attempt: 2026-10-25T13:06:20-04:00

| Source | Result | Rows before filtering | Details |
|---|---|---:|---|
| JobSpy: bilingual client services / Toronto, ON | ok | 40 | {&quot;errors&quot;: {}, &quot;warnings&quot;: {}} |
| JobSpy: staff scheduler / Toronto, ON | ok | 27 | {&quot;errors&quot;: {}, &quot;warnings&quot;: {}} |
| JobSpy: workforce coordinator / Toronto, ON | ok | 40 | {&quot;errors&quot;: {}, &quot;warnings&quot;: {}} |
| JobSpy: operations coordinator / Toronto, ON | ok | 40 | {&quot;errors&quot;: {}, &quot;warnings&quot;: {}} |
| JobSpy: training coordinator / Toronto, ON | ok | 21 | {&quot;errors&quot;: {}, &quot;warnings&quot;: {}} |
| JobSpy: bilingual administrative assistant / Toronto, ON | ok | 27 | {&quot;errors&quot;: {}, &quot;warnings&quot;: {}} |
| JobSpy: office coordinator / Toronto, ON | ok | 40 | {&quot;errors&quot;: {}, &quot;warnings&quot;: {}} |
| JobSpy: bilingual customer service / Toronto, ON | ok | 40 | {&quot;errors&quot;: {}, &quot;warnings&quot;: {}} |
| JobSpy: client service coordinator / Toronto, ON | ok | 40 | {&quot;errors&quot;: {}, &quot;warnings&quot;: {}} |
| JobSpy: banking customer service / Toronto, ON | ok | 40 | {&quot;errors&quot;: {}, &quot;warnings&quot;: {}} |
| JobSpy: bilingual insurance customer service / Toronto, ON | ok | 40 | {&quot;errors&quot;: {}, &quot;warnings&quot;: {}} |
| JobSpy: corporate receptionist / Toronto, ON | ok | 20 | {&quot;errors&quot;: {}, &quot;warnings&quot;: {}} |
| University of Toronto | ok | 4 | {&quot;errors&quot;: {}, &quot;warnings&quot;: {}} |
| City of Toronto | ok | 4 | {&quot;errors&quot;: {}, &quot;warnings&quot;: {}} |

## Coverage limits

- Automated: configured Indeed/LinkedIn searches through JobSpy, plus the employer portals listed in `config.json` when retrieval succeeds.
- Query counts and pagination are capped. A six-week lookback does not guarantee every posting from those weeks is returned.
- Search boards can return nearby cities. A separate Toronto-only location filter removes them; generic remote and GTA locations are excluded.
- Benefits, workplace and schedule extraction uses conservative text patterns. Boilerplate, negation, eligibility conditions and missing fields can cause ambiguity; all advertised terms must be confirmed.
- No confirmed transit times or applicant-specific eligibility are inferred. Salary and posting dates are source-reported.
- No dedicated sponsorship database is used. Employer-support text is a signal requiring confirmation; no candidate immigration details are stored.
- Matching is title-based screening, not a complete assessment of education, experience or licences. Training availability is not assumed.
- Failed sources retain existing listing history. Missing from search results is not proof that a job closed. A total collection failure exits nonzero.
- Verification rotates within page and time budgets. Inspect individual last-checked dates. Blocked or unsupported pages stay unverified.
- No paid API, proxy or LLM subscription is required by the code. Public board access can change or become unreliable.
