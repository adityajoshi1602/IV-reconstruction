import csv
import json
from pathlib import Path
import tempfile
import unittest
from shared_support import audit, run, COLUMNS


def row(oid, model, pred, actual=0, condition="0.1"):
    return dict(zip(COLUMNS, (condition, oid, model, actual, pred)))


class AuditTests(unittest.TestCase):
    def base(self):
        return [row("easy","linear",.1), row("hard","linear",""),
                row("easy","svi",.05), row("hard","svi",10)]
    def test_conditional_ranking_can_reverse_on_common_support(self):
        m=audit(self.base())["conditions"][0]["models"]
        self.assertLess(m["linear"]["conditional_on_own_success"]["rmse"],
                        m["svi"]["conditional_on_own_success"]["rmse"])
        self.assertGreater(m["linear"]["on_all_model_common_support"]["rmse"],
                           m["svi"]["on_all_model_common_support"]["rmse"])
    def test_coverage_keeps_failures(self):
        m=audit(self.base())["conditions"][0]["models"]
        self.assertEqual(m["linear"]["coverage"],.5)
        self.assertEqual(m["linear"]["missing_prediction_count"],1)
    def test_duplicate_rejected(self):
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            audit(self.base()+[self.base()[0]])
    def test_missing_row_rejected(self):
        with self.assertRaisesRegex(ValueError,"missing target"):
            audit(self.base()[1:])
    def test_inconsistent_truth_rejected(self):
        data=self.base();data[2]["iv"]=1
        with self.assertRaisesRegex(ValueError,"ground truth"):
            audit(data)
    def test_all_failed_has_null_not_nan(self):
        result=audit([row("x","a","NaN"),row("x","b","")])
        self.assertEqual(result["conditions"][0]["n_common_targets"],0)
        json.dumps(result,allow_nan=False)
    def test_empty_rejected(self):
        with self.assertRaises(ValueError):audit([])
    def test_infinite_truth_rejected(self):
        with self.assertRaisesRegex(ValueError,"Non-finite"):
            audit([row("x","a",0,float("inf")),row("x","b",0)])
    def test_missing_model_condition_rejected(self):
        with self.assertRaisesRegex(ValueError,"missing model"):
            audit(self.base()+[row("x","linear",1,condition="0.2")])
    def test_missing_columns_rejected(self):
        with self.assertRaisesRegex(ValueError,"missing columns"):
            audit([{}])
    def test_one_model_rejected(self):
        with self.assertRaisesRegex(ValueError,"two models"):
            audit([row("x","a",0)])
    def test_pairwise_difference_direction(self):
        r=audit([row("x","a",2),row("x","b",1)])["conditions"][0]
        self.assertEqual(r["paired_differences"][0]["mean_squared_error_difference"],3)
    def test_cli_preserves_input_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=root/'input.csv';out=root/'review'
            with source.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=COLUMNS);w.writeheader();w.writerows(self.base())
            before=source.read_bytes();result=run(source,out);saved=result.read_bytes()
            with self.assertRaises(FileExistsError):run(source,out)
            self.assertEqual(source.read_bytes(),before)
            self.assertEqual(result.read_bytes(),saved)
    def test_output_marked_post_hoc(self):
        r=audit(self.base())
        self.assertFalse(r['model_execution'])
        self.assertEqual(r['analysis_type'],'post_hoc_retained_prediction_audit')

if __name__=='__main__': unittest.main(verbosity=2)
