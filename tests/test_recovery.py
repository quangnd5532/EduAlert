import re
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.models import Audit, PasswordRecovery, StudentAccount, User
from app.security import check_password
from app.services import recovery_delivery as delivery
from tests.conftest import login

EMAIL = 'student5@students.example.edu'
PHONE = '+84912345678'
NEW_PASSWORD = 'NewStudentPassword!2026'


def csrf(client, path='/forgot-password'):
    return re.search(r'name="csrf" value="([^"]+)"', client.get(path).text)[1]


def post(client, path, **data):
    return client.post(path, data=data, follow_redirects=False)


@pytest.fixture
def recovery(env, monkeypatch):
    client, factory = env
    with factory() as db:
        uid = db.scalar(select(User.id).where(User.username == 'student'))
        account = db.get(StudentAccount, uid)
        account.email = EMAIL
        account.phone = PHONE
        db.commit()
    sent = []
    monkeypatch.setattr(delivery, 'available', lambda channel: True)
    monkeypatch.setattr(delivery, 'send_code', lambda channel, destination, code: sent.append((channel, destination, code)))
    return client, factory, uid, sent


def issue(client, sent, channel='email', contact=EMAIL):
    token = csrf(client)
    response = post(client, '/forgot-password', csrf=token, channel=channel, contact=contact)
    assert response.status_code == 303, response.text
    assert response.headers['location'] == '/forgot-password/verify'
    return token, sent[-1][2] if sent else None


@pytest.mark.parametrize('channel,contact,expected', [('email', ' STUDENT5@students.example.edu ', EMAIL), ('phone', '0912 345 678', PHONE)])
def test_real_reset_flow_and_session_revocation(recovery, channel, contact, expected):
    client, factory, uid, sent = recovery
    login(client, 'student')
    old_cookie = client.cookies.get('edualert_session')
    client.cookies.clear()
    client.headers.pop('X-CSRF-Token')
    token, code = issue(client, sent, channel, contact)
    assert sent[-1][:2] == (channel, expected)
    verify_html = client.get('/forgot-password/verify').text
    assert code not in verify_html and '10 phút' in verify_html
    assert expected not in verify_html
    with factory() as db:
        challenge = db.scalar(select(PasswordRecovery))
        assert code != challenge.code_hash and len(challenge.code_hash) == 64
    assert post(client, '/forgot-password/verify', csrf=token, code=code).headers['location'] == '/reset-password'
    assert client.get('/reset-password').status_code == 200
    verified_cookie = client.cookies.get('edualert_session')
    assert post(client, '/reset-password', csrf=token, password=NEW_PASSWORD, confirm_password=NEW_PASSWORD).status_code == 303
    page = client.get('/login')
    assert 'Đã đặt lại mật khẩu' in page.text
    assert 'Đã đặt lại mật khẩu' not in client.get('/login').text
    with factory() as db:
        user = db.get(User, uid)
        assert check_password(user.password_hash, NEW_PASSWORD)
        assert not check_password(user.password_hash, 'TestOnlyDemo!2026')
        assert db.scalar(select(PasswordRecovery)).consumed
        log = db.scalar(select(Audit).where(Audit.action == 'password_reset'))
        assert log.detail == {'channel': channel}
    # Both an older authenticated session and a replayed reset cookie lose access.
    client.cookies.set('edualert_session', old_cookie)
    assert client.get('/api/me').status_code == 401
    client.cookies.clear()
    client.cookies.set('edualert_session', verified_cookie)
    assert post(client, '/reset-password', csrf=token, password='ReplayPassword123', confirm_password='ReplayPassword123').status_code == 400
    client.cookies.clear()
    token = csrf(client, '/login')
    assert post(client, '/login', csrf=token, username='2351000005', password=NEW_PASSWORD).status_code == 303
    assert client.get('/api/me').status_code == 200


def test_unverified_code_cannot_reset(recovery):
    client, _, _, sent = recovery
    token, _ = issue(client, sent)
    assert client.get('/reset-password', follow_redirects=False).headers['location'] == '/forgot-password'
    assert post(client, '/reset-password', csrf=token, password=NEW_PASSWORD, confirm_password=NEW_PASSWORD).status_code == 400


def test_attempt_limit_and_expiry(recovery):
    client, factory, _, sent = recovery
    token, code = issue(client, sent)
    for _ in range(5):
        assert post(client, '/forgot-password/verify', csrf=token, code='invalid').status_code == 400
    assert post(client, '/forgot-password/verify', csrf=token, code=code).status_code == 400
    with factory() as db:
        challenge = db.scalar(select(PasswordRecovery))
        assert challenge.attempts == 5
        challenge.attempts = 0
        challenge.expires_at = int(time.time()) - 1
        db.commit()
    assert post(client, '/forgot-password/verify', csrf=token, code=code).status_code == 400


def test_fifth_correct_attempt_is_usable(recovery):
    client, _, _, sent = recovery
    token, code = issue(client, sent)
    for _ in range(4):
        assert post(client, '/forgot-password/verify', csrf=token, code='invalid').status_code == 400
    assert post(client, '/forgot-password/verify', csrf=token, code=code).status_code == 303
    assert post(client, '/reset-password', csrf=token, password=NEW_PASSWORD, confirm_password=NEW_PASSWORD).status_code == 303


def test_unknown_and_inactive_accounts_are_not_disclosed(recovery):
    client, factory, uid, sent = recovery
    token, _ = issue(client, sent, contact='unknown@students.example.edu')
    assert not sent
    assert 'Nếu thông tin khớp' in client.get('/forgot-password/verify').text
    assert post(client, '/forgot-password/verify', csrf=token, code='123456').status_code == 400
    with factory() as db:
        db.get(User, uid).active = False
        db.commit()
    issue(client, sent)
    assert not sent


def test_resend_cooldown_and_old_code_revoked(recovery):
    client, factory, _, sent = recovery
    token, first_code = issue(client, sent)
    assert post(client, '/forgot-password/resend', csrf=token).status_code == 429
    with factory() as db:
        first = db.scalar(select(PasswordRecovery))
        first_id = first.id
        first.created_at -= 61
        db.commit()
    assert post(client, '/forgot-password/resend', csrf=token).status_code == 303
    assert len(sent) == 2
    with factory() as db:
        assert db.get(PasswordRecovery, first_id).consumed
    assert post(client, '/forgot-password/verify', csrf=token, code=sent[-1][2]).status_code == 303


def test_destination_limit_survives_new_browser_session(recovery):
    client, factory, _, sent = recovery
    for index in range(5):
        if index:
            with factory() as db:
                for challenge in db.scalars(select(PasswordRecovery)):
                    challenge.created_at -= 61
                db.commit()
        issue(client, sent)
    with factory() as db:
        for challenge in db.scalars(select(PasswordRecovery)):
            challenge.created_at -= 61
        db.commit()
    client.cookies.clear()
    token = csrf(client)
    assert post(client, '/forgot-password', csrf=token, channel='email', contact=EMAIL).status_code == 429
    assert len(sent) == 5


@pytest.mark.parametrize('channel,contact', [('email', 'invalid'), ('phone', '01234'), ('other', EMAIL)])
def test_invalid_contact_is_explained(recovery, channel, contact):
    client, _, _, sent = recovery
    token = csrf(client)
    response = post(client, '/forgot-password', csrf=token, channel=channel, contact=contact)
    assert response.status_code == 400 and 'role="alert"' in response.text
    assert not sent


@pytest.mark.parametrize('password,confirm', [('short123', 'short123'), ('OnlyLettersLong', 'OnlyLettersLong'), ('12345678900', '12345678900'), (NEW_PASSWORD, 'Mismatch12345')])
def test_password_validation_keeps_verified_request(recovery, password, confirm):
    client, _, _, sent = recovery
    token, code = issue(client, sent)
    post(client, '/forgot-password/verify', csrf=token, code=code)
    response = post(client, '/reset-password', csrf=token, password=password, confirm_password=confirm)
    assert response.status_code == 400 and 'role="alert"' in response.text
    assert NEW_PASSWORD not in response.text
    assert post(client, '/reset-password', csrf=token, password=NEW_PASSWORD, confirm_password=NEW_PASSWORD).status_code == 303


def test_missing_transport_or_transport_failure_never_claims_sent(recovery, monkeypatch):
    client, factory, _, sent = recovery
    token = csrf(client)
    monkeypatch.setattr(delivery, 'available', lambda channel: False)
    response = post(client, '/forgot-password', csrf=token, channel='email', contact=EMAIL)
    assert response.status_code == 503 and 'chưa thể gửi mã' in response.text
    assert not sent
    monkeypatch.setattr(delivery, 'available', lambda channel: True)
    def fail(*args):
        raise delivery.DeliveryError('Transport down')
    monkeypatch.setattr(delivery, 'send_code', fail)
    response = post(client, '/forgot-password', csrf=token, channel='email', contact=EMAIL)
    assert response.status_code == 503 and 'Transport down' not in response.text
    with factory() as db:
        assert db.scalar(select(PasswordRecovery)).consumed


def test_contacts_require_password_and_only_modify_own_account(recovery):
    client, factory, uid, sent = recovery
    token, code = issue(client, sent)
    reset_cookie = client.cookies.get('edualert_session')
    token = login(client, 'student')
    response = post(client, '/student/profile/contacts', csrf=token, email='updated@students.example.edu', phone='0987654321', current_password='wrong')
    assert response.status_code == 400
    assert 'Mật khẩu hiện tại chưa đúng' in response.text
    with factory() as db:
        assert db.get(StudentAccount, uid).email == EMAIL
    response = post(client, '/student/profile/contacts', csrf=token, email='UPDATED@students.example.edu', phone='0987654321', current_password='TestOnlyDemo!2026', user_id='1')
    assert response.status_code == 303
    assert 'Đã lưu thông tin khôi phục' in client.get('/student/profile').text
    assert client.get('/api/me').status_code == 200
    with factory() as db:
        assert db.get(StudentAccount, uid).email == 'updated@students.example.edu'
        assert db.get(StudentAccount, uid).phone == '+84987654321'
        assert db.scalar(select(PasswordRecovery)).consumed
    # Previously issued code cannot be used after changing contacts.
    client.cookies.clear()
    client.cookies.set('edualert_session', reset_cookie)
    client.headers.pop('X-CSRF-Token')
    assert post(client, '/forgot-password/verify', csrf=csrf(client), code=code).status_code == 400


def test_contacts_reject_duplicates_and_staff(recovery):
    client, factory, uid, _ = recovery
    with factory() as db:
        other = db.scalar(select(StudentAccount).where(StudentAccount.user_id != uid))
        other.email = 'occupied@students.example.edu'
        db.commit()
    token = login(client, 'student')
    response = post(client, '/student/profile/contacts', csrf=token, email='occupied@students.example.edu', current_password='TestOnlyDemo!2026')
    assert response.status_code == 400
    with factory() as db:
        assert db.get(StudentAccount, uid).email == EMAIL
    token = login(client, 'advisor1')
    assert post(client, '/student/profile/contacts', csrf=token, email=EMAIL, current_password='TestOnlyDemo!2026').status_code == 403


def test_csrf_and_clean_public_pages(env):
    client, _ = env
    for path in ['/forgot-password', '/forgot-password/verify', '/forgot-password/resend', '/reset-password', '/student/profile/contacts']:
        assert post(client, path).status_code == 403
    for path in ['/login', '/forgot-password', '/forgot-password?channel=phone']:
        response = client.get(path)
        assert response.status_code == 200
        assert 'Tài khoản trải nghiệm' not in response.text
        assert 'giả lập' not in response.text
        assert '/docs' not in response.text
        assert '/static/auth.js' in response.text
    assert 'type="tel"' in client.get('/forgot-password?channel=phone').text


def test_smtp_delivery_uses_tls_and_sends_expected_recipient(monkeypatch):
    events = []
    class SMTP:
        def __init__(self, host, port, **kwargs):
            events.append((host, port))
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def starttls(self, **kwargs): events.append('tls')
        def login(self, user, password): events.append('login')
        def send_message(self, mail):
            assert mail['To'] == EMAIL and '123456' in mail.get_content()
            events.append('send')
            return {}
    monkeypatch.setenv('EDUALERT_SMTP_HOST', 'smtp.example.edu')
    monkeypatch.setenv('EDUALERT_MAIL_FROM', 'edualert@example.edu')
    monkeypatch.setenv('EDUALERT_SMTP_USER', 'sender')
    monkeypatch.setenv('EDUALERT_SMTP_PASSWORD', 'test-only')
    monkeypatch.setenv('EDUALERT_SMTP_SSL', 'false')
    monkeypatch.setattr(delivery.smtplib, 'SMTP', SMTP)
    delivery.send_code('email', EMAIL, '123456')
    assert events == [('smtp.example.edu', 587), 'tls', 'login', 'send']


def test_sms_delivery_uses_https_contract_and_rejects_errors(monkeypatch):
    monkeypatch.setenv('EDUALERT_SMS_URL', 'https://sms.example.edu/send')
    monkeypatch.setenv('EDUALERT_SMS_TOKEN', 'test-token')
    statuses = iter([202, 500, 302])
    class Client:
        def __init__(self, **kwargs): assert kwargs['follow_redirects'] is False
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def post(self, url, headers, json):
            assert headers['Authorization'] == 'Bearer test-token'
            assert json['to'] == PHONE and '123456' in json['message']
            return type('Response', (), {'status_code': next(statuses)})()
    monkeypatch.setattr(delivery.httpx, 'Client', Client)
    delivery.send_code('phone', PHONE, '123456')
    for _ in range(2):
        with pytest.raises(delivery.DeliveryError): delivery.send_code('phone', PHONE, '123456')
    monkeypatch.setenv('EDUALERT_SMS_URL', 'http://sms.example.edu/send')
    assert not delivery.available('phone')
