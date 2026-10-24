import html
import json
from datetime import date

from .core import public_jobs


def cell(value):
    return html.escape(str(value if value is not None else 'Unknown')).replace('|', '&#124;').replace('\n', ' ')


def age_text(posted, today):
    try:
        return f'{max(0, (today - date.fromisoformat(posted[:10])).days)}d'
    except (ValueError, TypeError):
        return '—'


def table(jobs, today):
    lines = ['| Role / employer | Location | Pay | Workplace | Benefits | Posted · age | Status | Apply |',
             '|---|---|---|---|---|---|---|---|']
    for j in jobs:
        link = '<a href="' + html.escape(j['url'], quote=True) + '"><img src="https://img.shields.io/badge/Apply-blue?style=for-the-badge" alt="Apply"></a>'
        values = [cell(j['title']) + ' — ' + cell(j['company']), cell(j['location']), cell(j['salary']),
                  cell(j.get('workplace')), cell(j.get('benefits')),
                  cell(j.get('posted_date') or 'Unknown') + ' · ' + age_text(j.get('posted_date'), today),
                  cell(j['status']) + ' · ' + cell(j['tier']), link]
        lines.append('| ' + ' | '.join(values) + ' |')
    return '\n'.join(lines)


def render(root, jobs, health, now):
    jobs = public_jobs(jobs)
    today = date.fromisoformat(now[:10])
    active = sorted([j for j in jobs if j['status'] not in ('Closed', 'Excluded')],
                    key=lambda j: (j.get('posted_date') or '', j.get('first_seen') or ''), reverse=True)
    verified = sum(j['status'] == 'Posting verified' for j in active)
    observed = max((j.get('last_seen', '') for j in jobs), default='No successful collection yet')
    preferred = sorted([j for j in active if j['tier'] == 'Priority'], key=lambda j: j.get('preference_score',0), reverse=True)
    readme = f'''# Toronto Career Opportunities

Office, scheduling, operations, training and client-service opportunities in Toronto, including French/English roles.

**[Open the job website](https://aremuc.github.io/do-tracker/)** · [Plain job list](docs/ALL_JOBS.md) · [Fallbacks](docs/FALLBACK.md) · [Source health](docs/SOURCES.md) · [Maintenance](docs/MAINTENANCE.md)

**{len(active)} active leads · {verified} posting pages checked · views generated {now}**

Latest discovery evidence: **{observed}**. Rendering a page does not fetch new jobs.

## Search preferences

- Permanent full-time, advertised health/dental benefits, and weekday schedules are preferred.
- Hybrid comes first, then office-based work; remote roles remain eligible for review.
- Toronto city only, preferably downtown. Other GTA cities and generic Ontario/Canada remote listings are excluded. Toronto boroughs remain eligible; a Toronto label does not establish a downtown office.
- Prefer an annual base salary of $45,000–$50,000 or more. $40,000–$45,000 can be reviewed against benefits and hours. Missing pay is retained; hourly pay is not annualized without confirmed hours.
- Banking, insurance, temporary work and lower-paying roles are fallbacks. Weekend, shift and commission signals are flagged.

“Priority” means several advertised preferences align. It does not establish qualifications, benefit eligibility, a weekday-only schedule, or availability. Unknown details remain unknown.

## Leads with stronger advertised signals

{table(preferred[:10], today)}

## Browse and apply

**[Open the website](https://aremuc.github.io/do-tracker/)** for search, filters, saved jobs and direct application links. No account or downloads are needed once GitHub Pages is enabled. Saved jobs stay in the current browser/device and are not uploaded. The Markdown listings remain available as a fallback.

The viewer shows schedule and employer-support signals, source excerpts, and last-check dates. “Advertised” means text was detected, **not independently confirmed**. Confirm benefit coverage, employee contributions, eligibility, waiting periods and schedule with the employer.

“Posting verified” means a matching posting page was checked successfully. It does not prove that hiring is ongoing or that a particular applicant qualifies. Remote work must allow Ontario residents. Employer sponsorship/support is shown only when the text explicitly indicates it; otherwise it is unknown. Personal work authorization must be assessed separately.

## Automation

JobSpy searches Indeed and LinkedIn; configured employer portals supplement discovery. First collection searches back six weeks with capped results per query; daily collection overlaps seven days. The tracker cannot promise complete job-market coverage.

GitHub Actions is scheduled for **13:23 UTC daily** (9:23 a.m. Toronto during daylight saving, 8:23 a.m. in winter). Scheduled starts can be delayed. Ordinary code pushes run tests and regenerate views; `[refresh-jobs]` in a code-change commit requests live collection. Check Actions and source health.

The public repository contains listing data and general filters only. Keep résumés, contact details, personal immigration information, application activity and notes elsewhere. No applications are submitted automatically.
'''
    (root/'README.md').write_text(readme, encoding='utf-8')
    docs = root/'docs'; docs.mkdir(exist_ok=True)
    groups = [('ALL_JOBS',active),('FALLBACK',[j for j in active if j['tier']=='Fallback']),
              ('ARCHIVE',[j for j in jobs if j['status']=='Closed']),('EXCLUDED',[j for j in jobs if j['status']=='Excluded'])]
    for name, subset in groups:
        intro = f'# {name.replace("_"," ").title()}\n\n[Home](../README.md) · Views generated {now}\n\n'
        if name == 'ALL_JOBS':
            intro += 'One list across all categories, newest source-reported posting first. Unknown dates appear last. Check the viewer for schedule, employer-support signals, evidence and requirements.\n\n'
        (docs/f'{name}.md').write_text(intro+table(subset,today)+'\n', encoding='utf-8')
    checked = max((h.get('checked_at','') for h in health),default='') or 'Not recorded'
    source = f'# Source health\n\n[Home](../README.md) · Latest collection attempt: {checked}\n\n'
    source += '| Source | Result | Rows before filtering | Details |\n|---|---|---:|---|\n'
    for h in health:
        source += '| ' + ' | '.join([cell(h['source']),cell(h['status']),str(h.get('count',0)),cell(h.get('error') or json.dumps({'errors':h.get('errors',{}),'warnings':h.get('warnings',{})}))])+' |\n'
    source += '''
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
'''
    (docs/'SOURCES.md').write_text(source, encoding='utf-8')
    payload = json.dumps(active,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    template = (root/'tracker/viewer.html').read_text()
    (root/'index.html').write_text(template.replace('__JOBS__',payload).replace('__UPDATED__',html.escape(now)).replace('__TODAY__',today.isoformat()).replace('__DISCOVERED__',html.escape(observed)),encoding='utf-8')
