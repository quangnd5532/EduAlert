import os
import secrets
from pathlib import Path
from urllib.parse import parse_qs
from fastapi import FastAPI,Request,HTTPException,Depends
from fastapi.responses import RedirectResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .db import get_db
from .models import User
from .security import check_password,csrf_token,login_allowed,login_succeeded
from .routers import api,pages
from .services.data import audit

secret=os.getenv('EDUALERT_SECRET')
https=os.getenv('EDUALERT_HTTPS','false').lower()=='true'
if not secret:
    if https: raise RuntimeError('HTTPS yêu cầu EDUALERT_SECRET riêng, tối thiểu 32 ký tự')
    key=Path('data/session.key')
    if not key.exists(): key.write_text(secrets.token_urlsafe(48),encoding='utf-8')
    secret=key.read_text(encoding='utf-8').strip()
if len(secret)<32: raise RuntimeError('EDUALERT_SECRET cần tối thiểu 32 ký tự')
app=FastAPI(title='EduAlert — Nhóm 5A',version='2.0.0',docs_url=None,redoc_url=None,description='Demo học vụ; dữ liệu giả lập; điểm hỗ trợ không phải xác suất.')
@app.middleware('http')
async def protection(request:Request,call_next):
    if request.method in ('POST','PUT','PATCH','DELETE'):
        supplied=request.headers.get('x-csrf-token','')
        if not supplied and request.headers.get('content-type','').startswith('application/x-www-form-urlencoded'):
            raw=await request.body();supplied=parse_qs(raw.decode()).get('csrf',[''])[0]
        expected=request.session.get('csrf','')
        if not expected or not secrets.compare_digest(supplied.encode('utf-8'),expected.encode('utf-8')): return JSONResponse({'detail':'CSRF không hợp lệ; tải lại trang và thử lại'},403)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='same-origin'
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; form-action 'self'" if not request.url.path.startswith('/docs') else "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'"
    response.headers['Cache-Control']='no-store'
    return response
# SessionMiddleware outermost: session available to protection middleware.
app.add_middleware(SessionMiddleware,secret_key=secret,session_cookie='edualert_session',https_only=https,same_site='lax',max_age=28800)
app.mount('/static',StaticFiles(directory='static'),name='static')
app.include_router(api.router);app.include_router(pages.router)
@app.exception_handler(HTTPException)
async def http_error(request,exc):
    if exc.status_code==401 and not request.url.path.startswith('/api'): return RedirectResponse('/login',303)
    if request.url.path.startswith('/api'): return JSONResponse({'detail':exc.detail},exc.status_code)
    return pages.templates.TemplateResponse(request=request,name='message.html',context={'message':exc.detail,'csrf':csrf_token(request)},status_code=exc.status_code)
@app.exception_handler(IntegrityError)
async def conflict(request,exc): return JSONResponse({'detail':'Dữ liệu trùng hoặc tham chiếu không hợp lệ. Tải lại và kiểm tra dữ liệu.'},409)
@app.get('/login',include_in_schema=False)
def login_page(request:Request):
    return pages.templates.TemplateResponse(request=request,name='login.html',context={'csrf':csrf_token(request),'error':None,'demo':os.getenv('EDUALERT_DEMO')=='true'})
@app.post('/login',include_in_schema=False)
async def login(request:Request,db=Depends(get_db)):
    form=await request.form();username=str(form.get('username',''));password=str(form.get('password',''))
    if len(username)>80 or len(password)>128:
        raise HTTPException(422,'Tên đăng nhập hoặc mật khẩu vượt độ dài cho phép')
    login_allowed((request.client.host,username))
    u=db.scalar(select(User).where(User.username==username))
    if not u or not u.active or not check_password(u.password_hash,password):
        return pages.templates.TemplateResponse(request=request,name='login.html',context={'csrf':csrf_token(request),'error':'Tên đăng nhập hoặc mật khẩu không đúng.','demo':os.getenv('EDUALERT_DEMO')=='true'},status_code=400)
    login_succeeded((request.client.host,username))
    request.session.clear();request.session['uid']=u.id;csrf_token(request)
    audit(db,u,'login',{});db.commit();return RedirectResponse('/dashboard',303)
@app.post('/logout',include_in_schema=False)
def logout(request:Request): request.session.clear();return RedirectResponse('/login',303)
@app.get('/health',tags=['System'])
def health(): return {'status':'ok','version':'2.0.0'}
@app.get('/docs',include_in_schema=False)
def local_docs():
    return get_swagger_ui_html(openapi_url='/openapi.json',title='EduAlert API',swagger_js_url='/static/vendor/swagger-ui-bundle.js',swagger_css_url='/static/vendor/swagger-ui.css',swagger_favicon_url='/static/favicon.svg',swagger_ui_parameters={'tryItOutEnabled':True})
