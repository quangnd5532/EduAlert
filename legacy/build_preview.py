"""Generate a read-only HTML preview without installing FastAPI. Run from repo root."""
import ast
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.demo import records
from app.risk import evaluate


def generate():
    # Read literal defaults without importing Pydantic in the dependency-free path.
    tree = ast.parse((ROOT / 'app/models.py').read_text(encoding='utf-8'))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Settings')
    settings = {}
    for node in cls.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.value, ast.Call):
            default = next(k.value for k in node.value.keywords if k.arg == 'default')
            settings[node.target.id] = ast.literal_eval(default)
    students, interventions = records()
    for s in students:
        s['latest'] = s['terms'][-1]
        s['risk'] = evaluate(s['terms'], SimpleNamespace(**settings), s['cohort'])
    data = json.dumps({'students':students,'interventions':interventions,'settings':settings}, ensure_ascii=False).replace('</', '<\\/')
    mock = '''
const PREVIEW_DATA = __DATA__;
window.fetch = async (url, options={}) => {
 const key = String(url).replace('/api/', '');
 if ((options.method || 'GET') !== 'GET') return {ok:false,json:async()=>({detail:'Đây là bản xem trước, chưa lưu dữ liệu. Khởi động FastAPI theo README để sử dụng chức năng này.'})};
 const value = PREVIEW_DATA[key];
 return {ok:value!==undefined,json:async()=>value ?? {detail:'Bản xem trước chỉ hỗ trợ xem dữ liệu minh họa.'}};
};
document.addEventListener('click', e => {
 const anchor=e.target.closest('a[href^="/api/"]');
 if(anchor){e.preventDefault();alert('Xuất và nhập tệp cần máy chủ FastAPI. Xem README.md để khởi chạy.');}
});
'''.replace('__DATA__', data)
    html = (ROOT / 'static/index.html').read_text(encoding='utf-8')
    html = html.replace('<link rel="stylesheet" href="/static/style.css">', '<style>'+(ROOT / 'static/style.css').read_text(encoding='utf-8')+'</style>')
    html = html.replace('<script src="/static/app.js" defer></script>', '')
    html = html.replace('<div class="shell">', '<div class="shell"><div style="padding:9px 20px;background:#fff0ce;color:#715214;text-align:center;font-size:12px">Bản xem trước · 24 hồ sơ minh họa · Chưa kết nối cơ sở dữ liệu · Các thao tác lưu cần FastAPI</div>')
    html = html.replace('</body>', '<script>'+mock+'</script><script>'+(ROOT / 'static/app.js').read_text(encoding='utf-8').replace('</script>', '<\\/script>')+'</script></body>')
    (ROOT / 'preview.html').write_text(html, encoding='utf-8')
    print('Created preview.html: read-only sample data; no dependencies required.')


if __name__ == '__main__':
    generate()
