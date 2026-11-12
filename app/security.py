import secrets
import time
from collections import defaultdict
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import Depends, HTTPException, Request, Header
from .db import get_db
from .models import User, Student, StudentAccount
hasher=PasswordHasher()
attempts=defaultdict(list)
def check_password(encoded,password):
    try: return hasher.verify(encoded,password)
    except (VerificationError,InvalidHashError): return False
def current_user(request:Request,db=Depends(get_db),csrf_header:str|None=Header(default=None,alias='X-CSRF-Token',description='Cần cho POST/PUT/PATCH/DELETE; token ở meta csrf-token sau đăng nhập')):
    user=db.get(User,request.session.get('uid')) if request.session.get('uid') else None
    if not user or not user.active or request.session.get('session_version',0)!=user.session_version:
        request.session.clear()
        raise HTTPException(401,'Vui lòng đăng nhập')
    return user
def admin(user=Depends(current_user)):
    if user.role!='admin': raise HTTPException(403,'Chỉ quản trị viên được thực hiện')
    return user
def staff(user=Depends(current_user)):
    if user.role not in ('admin','advisor'): raise HTTPException(403,'Chức năng dành cho cố vấn và quản trị viên')
    return user

def own_student(db,user):
    if user.role!='student': raise HTTPException(403,'Chức năng dành cho tài khoản sinh viên')
    link=db.get(StudentAccount,user.id)
    if not link: raise HTTPException(403,'Tài khoản chưa được liên kết hồ sơ sinh viên')
    return db.get(Student,link.student_id)
def student_access(db,user,sid):
    s=db.get(Student,sid)
    allowed = user.role=='admin' or (user.role=='advisor' and s is not None and s.advisor_id==user.id)
    if user.role=='student':
        link=db.get(StudentAccount,user.id)
        allowed=bool(link and link.student_id==sid)
    if not s or not allowed: raise HTTPException(404,'Không tìm thấy sinh viên trong phạm vi quyền')
    return s
def csrf_token(request):
    if 'csrf' not in request.session: request.session['csrf']=secrets.token_urlsafe(32)
    return request.session['csrf']
def login_allowed(key):
    now=time.monotonic();attempts[key]=[t for t in attempts[key] if now-t<300]
    if len(attempts[key])>=10: raise HTTPException(429,'Thử lại sau 5 phút')
    attempts[key].append(now)
def login_succeeded(key):
    attempts.pop(key,None)
