from html.parser import HTMLParser

from sqlalchemy import select

from app.models import Course,Followup
from app.services.data import asdict
from app.services.presentation import display_text
from tests.conftest import login


class PageText(HTMLParser):
    """Read page copy while excluding script data and stylesheet source."""
    def __init__(self):
        super().__init__();self.ignore=0;self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.ignore+=1
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.ignore=max(0,self.ignore-1)
    def handle_data(self,value):
        if not self.ignore:self.parts.append(value)
    def read(self,html):
        self.feed(html);return ' '.join(self.parts).casefold()


def test_shared_pages_use_product_copy_and_preserve_role_navigation(env):
    client,_=env
    for path in ('/login','/forgot-password'):
        html=client.get(path).text
        assert '/static/campus-ui.css' in html
        assert 'hành trình' not in PageText().read(html)
    login(client)
    for path in ('/dashboard','/students','/students/2351000005','/import','/settings','/interventions','/reports','/admin'):
        response=client.get(path);assert response.status_code==200
        text=PageText().read(response.text)
        for marker in ('phục vụ demo','giả lập','dữ liệu trải nghiệm','tài khoản trải nghiệm'):
            assert marker not in text,(path,marker)
        assert '/static/campus-ui.css' in response.text
    admin=client.get('/admin').text
    assert 'Quản trị học vụ' in admin and 'Phương thức xét tuyển' in admin
    assert 'staff-mobile-navigation' in admin and 'href="/settings"' in admin
    login(client,'advisor1')
    advisor=client.get('/dashboard').text
    for path in ('/admin','/settings','/import'):
        assert f'href="{path}"' not in advisor


def test_students_see_next_actions_and_can_expand_calculation_details(env):
    client,_=env;login(client,'student')
    overview=client.get('/student/overview').text
    assert 'Việc cần làm' in overview and 'Đặt mục tiêu học tập' in overview
    assert 'Nên trao đổi sớm với cố vấn' in overview
    assert '/ 100 điểm hỗ trợ' not in PageText().read(overview)
    analysis=client.get('/student/analysis').text
    assert '<summary>Xem cách tính điểm hỗ trợ</summary>' in analysis
    assert 'Nhận xét học tập' in analysis and 'Xem cách cải thiện GPA' in analysis
    profile=client.get('/student/profile').text
    assert profile.index('Hồ sơ sinh viên')<profile.index('id="recovery-contacts"')
    assert 'Phương thức xét tuyển' in profile
    for view in ('overview','results','analysis','planning','appointments','profile'):
        response=client.get('/student/'+view);assert response.status_code==200
        text=PageText().read(response.text)
        assert 'phục vụ demo' not in text and 'giả lập' not in text and 'dữ liệu trải nghiệm' not in text


def test_legacy_labels_are_presented_without_overwriting_stored_records(env):
    _,factory=env
    with factory() as db:
        note=db.scalar(select(Followup))
        original=note.note
        assert original.startswith('Ghi chú giả lập:')
        assert asdict(note)['note']=='Đã trao đổi mục tiêu và thống nhất buổi theo dõi.'
        assert db.get(Followup,note.id).note==original
        course=db.get(Course,'HP01')
        assert asdict(course)['name']=='Toán ứng dụng'
        assert course.name=='Toán ứng dụng (giả lập)'
    assert display_text('Bộ quy tắc minh họa phục vụ demo')=='Đánh giá học tập chung'
    assert display_text('Bản demo do người dùng đặt tên')=='Bản demo do người dùng đặt tên'
