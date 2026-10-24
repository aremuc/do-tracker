import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tracker.core import assess, canonical, merge, public_jobs, apply_scope
from tracker.render import render
from tracker.sources import classify_page, verify

CONFIG = json.loads((Path(__file__).resolve().parents[1]/'config.json').read_text())
NOW='2026-10-24T12:00:00-04:00'


def raw(**changes):
    return {'title':'Client Service Coordinator', 'company':'Example Employer', 'location':'Toronto, ON, Canada',
            'description':'Permanent full-time. Hybrid. Monday to Friday. Extended health and dental coverage. French and English required.',
            'job_url':'https://example.org/jobs/1', 'site':'test', **changes}


class PreferenceTests(unittest.TestCase):
    def test_toronto_only_new_and_stored(self):
        for location in ['Markham, ON', 'Mississauga, ON', 'Brampton, ON', 'Greater Toronto Area', 'Ontario, Canada', 'Toronto / Markham, ON', 'New York, USA', 'York Region, ON']:
            with self.subTest(location=location):
                self.assertIsNone(assess(raw(location=location, is_remote=True), CONFIG))
                jobs=merge([], [raw()], CONFIG, NOW)
                jobs[0]['location']=location
                self.assertEqual(apply_scope(jobs, CONFIG, NOW)[0]['status'], 'Excluded')
        for location in ['Toronto, ON', 'Downtown Toronto, ON', 'North York, ON', 'Scarborough, ON', 'Etobicoke, ON']:
            self.assertIsNotNone(assess(raw(location=location), CONFIG))


    def test_other_language_title_not_mislabelled_as_french(self):
        record=raw(title='English & Cantonese/Mandarin Customer Service Representative')
        result=assess(record,CONFIG)
        self.assertFalse(result['bilingual_signal'])
        jobs=merge([],[raw()],CONFIG,NOW)
        jobs[0]['title']=record['title'];jobs[0]['bilingual_signal']=True
        self.assertFalse(apply_scope(jobs,CONFIG,NOW)[0]['bilingual_signal'])

    def test_advertised_preferences_make_priority_without_claiming_eligibility(self):
        result=assess(raw(),CONFIG)
        self.assertEqual(result['tier'],'Priority')
        self.assertEqual(result['benefits'],'Advertised — confirm coverage')
        self.assertEqual(result['schedule'],'Weekdays advertised')
        self.assertTrue(result['bilingual_signal'])
        self.assertTrue(any('waiting period' in f for f in result['flags']))

    def test_fulltime_does_not_infer_benefits_or_weekdays(self):
        result=assess(raw(description='Full-time office duties.'),CONFIG)
        self.assertEqual(result['tier'],'Review')
        self.assertTrue(result['benefits'].startswith('Not stated'))
        self.assertTrue(result['schedule'].startswith('Not stated'))

    def test_no_benefits_negation_wins(self):
        result=assess(raw(description='Full-time. No extended health benefits. Hybrid.'),CONFIG)
        self.assertEqual(result['benefits'],'Not offered in text')
        self.assertEqual(result['tier'],'Fallback')

    def test_weekday_plus_weekends_downgrades_priority(self):
        result=assess(raw(description=raw()['description']+' Occasional Saturdays required.'),CONFIG)
        self.assertEqual(result['tier'],'Review')
        self.assertIn('extra-hours',result['schedule'])

    def test_no_weekends_does_not_trigger_weekend_warning(self):
        result=assess(raw(description=raw()['description']+' No weekends required.'),CONFIG)
        self.assertEqual(result['schedule'],'Weekdays advertised')

    def test_commission_and_contract_are_fallbacks(self):
        for extra in [' 12-month contract position.',' Commission-only compensation.',' Temporary role.']:
            self.assertEqual(assess(raw(description=raw()['description']+extra),CONFIG)['tier'],'Fallback')

    def test_bank_customer_service_is_fallback_even_when_title_is_generic(self):
        self.assertEqual(assess(raw(title='Customer Service Representative',company='Royal Bank of Canada'),CONFIG)['tier'],'Fallback')

    def test_low_annual_pay_and_review_range(self):
        self.assertEqual(assess(raw(min_amount=38000,interval='yearly',currency='CAD'),CONFIG)['tier'],'Fallback')
        self.assertEqual(assess(raw(min_amount=42000,interval='yearly',currency='CAD'),CONFIG)['tier'],'Review')
        self.assertEqual(assess(raw(min_amount=50000,interval='yearly',currency='CAD'),CONFIG)['tier'],'Priority')

    def test_hourly_salary_is_not_annualized(self):
        self.assertIsNone(assess(raw(min_amount=25,interval='hourly'),CONFIG)['annual_base_min'])

    def test_annual_currency_is_not_invented_from_text(self):
        result=assess(raw(description=raw()['description']+' $45,000 to $55,000 per year.'),CONFIG)
        self.assertIsNone(result['annual_base_min'])
        self.assertIn('confirm currency',result['salary'])

    def test_support_is_not_assumed_and_negation_wins(self):
        self.assertEqual(assess(raw(),CONFIG)['employer_support'],'Not stated / not extracted')
        self.assertEqual(assess(raw(description='We offer visa sponsorship.'),CONFIG)['employer_support'],'Advertised — confirm with employer')
        self.assertEqual(assess(raw(description='We do not offer visa sponsorship.'),CONFIG)['employer_support'],'Not offered in text')

    def test_remote_review_and_foreign_or_distant_locations_excluded(self):
        r=assess(raw(location='Ontario, Canada',is_remote=True,description='Full-time remote role. Extended health benefits.'),CONFIG)
        self.assertIsNone(r)
        self.assertIsNone(assess(raw(location='United States',is_remote=True),CONFIG))
        self.assertIsNone(assess(raw(location='Ottawa, Ontario, Canada',is_remote=False),CONFIG))

    def test_nearby_city_requires_commute_review(self):
        self.assertIsNone(assess(raw(location='Mississauga, ON, Canada'),CONFIG))

    def test_irrelevant_titles_and_internal_roles_excluded(self):
        for title in ['Software Engineer','Registered Nurse','Retail Sales Associate','Administrative Intern','Director of Operations']:
            self.assertIsNone(assess(raw(title=title),CONFIG))
        self.assertIsNone(assess(raw(description='Internal applicants only'),CONFIG))

    def test_office_customer_service_not_excluded_by_industry(self):
        self.assertIsNotNone(assess(raw(title='Bilingual Customer Service Representative - Pharmaceutical Services'),CONFIG))
        self.assertIsNone(assess(raw(title='Pharmacist Customer Service'),CONFIG))

    def test_assistant_to_director_is_not_a_director(self):
        self.assertIsNotNone(assess(raw(title='Administrative Assistant to the Director'),CONFIG))


class HistoryTests(unittest.TestCase):
    def test_unknown_requisition_query_is_retained(self):
        self.assertEqual(canonical('https://example.org/jobs?vacancyId=123&utm_source=x'),'https://example.org/jobs?vacancyId=123')

    def test_distinct_requisitions_and_tracking_dedupe(self):
        rows=[raw(),raw(job_url='https://example.org/jobs/1?utm_source=board'),raw(job_url='https://example.org/jobs/2')]
        self.assertEqual(len(merge([],rows,CONFIG,NOW)),2)

    def test_url_bridge_merges_old_duplicates(self):
        jobs=merge([],[raw(job_url='https://example.org/1'),raw(job_url='https://indeed.com/viewjob?jk=2')],CONFIG,NOW)
        jobs=merge(jobs,[raw(job_url='https://indeed.com/viewjob?jk=2',job_url_direct='https://example.org/1')],CONFIG,NOW)
        self.assertEqual(len(jobs),1)

    def test_changed_application_url_invalidates_verification(self):
        jobs=merge([],[raw()],CONFIG,NOW);jobs[0].update(status='Posting verified',last_checked=NOW)
        jobs=merge(jobs,[raw(job_url_direct='https://employer.example/new')],CONFIG,NOW)
        self.assertEqual(jobs[0]['status'],'Unverified');self.assertNotIn('last_checked',jobs[0])

    def test_stale_is_not_closed_and_deadlines_expire(self):
        jobs=merge([],[raw()],CONFIG,'2026-10-01T12:00:00-04:00')
        self.assertEqual(apply_scope(jobs,CONFIG,NOW)[0]['status'],'Stale — recheck')
        jobs[0]['deadline']='2026-10-20'
        self.assertEqual(apply_scope(jobs,CONFIG,NOW)[0]['status'],'Closed')

    def test_new_scope_excludes_stored_irrelevant_roles_without_deleting_history(self):
        jobs=merge([],[raw()],CONFIG,NOW);jobs[0]['title']='Software Engineer'
        self.assertEqual(apply_scope(jobs,CONFIG,NOW)[0]['status'],'Excluded')
        self.assertEqual(len(jobs),1)


class SafetyAndVerificationTests(unittest.TestCase):
    def test_public_field_allowlist_and_render_escape(self):
        jobs=merge([],[raw(company='</script><script>alert(1)</script>')],CONFIG,NOW)
        jobs[0].update(candidate_name='PERSONAL_SENTINEL',notes='PERSONAL_SENTINEL',application_status='PERSONAL_SENTINEL')
        self.assertNotIn('PERSONAL_SENTINEL',json.dumps(public_jobs(jobs)))
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'tracker').mkdir();(root/'tracker/viewer.html').write_text('__JOBS__')
            render(root,jobs,[],NOW)
            out=(root/'index.html').read_text()
            self.assertNotIn('PERSONAL_SENTINEL',out);self.assertNotIn('</script>',out)
            self.assertIn('\\u003c',out)

    def test_http_success_and_generic_careers_page_are_not_verified(self):
        for content in ['<h1>Site Unavailable</h1>','<h1>Careers</h1><a href="/">Apply</a>']:
            self.assertEqual(classify_page(200,content,'Client Service Coordinator',NOW)[0],'Unverified')

    def test_explicit_closure_and_expired_posting(self):
        self.assertEqual(classify_page(200,'This job is no longer available','Role',NOW)[0],'Closed')
        content='<script type="application/ld+json">'+json.dumps({'@type':'JobPosting','title':'Role','validThrough':'2026-10-01'})+'</script>'
        self.assertEqual(classify_page(200,content,'Role',NOW)[0],'Closed')

    def test_matching_page_can_be_verified(self):
        content='<h1>Client Service Coordinator</h1>'+('Office duties. '*150)+'<a href="/apply">Apply</a>'
        self.assertEqual(classify_page(200,content,'Client Service Coordinator',NOW)[0],'Posting verified')

    def test_excluded_records_and_time_budget_defer_requests(self):
        jobs=merge([],[raw()],CONFIG,NOW)
        with patch('tracker.sources.session') as session:
            self.assertEqual(verify(jobs,{**CONFIG,'verification_time_budget_seconds':0},NOW),0)
            session.return_value.get.assert_not_called()

    def test_total_outage_preserves_existing_listing_content(self):
        from tracker import update
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'data').mkdir();(root/'tracker').mkdir();(root/'tracker/viewer.html').write_text('__JOBS__')
            (root/'config.json').write_text(json.dumps(CONFIG));jobs=merge([],[raw()],CONFIG,NOW)
            (root/'data/jobs.json').write_text(json.dumps(jobs))
            with patch.object(update,'ROOT',root),patch.object(update,'discover',return_value=([],[{'source':'Test','status':'failed'}])),patch('sys.argv',['update']):
                self.assertEqual(update.main(),1)
            self.assertEqual(json.loads((root/'data/jobs.json').read_text()),jobs)

    def test_no_unsafe_application_url(self):
        self.assertEqual(canonical('javascript:alert(1)'), '')

if __name__=='__main__':unittest.main()
