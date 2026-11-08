"""One-time source transformation for the accessible blue portal palette."""
from pathlib import Path

def main():
    path=Path('app/templates/app.html');text=path.read_text(encoding='utf-8')
    start=text.find('<details>\n<summary>Nhóm 5A</summary>')
    if start!=-1:
        end=text.index('</details>',start)+len('</details>')
        text=text[:start]+text[end:]
    text=text.replace('Hỗ trợ học tập · Demo','Theo dõi và đồng hành')
    text=text.replace('Hồ sơ giả lập · Đồng hành qua từng học kỳ.','Đồng hành qua từng học kỳ.')
    text=text.replace('EduAlert · Dữ liệu giả lập phục vụ bài thi giữa kỳ.','Cổng hỗ trợ và quản lý kết quả học tập.')
    text=text.replace('<span class="demo-label">Dữ liệu demo</span>','<span class="demo-label">Dữ liệu trải nghiệm</span>')
    text=text.replace('EduAlert · Nhóm 5A','EduAlert · Cổng hỗ trợ học tập')
    path.write_text(text,encoding='utf-8')
    path=Path('static/portal.css');text=path.read_text(encoding='utf-8')
    palette={'#173b43':'#26364d','#f3f7f8':'#f4f6fb','#087f78':'#3569c8','#08766f':'#2b59ad','#05665f':'#244f9e',
             '#dce7e9':'#dce4ef','#526d76':'#586b84','#b9ced2':'#c6d2e3','#e7f2f1':'#edf2fc',
             '#123e43':'#ffffff','#e3efed':'#263d60','#a9dcca':'#3569c8','#addccc':'#3569c8',
             '#45666a':'#dce4ef','#c4d9d8':'#66778f','#d2e4e3':'#52647e','#245157':'#f0f4fb',
             '#d9eee3':'#e8efff','#154e45':'#2d58a2','#c6dcda':'#62738b','#f2f7f6':'#29436b',
             '#e0eee7':'#e7eefe','#235348':'#345ba4','#42616a':'#566b89','#edf4f3':'#f2f5fb',
             '#163e42':'#263d60','#eaf5f3':'#eef3ff','#c0dcd5':'#cbd9f3','#245951':'#304f83',
             '#e8f4ee':'#f4f7fc','#bdd5cd':'#cedbf0','#edf7f2':'#f0f4fc'}
    for old,new in palette.items():text=text.replace(old,new)
    path.write_text(text,encoding='utf-8')
    path=Path('static/portal.js');text=path.read_text(encoding='utf-8')
    text=text.replace("const colors=['#389a7b','#d3972e','#cd5369','#8f9eb4'];","const colors=['#36856b','#b47b1e','#c54f65','#8d9bb2'];")
    text=text.replace('${esc(s.class_id)}<small>','${esc(s.class_name||s.class_id)}<small>')
    path.write_text(text,encoding='utf-8')
    path=Path('app/main.py');text=path.read_text(encoding='utf-8').replace("title='EduAlert — Nhóm 5A'","title='EduAlert — Cổng hỗ trợ học tập'")
    path.write_text(text,encoding='utf-8')
    print('Updated portal palette and removed group identity from application screens.')

if __name__=='__main__':main()
