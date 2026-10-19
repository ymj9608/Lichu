import logging
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError
from app.api.routes import router
from app.core.config import settings
from app.core.errors import AppError
from app.core.business_context import trace_id, record

app = FastAPI(title='LiChU. API', version='1.1.0', description='사내 SaaS 라이선스 신청·승인·할당·반납·회수')
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(','), allow_methods=['GET', 'POST', 'PATCH'], allow_headers=['Authorization', 'Content-Type'])
app.include_router(router)


@app.middleware('http')
async def signup_context(request: Request, call_next):
    if request.method != 'POST' or request.url.path != '/api/auth/signup':
        return await call_next(request)
    # Never trust client-supplied trace headers or read/log the request body here.
    trace = str(uuid4())
    token = trace_id.set(trace)
    lab_mode = settings.csi_lab_mode
    record('REQUEST_STARTED', trace=trace, lab_mode=lab_mode)
    try:
        response = await call_next(request)
        record('HTTP_FINISHED', trace=trace, lab_mode=lab_mode, status=response.status_code)
        response.headers['X-Trace-ID'] = trace
        return response
    except Exception:
        record('REQUEST_FAILED', trace=trace, lab_mode=lab_mode, status=500)
        raise
    finally:
        trace_id.reset(token)


@app.get('/api/csi-lab', include_in_schema=False)
def csi_lab():
    from app.core.csi_signup import lab_version
    return {'enabled': settings.csi_lab_mode, 'version': lab_version() if settings.csi_lab_mode else 'standard'}


@app.exception_handler(AppError)
async def business_error(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status, content={'code': exc.code, 'message': exc.message, 'fields': exc.fields})


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    fields = {}
    for error in exc.errors():
        key = str(error['loc'][-1])
        if key == 'body':
            key = 'password_confirm' if '비밀번호' in error['msg'] else 'end_date' if '시작일' in error['msg'] else '_form'
        fields[key] = error['msg'].removeprefix('Value error, ')
    return JSONResponse(status_code=422, content={'code': 'VALIDATION_ERROR', 'message': '입력값을 확인해주세요.', 'fields': fields})


@app.exception_handler(IntegrityError)
async def integrity_error(request: Request, exc: IntegrityError):
    logging.getLogger('lichu').warning('Database constraint conflict: %s', type(exc.orig).__name__)
    return JSONResponse(status_code=409, content={'code': 'CONFLICT', 'message': '동시에 변경된 데이터 또는 중복 정보가 있습니다. 새로고침 후 확인해주세요.', 'fields': {}})


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={'code': 'HTTP_ERROR', 'message': str(exc.detail), 'fields': {}})


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    logging.getLogger('lichu').exception('Unhandled API error')
    return JSONResponse(status_code=500, content={'code': 'INTERNAL_ERROR', 'message': '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.', 'fields': {}})
