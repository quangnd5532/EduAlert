"""Student password recovery; codes and reset authorization remain server-side."""
import hashlib
import hmac
import re
import secrets
import time

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select, update

from ..db import get_db
from ..models import PasswordRecovery, StudentAccount, User
from ..security import csrf_token, hasher
from ..services.data import audit
from ..services import recovery_delivery as delivery
from .pages import templates

router = APIRouter(include_in_schema=False)
INVALID_CODE = 'Mã xác minh không đúng hoặc đã hết hạn. Vui lòng kiểm tra lại hoặc yêu cầu mã mới.'
UNAVAILABLE = 'Hiện chưa thể gửi mã qua kênh này. Bạn vui lòng thử kênh còn lại hoặc liên hệ bộ phận học vụ.'


def normalize_contact(channel, value):
    value = value.strip()
    if channel == 'email':
        value = value.casefold()
        if len(value) <= 254 and re.fullmatch(r'[a-z0-9.!#$%&\x27*+/=?^_`{|}~-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+', value):
            return value
        raise ValueError('Vui lòng nhập đúng địa chỉ email sinh viên đã đăng ký.')
    if channel == 'phone':
        if len(value)>30:
            raise ValueError('Vui lòng kiểm tra lại số điện thoại đã đăng ký.')
        value = re.sub(r'[\s().-]', '', value)
        if value.startswith('+84'):
            value = '0' + value[3:]
        if re.fullmatch(r'0[35789][0-9]{8}', value):
            return '+84' + value[1:]
        raise ValueError('Vui lòng nhập số điện thoại Việt Nam gồm 10 chữ số đã đăng ký.')
    raise ValueError('Vui lòng chọn email hoặc số điện thoại để khôi phục mật khẩu.')


def digest(request, value):
    return hmac.new(request.app.state.recovery_secret.encode(), value.encode(), hashlib.sha256).hexdigest()


def masked_contact(channel, value):
    if channel == 'email':
        name, domain = value.split('@')
        return name[:2] + '***@' + domain
    return '0•• ••• •' + value[-3:]


def render(request, step='request', error=None, status=200, **context):
    return templates.TemplateResponse(request=request, name='recovery.html',
        context={'csrf': csrf_token(request), 'step': step, 'error': error,
                 'channel': 'email', 'contact': '', 'destination': request.session.get('recovery_destination', ''),
                 **context}, status_code=status)


def challenge_for(request, db):
    challenge = db.get(PasswordRecovery, request.session.get('recovery_id', ''))
    if not challenge or challenge.consumed or challenge.expires_at <= int(time.time()) or (challenge.attempts >= 5 and not challenge.verified):
        return None
    return challenge


def issue_code(request, db, channel, contact=None, previous=None):
    now = int(time.time())
    destination_hash = previous.destination_hash if previous else digest(request, channel + ':' + contact)
    ip_hash = digest(request, 'ip:' + request.client.host)
    recent = db.scalar(select(func.max(PasswordRecovery.created_at)).where(
        PasswordRecovery.destination_hash == destination_hash))
    count_ip = db.scalar(select(func.count()).select_from(PasswordRecovery).where(
        PasswordRecovery.ip_hash == ip_hash, PasswordRecovery.created_at > now - 900))
    count_contact = db.scalar(select(func.count()).select_from(PasswordRecovery).where(
        PasswordRecovery.destination_hash == destination_hash, PasswordRecovery.created_at > now - 3600))
    if recent is not None and now - recent < 60:
        return 'Vui lòng đợi 60 giây giữa hai lần yêu cầu mã xác minh.', 429
    if count_ip >= 10 or count_contact >= 5:
        return 'Bạn đã yêu cầu mã nhiều lần. Vui lòng thử lại sau một giờ.', 429
    if not delivery.available(channel):
        return UNAVAILABLE, 503
    field = StudentAccount.email if channel == 'email' else StudentAccount.phone
    account = (db.get(StudentAccount, previous.user_id) if previous and previous.user_id else
               db.scalar(select(StudentAccount).where(field == contact)) if contact else None)
    if previous and account:
        contact = account.email if channel == 'email' else account.phone
        if not contact or not hmac.compare_digest(destination_hash, digest(request, channel + ':' + contact)):
            account = None
    user = db.get(User, account.user_id) if account else None
    if user and (not user.active or user.role != 'student'):
        user = None
    challenge_id = secrets.token_urlsafe(32)
    code = f'{secrets.randbelow(1_000_000):06d}'
    challenge = PasswordRecovery(id=challenge_id, user_id=user.id if user else None,
        session_version=user.session_version if user else 0, channel=channel,
        destination_hash=destination_hash, ip_hash=ip_hash,
        code_hash=digest(request, challenge_id + ':' + code), created_at=now, expires_at=now + 600)
    if user:
        try:
            delivery.send_code(channel, contact, code)
        except delivery.DeliveryError:
            # Count failed delivery attempts too; never turn an outage into unlimited sending.
            challenge.consumed = True
            db.add(challenge)
            db.commit()
            return UNAVAILABLE, 503
    if previous:
        previous.consumed = True
    db.add(challenge)
    db.commit()
    request.session['recovery_id'] = challenge_id
    if contact and not previous:
        request.session['recovery_destination'] = masked_contact(channel, contact)
    return None, 200


@router.get('/forgot-password')
def request_page(request: Request, channel: str = 'email'):
    return render(request, channel=channel if channel in ('email', 'phone') else 'email')


@router.post('/forgot-password')
def request_code(request: Request, channel: str = Form('email'), contact: str = Form(''), db=Depends(get_db)):
    try:
        normalized = normalize_contact(channel, contact)
    except ValueError as exc:
        return render(request, error=str(exc), status=400, channel=channel if channel == 'phone' else 'email', contact=contact[:254])
    error, status = issue_code(request, db, channel, normalized)
    if error:
        return render(request, error=error, status=status, channel=channel, contact=contact[:254])
    return RedirectResponse('/forgot-password/verify', 303)


@router.get('/forgot-password/verify')
def verify_page(request: Request, db=Depends(get_db)):
    challenge = challenge_for(request, db)
    if not challenge:
        return render(request, error='Yêu cầu đã hết hạn. Vui lòng nhập thông tin để nhận mã mới.', status=400)
    if challenge.verified:
        return RedirectResponse('/reset-password', 303)
    return render(request, 'verify', channel=challenge.channel, cooldown=max(0, challenge.created_at + 60 - int(time.time())))


@router.post('/forgot-password/resend')
def resend_code(request: Request, db=Depends(get_db)):
    previous = db.get(PasswordRecovery, request.session.get('recovery_id', ''))
    if not previous or previous.consumed or previous.verified:
        return RedirectResponse('/forgot-password', 303)
    error, status = issue_code(request, db, previous.channel, previous=previous)
    if error:
        return render(request, 'verify', error, status, channel=previous.channel,
                      cooldown=max(0, previous.created_at + 60 - int(time.time())))
    return RedirectResponse('/forgot-password/verify?resent=1', 303)


@router.post('/forgot-password/verify')
def verify_code(request: Request, code: str = Form(''), db=Depends(get_db)):
    challenge = challenge_for(request, db)
    if not challenge:
        return render(request, error=INVALID_CODE, status=400)
    if challenge.verified:
        return RedirectResponse('/reset-password', 303)
    # Count attempts atomically, including malformed inputs; parallel requests cannot bypass the cap.
    claimed = db.execute(update(PasswordRecovery).where(PasswordRecovery.id == challenge.id,
        PasswordRecovery.attempts < 5, PasswordRecovery.verified == False,
        PasswordRecovery.consumed == False, PasswordRecovery.expires_at > int(time.time()))
        .values(attempts=PasswordRecovery.attempts + 1))
    if claimed.rowcount != 1:
        db.rollback()
        return render(request, error=INVALID_CODE, status=400)
    valid = (bool(re.fullmatch(r'[0-9]{6}', code.strip())) and challenge.user_id is not None and
             hmac.compare_digest(challenge.code_hash, digest(request, challenge.id + ':' + code.strip())))
    if not valid:
        db.commit()
        return render(request, 'verify', INVALID_CODE, 400, channel=challenge.channel,
                      cooldown=max(0, challenge.created_at + 60 - int(time.time())))
    challenge.verified = True
    db.commit()
    return RedirectResponse('/reset-password', 303)


@router.get('/reset-password')
def reset_page(request: Request, db=Depends(get_db)):
    challenge = challenge_for(request, db)
    if not challenge or not challenge.verified:
        return RedirectResponse('/forgot-password', 303)
    return render(request, 'reset')


@router.post('/reset-password')
def reset_password(request: Request, password: str = Form(''), confirm_password: str = Form(''), db=Depends(get_db)):
    challenge = challenge_for(request, db)
    if not challenge or not challenge.verified:
        return render(request, error='Yêu cầu đã hết hạn hoặc chưa được xác minh. Vui lòng nhận mã mới.', status=400)
    if not 10 <= len(password) <= 128 or not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password):
        return render(request, 'reset', 'Mật khẩu cần từ 10–128 ký tự, có ít nhất một chữ cái và một chữ số.', 400)
    if password != confirm_password:
        return render(request, 'reset', 'Mật khẩu xác nhận chưa khớp. Vui lòng nhập lại.', 400)
    user = db.get(User, challenge.user_id)
    if not user or not user.active or user.role != 'student' or user.session_version != challenge.session_version:
        return render(request, error='Yêu cầu không còn hiệu lực. Vui lòng nhận mã mới.', status=400)
    password_hash = hasher.hash(password)
    changed = db.execute(update(User).where(User.id == user.id, User.active == True,
        User.session_version == challenge.session_version).values(
        password_hash=password_hash, session_version=User.session_version + 1))
    if changed.rowcount != 1:
        db.rollback()
        return render(request, error='Yêu cầu không còn hiệu lực. Vui lòng nhận mã mới.', status=400)
    db.execute(update(PasswordRecovery).where(PasswordRecovery.user_id == user.id).values(consumed=True))
    audit(db, user, 'password_reset', {'channel': challenge.channel})
    db.commit()
    request.session.clear()
    request.session['auth_message'] = 'Đã đặt lại mật khẩu. Bạn có thể đăng nhập bằng mật khẩu mới.'
    return RedirectResponse('/login', 303)
