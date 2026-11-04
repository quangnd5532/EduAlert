"""Synthetic academic data shared by the seed command and dependency-free checks."""

SEMESTERS = [
    {
        'id': n,
        'name': f'HK{1 + (n - 1) % 2} · {2023 + (n - 1) // 2}–{2024 + (n - 1) // 2}',
        'sequence': n,
        'kind': 'regular',
        'completed': True,
    }
    for n in range(1, 7)
] + [{'id': 7, 'name': 'Hè 2026 (không tính xu hướng)', 'sequence': 7, 'kind': 'summer', 'completed': True}]


def academic_data(number):
    """Return result, confirmed-warning and debt rows for one fictional student."""
    if not 1 <= number <= 60:
        raise ValueError('Demo chỉ có số thứ tự 1–60')
    examples = {
        1: [3.2, 3.3, 3.1, 3.2, 3.3, 3.4],
        2: [3, 3.1, 3, 2.8, 2.3, 1.9],
        3: [2.9, 2.8, 2.7, 2.6, 2.1, 1.1],
        4: [2.5, 2.4, 2.3, 1.8, 1.5, 1.3],
        5: [3, 3.1, 3, 2.8, 2.3, 1.9],
        6: [3, 2.6, 2.1, 1.6, 2.3, 2.9],
        7: [None, 3, 2.9, 2.7, None, 2.2],
    }
    mode = number % 5
    default = (
        [3, 3.1, 3, 3.2, 3.3, 3.2] if mode == 0 else
        [3, 2.8, 2.7, 2.6, 2.2, 1.6] if mode == 1 else
        [2.5, 2.3, 2.1, 1.8, 1.4, 1.0] if mode == 2 else
        [2.4, 2.6, 2.7, 2.8, 2.8, 3.1]
    )
    gpas = examples.get(number, default)
    student_id = f'{number:06}'
    results, warnings, debts = [], [], []
    accumulated = 0
    for sequence, gpa in enumerate(gpas, 1):
        failed = (0 if gpa is None or gpa >= 3 else 2 if gpa >= 2.5 else
                  4 if gpa >= 2 else 8 if gpa >= 1.5 else 12)
        passed = 20 - failed
        accumulated += passed  # Demo assumption: no repeated passed courses.
        known = [value for value in gpas[:sequence] if value is not None]
        cumulative = round(sum(known) / len(known), 2) if known else None
        results.append({
            'student_id': student_id, 'semester_id': sequence, 'gpa': gpa,
            'cumulative_gpa': cumulative, 'registered': 20, 'passed': passed,
            'failed': failed, 'accumulated': accumulated, 'conduct': 75,
            'status': 'completed',
        })
        # These are supplied historical decisions, not today's rule-engine output.
        if number != 7:
            warnings.append({
                'student_id': student_id, 'semester_id': sequence,
                'warned': (number in (4, 5) and sequence in (3, 4, 5)) or
                          (gpa is not None and gpa < 1.2),
            })
        if failed >= 8:
            debts.append({'student_id': student_id, 'course_id': 'HP01', 'semester_id': sequence})
    return results, warnings, debts
