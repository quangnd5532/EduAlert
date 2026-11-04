from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Settings


def evaluate(terms: list[dict], settings: Settings, cohort: str = '') -> dict:
    terms = sorted(terms, key=lambda t: (t['year'], t['semester']))
    base = {'score': None, 'level': 'no_data', 'reasons': [], 'academic': [], 'rule_name': settings.name}
    if not terms:
        return base
    if settings.cohort not in ('*', cohort):
        return {**base, 'level': 'out_of_scope'}
    current = terms[-1]
    academic = []
    if current['gpa'] < settings.academic_gpa:
        academic.append(f"GPA học kỳ {current['gpa']:.2f} < {settings.academic_gpa:.2f}")
    if current['cumulative_gpa'] < settings.academic_cumulative:
        academic.append(f"GPA tích lũy {current['cumulative_gpa']:.2f} < {settings.academic_cumulative:.2f}")
    if current['failed'] / current['registered'] >= settings.academic_failed_ratio:
        academic.append(f"Tỷ lệ tín chỉ không đạt ≥ {settings.academic_failed_ratio:.0%}")
    reasons = []

    def add(condition, label, weight):
        if condition:
            reasons.append({'text': label, 'points': weight})

    add(current['gpa'] < settings.low_gpa, f"GPA học kỳ dưới {settings.low_gpa:.2f}", settings.low_gpa_weight)
    add(len(terms) >= 3 and terms[-3]['gpa'] > terms[-2]['gpa'] > current['gpa'],
        'GPA giảm liên tiếp qua hai kỳ', settings.decline_weight)
    add(len(terms) >= 2 and current['failed'] > terms[-2]['failed'],
        'Số tín chỉ không đạt tăng so với kỳ trước', settings.failed_weight)
    add(current['previous_warnings'] >= 1, f"Đã có {current['previous_warnings']} cảnh báo trước kỳ này", settings.repeat_weight)
    add(current.get('conduct') is not None and current['conduct'] < 50,
        'Điểm rèn luyện dưới 50/100', settings.conduct_weight)
    score = min(100, sum(r['points'] for r in reasons))
    level = 'high' if score >= settings.high else 'attention' if score >= settings.attention else 'normal'
    return {**base, 'score': score, 'level': level, 'reasons': reasons, 'academic': academic}
