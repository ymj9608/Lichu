from typing import Literal
from fastapi import APIRouter, Query
from app.api.deps import DB, Actor, Master, Employee
from app.models.entities import Department, License, LicenseRequest, LicenseAssignment
from app.repositories import hub as repo
from app.services import hub as service
from app.schemas.dto import (Signup, Login, TokenOut, UserOut, DepartmentOut, LicenseInput,
    LicensePatch, LicenseOut, RequestInput, RequestOut, AssignmentOut, Reason, DashboardOut, ErrorOut,
    ProfileUpdate, AssignmentPeriod)

errors = {status: {'model': ErrorOut, 'description': desc,
    'content': {'application/json': {'example': {'code': code, 'message': desc, 'fields': {}}}}}
    for status, code, desc in [(400, 'INVALID_TRANSITION', '잘못된 상태 전이 또는 업무 규칙 위반'),
        (401, 'UNAUTHORIZED', '로그인이 필요합니다.'), (403, 'FORBIDDEN', '권한이 없습니다.'),
        (404, 'NOT_FOUND', '해당 데이터가 없습니다.'), (409, 'CONFLICT', '중복 또는 좌석 충돌'),
        (422, 'VALIDATION_ERROR', '입력값을 확인해주세요.') ]}
router = APIRouter(prefix='/api', responses=errors)


@router.get('/departments', response_model=list[DepartmentOut], tags=['Auth'], summary='회원가입 부서 목록')
def departments(db: DB):
    return repo.rows(db, Department)


@router.post('/auth/signup', response_model=UserOut, status_code=201, tags=['Auth'], summary='직원 회원가입')
def signup(body: Signup, db: DB):
    return service.signup(db, body)


@router.post('/auth/login', response_model=TokenOut, tags=['Auth'], summary='아이디와 비밀번호 로그인')
def login(body: Login, db: DB):
    return service.login(db, body)


@router.get('/auth/me', response_model=UserOut, tags=['Auth'], summary='현재 로그인 사용자')
def me(user: Actor):
    return service.user_out(user)


@router.patch('/auth/me', response_model=UserOut, tags=['Auth'], summary='회원 정보와 프로필 사진 수정')
def edit_me(body: ProfileUpdate, db: DB, user: Actor):
    return service.update_profile(db, user, body)


@router.get('/licenses', response_model=list[LicenseOut], tags=['Licenses'], summary='라이선스 검색과 좌석 현황')
def licenses(db: DB, user: Actor, q: str | None = Query(None, max_length=150), category: str | None = Query(None, max_length=50)):
    return [service.license_out(db, row, user.id) for row in repo.licenses(db, q, category)]


@router.get('/licenses/{license_id}', response_model=LicenseOut, tags=['Licenses'], summary='라이선스 상세')
def license_detail(license_id: int, db: DB, user: Actor):
    return service.license_out(db, repo.get(db, License, license_id), user.id)


@router.post('/license-requests', response_model=RequestOut, status_code=201, tags=['Requests'], summary='사용 신청')
def request_create(body: RequestInput, db: DB, user: Employee):
    return service.create_request(db, user, body)


@router.get('/license-requests/me', response_model=list[RequestOut], tags=['Requests'], summary='내 신청과 처리 결과')
def my_requests(db: DB, user: Employee):
    return [service.request_out(db, row) for row in repo.rows(db, LicenseRequest, LicenseRequest.user_id == user.id)]


@router.post('/license-requests/{request_id}/cancel', response_model=RequestOut, tags=['Requests'], summary='내 대기 신청 취소')
def cancel(request_id: int, db: DB, user: Employee):
    return service.cancel(db, user, request_id)


@router.get('/license-assignments/me', response_model=list[AssignmentOut], tags=['Assignments'], summary='내 활성 라이선스')
def my_assignments(db: DB, user: Employee):
    return [service.assignment_out(db, row) for row in repo.rows(db, LicenseAssignment,
        LicenseAssignment.user_id == user.id, LicenseAssignment.status == 'ACTIVE')]


@router.post('/license-assignments/{assignment_id}/return', response_model=AssignmentOut, tags=['Assignments'], summary='라이선스 직접 반납')
def return_assignment(assignment_id: int, db: DB, user: Employee):
    return service.end_assignment(db, user, assignment_id)


@router.get('/admin/dashboard', response_model=DashboardOut, tags=['Admin'], summary='관리자 좌석 및 요청 요약')
def dashboard(db: DB, user: Master):
    return service.dashboard(db)


@router.get('/admin/license-requests', response_model=list[RequestOut], tags=['Admin'], summary='승인 대기 신청')
def pending(db: DB, user: Master):
    return [service.request_out(db, row) for row in repo.rows(db, LicenseRequest, LicenseRequest.status == 'PENDING')]


@router.get('/admin/license-requests/history', response_model=list[RequestOut], tags=['Admin'], summary='승인 및 반려 처리 이력')
def history(db: DB, user: Master, status: Literal['APPROVED', 'REJECTED'] | None = None):
    return [service.request_out(db, row) for row in repo.rows(db, LicenseRequest,
        LicenseRequest.status == status if status else LicenseRequest.status.in_(['APPROVED', 'REJECTED']))]


@router.post('/admin/license-requests/{request_id}/approve', response_model=RequestOut, tags=['Admin'], summary='사유와 함께 승인 및 할당')
def approve(request_id: int, body: Reason, db: DB, user: Master):
    return service.decision(db, user, request_id, body.reason, True)


@router.post('/admin/license-requests/{request_id}/reject', response_model=RequestOut, tags=['Admin'], summary='사유와 함께 반려')
def reject(request_id: int, body: Reason, db: DB, user: Master):
    return service.decision(db, user, request_id, body.reason, False)


@router.get('/admin/licenses', response_model=list[LicenseOut], tags=['Admin'], summary='관리 대상 라이선스')
def admin_licenses(db: DB, user: Master):
    return [service.license_out(db, row) for row in repo.licenses(db)]


@router.post('/admin/licenses', response_model=LicenseOut, status_code=201, tags=['Admin'], summary='라이선스 등록')
def create_license(body: LicenseInput, db: DB, user: Master):
    return service.save_license(db, body)


@router.patch('/admin/licenses/{license_id}', response_model=LicenseOut, tags=['Admin'], summary='라이선스 부분 수정')
def edit_license(license_id: int, body: LicensePatch, db: DB, user: Master):
    return service.save_license(db, body, license_id)


@router.get('/admin/licenses/{license_id}/assignments', response_model=list[AssignmentOut], tags=['Admin'], summary='현재 사용자 인사정보 및 할당')
def license_users(license_id: int, db: DB, user: Master):
    repo.get(db, License, license_id)
    return [service.assignment_out(db, row) for row in repo.rows(db, LicenseAssignment,
        LicenseAssignment.license_id == license_id, LicenseAssignment.status == 'ACTIVE')]


@router.post('/admin/license-assignments/{assignment_id}/revoke', response_model=AssignmentOut, tags=['Admin'], summary='사유와 함께 관리자 회수')
def revoke(assignment_id: int, body: Reason, db: DB, user: Master):
    return service.end_assignment(db, user, assignment_id, True, body.reason)


@router.patch('/admin/license-assignments/{assignment_id}', response_model=AssignmentOut, tags=['Admin'], summary='권한 승인 기간 수정')
def edit_assignment_period(assignment_id: int, body: AssignmentPeriod, db: DB, user: Master):
    return service.update_assignment_period(db, assignment_id, body)
