import unittest
from test_card_api import api


def attempt(run_id, **statuses):
    """A run record; question statuses are given as Q01='complete' and so on, every question of a main paper + paper B being listed."""
    base = {qid: 'complete' for qid in ('Q01', 'Q02', 'Q21', 'B01')}
    base.update(statuses)
    return {'run_id': run_id, 'status': 'complete', 'questions': {qid: {'status': status} for qid, status in base.items()}}


def report(run_id, valid=True, salvaged=False, honesty_valid=None, error='card problem'):
    result = {'run_id': run_id, 'objective': {'format_valid': valid, 'salvaged': salvaged}}
    if not valid:
        result['objective']['error'] = error
    if honesty_valid is not None:
        result['honesty'] = {'format_valid': honesty_valid, 'salvaged': False}
    return result


class DiagnosticsTests(unittest.TestCase):
    def test_truncation_is_counted_per_question_and_separate_from_received(self):
        manifest = {'planned_runs': 3, 'papers': ['main', 'honesty'], 'configuration': {'max_output_tokens': 8192},
                    'attempts': [attempt(f'run-0{i}', Q01='truncated', B01='truncated' if i == 1 else 'complete') for i in range(1, 4)]}
        reports = [report(f'run-0{i}', valid=False, salvaged=i < 3, error='No complete JSON block') for i in range(1, 4)]
        counts, text = api.run_diagnostics(manifest, reports)
        self.assertEqual(counts, {'planned_runs': 3, 'received_replies': 3, 'format_valid_cards': 0, 'truncated_runs': 3, 'truncated_questions': 4,
                                  'format_failed_runs': 3, 'salvaged_cards': 2, 'failed_requests': 0, 'requests_per_run': 4})
        self.assertIn('8192', text)
        self.assertIn('Every question is its own request', text)
        self.assertIn('affects only that question', text)
        self.assertIn('run-01: No complete JSON block', text)
        self.assertNotIn('failed or were interrupted', text)

    def test_clean_run_has_no_truncation_or_failure_claim(self):
        counts, text = api.run_diagnostics({'planned_runs': 1, 'configuration': {}, 'attempts': [attempt('run-01')]}, [report('run-01', honesty_valid=True)])
        self.assertEqual((counts['format_valid_cards'], counts['truncated_questions'], counts['failed_requests'], counts['received_replies']), (1, 0, 0, 1))
        self.assertNotIn('输出上限', text)
        self.assertNotIn('failed or were interrupted', text)
        self.assertNotIn('Format issues', text)

    def test_a_card_counts_as_valid_only_when_both_papers_are_valid(self):
        manifest = {'planned_runs': 2, 'papers': ['main', 'honesty'], 'configuration': {}, 'attempts': [attempt('run-01'), attempt('run-02')]}
        counts, _ = api.run_diagnostics(manifest, [report('run-01', honesty_valid=True), report('run-02', honesty_valid=False)])
        self.assertEqual((counts['format_valid_cards'], counts['format_failed_runs']), (1, 1))

    def test_failed_and_interrupted_requests_are_reported_and_their_runs_are_not_received(self):
        unfinished = attempt('run-02', Q02='failed', Q21='pending', B01='pending')
        unfinished['status'] = 'incomplete'
        interrupted = attempt('run-03', Q01='interrupted', Q02='pending', Q21='pending', B01='pending')
        interrupted['status'] = 'incomplete'
        manifest = {'planned_runs': 3, 'papers': ['main', 'honesty'], 'configuration': {}, 'attempts': [attempt('run-01'), unfinished, interrupted]}
        counts, text = api.run_diagnostics(manifest, [report('run-01')])
        self.assertEqual((counts['failed_requests'], counts['received_replies'], counts['planned_runs']), (2, 1, 3))
        self.assertIn('2 request(s) failed or were interrupted', text)
        self.assertIn('--resume --continue', text)
        self.assertIn('not counted as 0', text)

    def test_only_full_runs_count_toward_truncation(self):
        unfinished = attempt('run-02', Q01='truncated', Q02='failed', Q21='pending', B01='pending')    # missing data: its truncation is not a quality statistic
        unfinished['status'] = 'incomplete'
        manifest = {'planned_runs': 2, 'papers': ['main', 'honesty'], 'configuration': {}, 'attempts': [attempt('run-01', Q02='truncated'), unfinished]}
        counts, _ = api.run_diagnostics(manifest, [report('run-01', valid=False)])
        self.assertEqual((counts['truncated_runs'], counts['truncated_questions'], counts['failed_requests']), (1, 1, 1))

    def test_no_attempts_means_zero_requests_per_run(self):
        counts, text = api.run_diagnostics({'planned_runs': 5, 'configuration': {}, 'attempts': []}, [])
        self.assertEqual((counts['requests_per_run'], counts['received_replies'], counts['truncated_runs'], counts['failed_requests']), (0, 0, 0, 0))
        self.assertIn('0/5', text)

    def test_reasoning_usage_kept_but_untrusted_fields_excluded(self):
        usage = api.safe_usage({'prompt_tokens': 10, 'completion_tokens': 20, 'total_tokens': 100, 'SECRET_FIELD': 'do not save', 'completion_tokens_details': {'reasoning_tokens': 70, 'SECRET_FIELD': 'do not save'}, 'prompt_tokens_details': {'cached_tokens': 5}})
        self.assertEqual(usage['completion_tokens_details'], {'reasoning_tokens': 70})
        self.assertEqual(usage['prompt_tokens_details'], {'cached_tokens': 5})
        self.assertNotIn('SECRET_FIELD', str(usage))
        self.assertNotIn('reasoning_tokens', api.safe_usage({'total_tokens': 100}))


if __name__ == '__main__':
    unittest.main()
