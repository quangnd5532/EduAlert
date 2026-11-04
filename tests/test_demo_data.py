import unittest
from app.demo_data import SEMESTERS, academic_data
from app.services.assessment import DEFAULT, evaluate


def assess(number):
    results, warnings, _ = academic_data(number)
    return evaluate(SEMESTERS,
                    [{**r, 'sequence': r['semester_id']} for r in results],
                    [{**w, 'sequence': w['semester_id']} for w in warnings], 6, DEFAULT)


class DemoDataTests(unittest.TestCase):
    def test_all_sixty_credit_histories_are_consistent(self):
        for number in range(1, 61):
            with self.subTest(student=number):
                results, warnings, debts = academic_data(number)
                self.assertEqual(len(results), 6)
                self.assertEqual(len({r['semester_id'] for r in results}), 6)
                accumulated = 0
                for r in results:
                    self.assertEqual(r['passed'] + r['failed'], r['registered'])
                    accumulated += r['passed']
                    self.assertEqual(r['accumulated'], accumulated)
                    self.assertEqual(r['student_id'], f'{number:06}')
                    self.assertTrue(r['gpa'] is None or 0 <= r['gpa'] <= 4)
                self.assertEqual(len(warnings), 0 if number == 7 else 6)
                self.assertEqual(len(debts), len({(r['semester_id'], r['course_id']) for r in debts}))

    def test_stable_demo_is_normal(self):
        result = assess(1)
        self.assertEqual(result['score'], 0)
        self.assertEqual(result['level'], 'Bình thường')

    def test_high_risk_without_rule_comes_from_real_seed_factory(self):
        result = assess(5)
        self.assertEqual(result['score'], 71.5)
        self.assertEqual(result['rule']['state'], 'false')
        self.assertIn('2.8 → 2.3 → 1.9', result['factors'][2]['reason'])

    def test_missing_demo_stays_missing(self):
        result = assess(7)
        self.assertIsNone(result['score'])
        self.assertEqual(result['level'], 'Chưa đủ dữ liệu')
        self.assertIsNone(result['factors'][2]['contribution'])
        self.assertIsNone(result['factors'][3]['contribution'])

    def test_failed_and_repeat_examples(self):
        self.assertEqual(assess(3)['factors'][1]['value'], 1)
        self.assertEqual(assess(3)['rule']['state'], 'true')
        self.assertEqual(assess(4)['factors'][3]['value'], 1)

    def test_improved_example_has_comparable_completed_periods(self):
        results, _, _ = academic_data(6)
        self.assertEqual([r['gpa'] for r in results[3:]], [1.6, 2.3, 2.9])
        self.assertEqual(assess(6)['factors'][2]['value'], 0)

if __name__ == '__main__':
    unittest.main()
