// Unit checks for the real browser script with a tiny DOM fixture, not a browser E2E test.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('static/portal.js', 'utf8');

function harness(fetchImpl = async () => ({ ok: true, json: async () => ({}) })) {
  const nodes = new Map([
    ['#catalog-data', { textContent: '{}' }],
    ['meta[name="csrf-token"]', { content: 'fixture-csrf-token' }],
  ]);
  class FixtureFormData {
    constructor(form) { this.rows = form?.rows || []; }
    [Symbol.iterator]() { return this.rows[Symbol.iterator](); }
  }
  const context = vm.createContext({
    document: {
      body: { dataset: { page: 'fixture', student: '' } },
      querySelector: selector => nodes.get(selector) || null,
      querySelectorAll: () => [],
    },
    window: {}, FormData: FixtureFormData, URLSearchParams, Date, fetch: fetchImpl,
  });
  vm.runInContext(source, context);
  return { context, nodes };
}

function assessment(overrides = {}) {
  return { score: 71.5, level: 'Nguy cơ cao', rule_label: 'Không thỏa điều kiện',
    config_id: 1, config_name: 'Minh họa', evaluated_at: '2026-11-03T00:00:00Z',
    factors: [{ name: 'GPA', weight: 35, value: .4, contribution: 14,
      reason: 'GPA 2.8 → 2.3 → 1.9', semesters: [4, 5, 6] }], missing: [], ...overrides };
}

test('student table escapes untrusted names and explains unknown separately', () => {
  const { context } = harness();
  const html = context.studentTable([{ id: '000005', name: '<img src=x onerror=alert(1)>',
    class_id: 'L1', cohort_id: 'K23', assessment: assessment({ score: null,
      level: 'Chưa đủ dữ liệu', missing: ['Thiếu lịch sử <script>'] }) }]);
  assert.ok(!html.includes('<img'));
  assert.ok(!html.includes('<script>'));
  assert.ok(html.includes('&lt;img'));
  assert.ok(html.includes('badge missing'));
  assert.ok(html.includes('/students/000005'));
  assert.ok(html.includes('Không thỏa điều kiện'));
});

test('evaluation explanation names both outcomes, version and unsaved timestamp', () => {
  const { context } = harness();
  const html = context.explanation(assessment({ rule: { op: 'lt', field: 'gpa', value: 1.2,
    actual: 1.9, state: 'false', reason: 'gpa = 1.9; lt 1.2' } }));
  for (const text of ['A. Kiểm tra cảnh báo học vụ', 'B. Điểm cảnh báo sớm', '71.50',
    '2.8 → 2.3 → 1.9', 'Cấu hình #1', '2026-11-03T00:00:00Z', 'chưa lưu phiên mới']) {
    assert.ok(html.includes(text), text);
  }
});

test('intervention rendering preserves overdue and before/after comparisons safely', () => {
  const { context } = harness();
  const html = context.renderPlans([{ id: 1, student_id: '000006', student_name: 'Giả lập',
    goal: '"><script>alert(1)</script>', action: 'Lập lịch học', overdue: true,
    status: 'Đang hỗ trợ', due_date: '2026-01-01', owner: 'Cố vấn A', evaluation_id: 10,
    comparison: { before: { gpa: 1.6, semester: 'Kỳ 4' }, after: { gpa: 2.3, semester: 'Kỳ 5' } },
    notes: [{ created_at: '2026-01-02', note: '<img src=x>' }] }]);
  assert.ok(!html.includes('<script>'));
  assert.ok(!html.includes('<img'));
  assert.ok(html.includes('Lịch hẹn quá hạn'));
  assert.ok(html.includes('1.6 (Kỳ 4)'));
  assert.ok(html.includes('2.3 (Kỳ 5)'));
  assert.ok(html.includes('không kết luận quan hệ nhân quả'));
  assert.ok(html.includes('<option selected>Đang hỗ trợ</option>'));
});

test('API sends CSRF and JSON and exposes field errors', async () => {
  let sent;
  const { context } = harness(async (url, options) => {
    sent = options;
    return { ok: false, json: async () => ({ detail: [{ loc: ['body', 'gpa'], msg: 'GPA ≤ 4' }] }) };
  });
  await assert.rejects(context.api('/api/simulate', { method: 'POST', body: { gpa: 5 } }),
    error => error.message.includes('body.gpa') && error.issues[0].loc[1] === 'gpa');
  assert.equal(sent.headers['X-CSRF-Token'], 'fixture-csrf-token');
  assert.equal(sent.headers['Content-Type'], 'application/json');
  assert.deepEqual(JSON.parse(sent.body), { gpa: 5 });
});

test('dashboard forwards the same filters to summary and semester trend', async () => {
  const calls = [];
  const { context, nodes } = harness(async url => {
    calls.push(url);
    const payload = url.startsWith('/api/summary') ? {
      total: 2, assessed: 1, open: 0, overdue: 0,
      levels: { 'Bình thường': 1, 'Cần chú ý': 0, 'Nguy cơ cao': 0, 'Chưa đủ dữ liệu': 1 },
      priority: [], interventions: {},
    } : [{ name: 'Kỳ 6', 'Bình thường': 1, 'Cần chú ý': 0, 'Nguy cơ cao': 0, 'Chưa đủ dữ liệu': 1 }];
    return { ok: true, json: async () => payload };
  });
  nodes.set('#filters', { rows: [['class_id', 'L1'], ['semester_id', '6']], querySelectorAll: () => [] });
  for (const name of ['report-context', 'metrics', 'distribution-table', 'trend-table', 'denominator', 'list']) {
    nodes.set('#' + name, { innerHTML: '', textContent: '' });
  }
  await context.loadOverview();
  assert.equal(calls.length, 2);
  for (const url of calls) {
    const params = new URLSearchParams(url.split('?')[1]);
    assert.equal(params.get('class_id'), 'L1');
    assert.equal(params.get('semester_id'), '6');
  }
  assert.ok(nodes.get('#metrics').innerHTML.includes('1 hồ sơ chưa đủ dữ liệu'));
  assert.ok(nodes.get('#distribution-table').innerHTML.includes('Chưa đủ dữ liệu'));
  assert.equal(nodes.get('#denominator').textContent, '2 sinh viên · 1 đủ dữ liệu');
});

test('empty intervention list and nested unknown rule have explicit states', () => {
  const { context } = harness();
  assert.ok(context.renderPlans([]).includes('Chưa có hồ sơ can thiệp'));
  const html = context.ruleTree({ op: 'OR', state: 'unknown', children: [
    { field: 'gpa', op: 'lt', value: 1.2, state: 'unknown', reason: 'Thiếu gpa' },
  ] });
  assert.ok(html.includes('Nhóm OR'));
  assert.ok(html.includes('Không đủ dữ liệu'));
  assert.ok(html.includes('Thiếu gpa'));
});
