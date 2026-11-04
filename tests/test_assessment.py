import unittest
from copy import deepcopy
from app.services.assessment import DEFAULT,evaluate,simulate,rule_result,validate_config,classify

def fixture():
    terms=[{'sequence':n,'name':f'HK{n}','kind':'regular','completed':True} for n in range(1,7)]
    gpas=[3,3,3,2.8,2.3,1.9]
    results=[{'sequence':n,'gpa':gpas[n-1],'cumulative_gpa':2.4,'registered':20,'passed':12 if n==6 else 20,'failed':8 if n==6 else 0,'status':'completed'} for n in range(1,7)]
    warnings=[{'sequence':n,'warned':n in (3,4,5)} for n in range(1,7)]
    return terms,results,warnings
class AssessmentTests(unittest.TestCase):
    def setUp(self): self.s,self.r,self.w=fixture();self.c=deepcopy(DEFAULT)
    def run_eval(self): return evaluate(self.s,self.r,self.w,6,self.c)
    def test_hand_calculation(self):
        out=self.run_eval();self.assertAlmostEqual(out['score'],71.5)
        self.assertEqual([f['contribution'] for f in out['factors']],[14,20,22.5,15])
        self.assertEqual(out['level'],'Nguy cơ cao');self.assertEqual(out['rule']['state'],'false')
    def test_classification_boundaries(self):
        for score,label in [(0,'Bình thường'),(29.999,'Bình thường'),(30,'Cần chú ý'),(59.999,'Cần chú ý'),(60,'Nguy cơ cao'),(100,'Nguy cơ cao')]:
            with self.subTest(score=score): self.assertEqual(classify(score,self.c),label)
    def test_gpa_clamps(self):
        for g,expected in [(4,0),(2.5,0),(1,1),(0,1)]:
            self.r[-1]['gpa']=g;self.assertEqual(self.run_eval()['factors'][0]['value'],expected)
    def test_fail_clamp(self):
        self.r[-1].update(failed=20,passed=0);self.assertEqual(self.run_eval()['factors'][1]['value'],1)
    def test_missing_gpa(self):
        self.r[-1]['gpa']=None;out=self.run_eval();self.assertIsNone(out['score']);self.assertIsNone(out['factors'][0]['value']);self.assertEqual(out['rule']['state'],'unknown')
    def test_zero_registered(self):
        self.r[-1].update(registered=0,passed=0,failed=0);out=self.run_eval();self.assertIsNone(out['score']);self.assertIsNone(out['factors'][1]['value'])
    def test_invalid_gpa(self):
        for value in (-.1,4.1,float('nan'),float('inf')):
            self.r[-1]['gpa']=value
            with self.assertRaises(ValueError): self.run_eval()
    def test_invalid_credits(self):
        self.r[-1]['passed']=20
        with self.assertRaises(ValueError): self.run_eval()
    def test_missing_middle_period(self):
        self.r=[r for r in self.r if r['sequence']!=5];self.assertIsNone(self.run_eval()['factors'][2]['value'])
    def test_leave_breaks_trend(self):
        self.r[-2]['status']='leave';self.assertIsNone(self.run_eval()['factors'][2]['value'])
    def test_too_few_trend_periods(self):
        self.assertIsNone(evaluate(self.s,self.r,self.w,2,self.c)['factors'][2]['value'])
    def test_unfinished_middle_semester_is_not_skipped(self):
        self.s[-2]['completed']=False
        self.assertIsNone(self.run_eval()['factors'][2]['value'])
        self.assertIsNone(self.run_eval()['factors'][3]['value'])
    def test_equal_gpa_not_strict_decline(self):
        self.r[-2]['gpa']=2.8;self.assertEqual(self.run_eval()['factors'][2]['value'],0)
    def test_increase_not_decline(self):
        self.r[-1]['gpa']=3;self.assertEqual(self.run_eval()['factors'][2]['value'],0)
    def test_summer_excluded(self):
        baseline=self.run_eval();self.s.append({'sequence':4.5,'name':'Hè','kind':'summer','completed':True});self.r.append({'sequence':4.5,'gpa':0,'registered':0,'passed':0,'failed':0,'status':'completed'})
        self.assertEqual(self.run_eval(),baseline)
    def test_unordered_semesters(self):
        baseline=self.run_eval();self.s.reverse();self.r.reverse();self.w.reverse();self.assertEqual(self.run_eval(),baseline)
    def test_no_future_leak(self):
        baseline=evaluate(self.s,self.r,self.w,5,self.c)
        self.r[-1]['gpa']=0;self.w[-1]['warned']=True
        self.assertEqual(evaluate(self.s,self.r,self.w,5,self.c),baseline)
    def test_repeat_exact_window(self):
        self.w=[{'sequence':n,'warned':n in (1,2,6)} for n in range(1,7)]
        self.assertEqual(self.run_eval()['factors'][3]['value'],0)
        self.w[3]['warned']=True;self.assertEqual(self.run_eval()['factors'][3]['value'],.5)
    def test_confirmed_no_warning_vs_unknown(self):
        for w in self.w:w['warned']=False
        self.assertEqual(self.run_eval()['factors'][3]['value'],0)
        self.w=[w for w in self.w if w['sequence']!=4];self.assertIsNone(self.run_eval()['score'])
    def test_no_configuration(self):
        out=evaluate(self.s,self.r,self.w,6);self.assertEqual(out['rule_label'],'Chưa có cấu hình áp dụng');self.assertIsNone(out['score'])
    def test_rule_or_unknown(self):
        r={'op':'OR','children':[{'field':'gpa','op':'lt','value':1.2},{'field':'conduct','op':'lt','value':50}]}
        self.assertEqual(rule_result(r,{'gpa':3})['state'],'unknown')
        self.assertEqual(rule_result(r,{'gpa':1})['state'],'true')
    def test_rule_and_three_values(self):
        r={'op':'AND','children':[{'field':'gpa','op':'lt','value':1.2},{'field':'conduct','op':'lt','value':50}]}
        self.assertEqual(rule_result(r,{'gpa':1})['state'],'unknown');self.assertEqual(rule_result(r,{'gpa':3})['state'],'false');self.assertEqual(rule_result(r,{'gpa':1,'conduct':40})['state'],'true')
    def test_unsafe_rule_rejected(self):
        self.c['rule']={'field':'__import__','op':'exec','value':0}
        with self.assertRaises(ValueError):validate_config(self.c)
    def test_weights_must_sum_100(self):
        self.c['weights']=[35,25,25,16]
        with self.assertRaises(ValueError):validate_config(self.c)
    def test_zero_denominators_rejected(self):
        for k in ('gpa_span','fail_span','trend_span','repeat_span'):
            c=deepcopy(DEFAULT);c[k]=0
            with self.subTest(k=k),self.assertRaises(ValueError):validate_config(c)
    def test_threshold_order(self):
        self.c['attention']=60;self.c['high']=30
        with self.assertRaises(ValueError):validate_config(self.c)
    def test_simulation_immutable(self):
        before=deepcopy((self.s,self.r,self.w,self.c));out=simulate(self.s,self.r,self.w,6,{'gpa':3,'registered':20,'failed':0},self.c)
        self.assertEqual(before,(self.s,self.r,self.w,self.c));self.assertEqual(out['factors'][3]['semesters'],[4,5,6]);self.assertEqual(out['factors'][2]['value'],0)
    def test_config_invalid_shape(self):
        for value in ({}, {'weights':[]}, None):
            with self.assertRaises(ValueError):validate_config(value)
if __name__=='__main__':unittest.main()
