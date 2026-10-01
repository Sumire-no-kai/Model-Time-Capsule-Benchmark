import unittest
from test_card_api import api


class DiagnosticsTests(unittest.TestCase):
    def test_truncation_separate_from_received(self):
        manifest={'planned_runs':3,'configuration':{'max_output_tokens':8192},'attempts':[{'status':'truncated'}]*3}
        reports=[{'run_id':f'run-0{i}','objective':{'format_valid':False,'salvaged':i<3,'error':'No complete JSON block'}} for i in range(1,4)]
        counts,text=api.run_diagnostics(manifest,reports)
        self.assertEqual(counts['received_replies'],3)
        self.assertEqual(counts['format_valid_cards'],0)
        self.assertEqual(counts['truncated_runs'],3)
        self.assertEqual(counts['salvaged_cards'],2)
        self.assertIn('8192',text)
        self.assertIn('graded on the questions that were written out completely',text)

    def test_clean_run_has_no_truncation_claim(self):
        counts,text=api.run_diagnostics({'planned_runs':1,'configuration':{},'attempts':[{'status':'complete'}]},[{'run_id':'run-01','objective':{'format_valid':True}}])
        self.assertEqual(counts['format_valid_cards'],1)
        self.assertNotIn('Output was truncated',text)

    def test_reasoning_usage_kept_but_untrusted_fields_excluded(self):
        usage=api.safe_usage({'prompt_tokens':10,'completion_tokens':20,'total_tokens':100,'SECRET_FIELD':'do not save','completion_tokens_details':{'reasoning_tokens':70,'SECRET_FIELD':'do not save'},'prompt_tokens_details':{'cached_tokens':5}})
        self.assertEqual(usage['completion_tokens_details'],{'reasoning_tokens':70})
        self.assertEqual(usage['prompt_tokens_details'],{'cached_tokens':5})
        self.assertNotIn('SECRET_FIELD',str(usage))
        self.assertNotIn('reasoning_tokens',api.safe_usage({'total_tokens':100}))


if __name__=='__main__':unittest.main()
