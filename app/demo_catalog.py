"""Current fictional population: admission-year IDs and distinct academic histories.

demo_data retains the frozen fixtures used by the historical v1 -> v2 upgrader.
"""
from .demo_data import SEMESTERS, course_catalog, student_profile as legacy_profile
from .demo_data import academic_data as legacy_academics, detailed_academics as transcript

CLASSES = {
    'L1': ('CNTT23A', 'CNTT', 'K23'), 'L2': ('CNTT24A', 'CNTT', 'K24'),
    'L3': ('QTKD23A', 'QTKD', 'K23'), 'L4': ('QTKD24A', 'QTKD', 'K24'),
    'L5': ('CNTT25A', 'CNTT', 'K25'), 'L6': ('QTKD25A', 'QTKD', 'K25'),
}
START = {'K23': 1, 'K24': 3, 'K25': 5}


def student_profile(number):
    profile = legacy_profile(number)
    advisor = profile['advisor_id']
    options = ['L1', 'L2', 'L5'] if advisor == 2 else ['L3', 'L4', 'L6']
    class_id = options[((number - 1) // 4) % 3]
    class_id = {5: 'L1', 6: 'L2', 7: 'L3', 8: 'L4'}.get(number, class_id)
    _, major, cohort = CLASSES[class_id]
    return {**profile, 'id': f'{cohort[1:]}{51 if major == "CNTT" else 52:02}{number:06}', 'class_id': class_id}


def student_id(number):
    return student_profile(number)['id']


def detailed_academics(number):
    profile = student_profile(number)
    _, major, cohort = CLASSES[profile['class_id']]
    rows, warnings, _ = legacy_academics(number)
    rows = [dict(row) for row in rows if row['semester_id'] >= START[cohort]]
    accumulated = 0
    points = 0
    credits = 0
    known = True
    patterns = [
        [3.1, 3.3, 3.4, 3.5, 3.6, 3.7], [3.3, 3.1, 2.9, 2.6, 2.2, 1.7],
        [2.4, 2.2, 2, 1.6, 1.3, 1], [1.5, 1.8, 2.1, 2.5, 2.9, 3.2],
        [2.8, 2.4, 3, 2.6, 3.2, 2.7], [2.7, 2.8, 2.6, 2.5, 2.4, 2.3],
        [3.5, 3.6, 3.4, 3.7, 3.5, 3.8], [2, 2.1, 1.9, 2.2, 2, 2.4],
    ]
    for row in rows:
        seq = row['semester_id']
        row['student_id'] = profile['id']
        if number > 8:
            gpa = round(min(4, max(.8, patterns[number % len(patterns)][seq - 1] + ((number * 7 + seq * 3) % 11 - 5) * .035)), 2)
            row['gpa'] = gpa
            proposed = 0 if gpa >= 3 else 2 if gpa >= 2.5 else 4 if gpa >= 2 else 8 if gpa >= 1.5 else 12
            row['failed'] = max(f for f in range(0, proposed + 1, 2) if f <= row['registered'] * (1 - gpa / 4) + 1e-9)
            row['passed'] = row['registered'] - row['failed']
        accumulated += row['passed']
        credits += row['registered']
        if row['gpa'] is None:
            known = False
        else:
            points += row['gpa'] * row['registered']
        row['accumulated'] = accumulated
        row['cumulative_gpa'] = round(points / credits, 2) if known else None
    warnings = [{**w, 'student_id': profile['id']} for w in warnings if w['semester_id'] >= START[cohort]]
    if number > 8:
        for warning, row in zip(warnings, rows):
            warning['warned'] = row['gpa'] < 1.2 or row['failed'] / row['registered'] >= .5
    return transcript(number, rows, warnings, major)
