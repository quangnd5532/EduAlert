import unittest
from types import SimpleNamespace
from app.risk import evaluate


def settings(**changes):
    values = dict(name='Test', cohort='*', academic_gpa=1.2, academic_cumulative=1.8,
                  academic_failed_ratio=.5, low_gpa=2, low_gpa_weight=30,
                  decline_weight=25, failed_weight=20, repeat_weight=15,
                  conduct_weight=10, attention=30, high=60)
    return SimpleNamespace(**(values | changes))


def term(year=2025, semester=1, gpa=3, **changes):
    return dict(year=year, semester=semester, gpa=gpa, cumulative_gpa=2.5,
                registered=18, passed=18, failed=0, previous_warnings=0, conduct=80) | changes


class RiskTests(unittest.TestCase):
    def test_no_data_does_not_mean_normal(self):
        result = evaluate([], settings())
        self.assertEqual(result['level'], 'no_data')
        self.assertIsNone(result['score'])

    def test_normal(self):
        self.assertEqual(evaluate([term()], settings())['score'], 0)

    def test_decline_requires_three_terms_and_sorts_chronologically(self):
        terms = [term(2025, 1, 1.5, failed=6), term(2024, 1, 3), term(2024, 2, 2.5, failed=3)]
        result = evaluate(terms, settings())
        self.assertEqual(result['score'], 75)
        self.assertEqual(result['level'], 'high')
        self.assertEqual(len(result['reasons']), 3)
        self.assertEqual(evaluate(terms[:2], settings())['score'], 50)

    def test_academic_and_early_score_are_independent(self):
        result = evaluate([term(gpa=2.8, cumulative_gpa=1.5)], settings())
        self.assertEqual(result['level'], 'normal')
        self.assertEqual(len(result['academic']), 1)

    def test_threshold_boundaries(self):
        self.assertEqual(evaluate([term(gpa=1.9)], settings())['level'], 'attention')
        self.assertEqual(evaluate([term(gpa=2)], settings())['level'], 'normal')
        self.assertEqual(evaluate([term(gpa=1.2, cumulative_gpa=1.8, failed=9)], settings())['academic'], ['Tỷ lệ tín chỉ không đạt ≥ 50%'])
        self.assertEqual(evaluate([term(gpa=1.5, previous_warnings=1)], settings(high=45))['level'], 'high')

    def test_cap_100(self):
        result = evaluate([term(2024,1,3), term(2024,2,2), term(gpa=1,failed=9,previous_warnings=2,conduct=40)], settings(low_gpa_weight=100))
        self.assertEqual(result['score'], 100)

    def test_missing_conduct_is_not_zero(self):
        self.assertEqual(evaluate([term(conduct=None)], settings())['score'], 0)

    def test_scope_is_not_normal(self):
        result = evaluate([term()], settings(cohort='2023'), '2024')
        self.assertEqual(result['level'], 'out_of_scope')
        self.assertIsNone(result['score'])

    def test_flat_or_recovered_gpa_does_not_trigger_decline(self):
        for values in ([3,2,2], [2,1,3]):
            terms = [term(2024+i//2,i%2+1,v) for i,v in enumerate(values)]
            self.assertFalse(any('liên tiếp' in r['text'] for r in evaluate(terms, settings())['reasons']))


if __name__ == '__main__':
    unittest.main()
