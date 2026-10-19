from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.errors import AppError
from app.core.security import hash_password, verify_password, token_for
from app.core.config import settings
from app.core.csi_signup import validate_lab_signup, hash_signup_password, record_signup
from app.models.entities import CsiSignupProfile
from app.models.entities import Department, User, License, LicenseRequest, LicenseAssignment, utcnow
from app.repositories import hub as repo
from app.schemas.dto import Signup, Login, LicenseInput, LicensePatch, RequestInput, ProfileUpdate, AssignmentPeriod


def fields(row):
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}


def user_out(user):
    return {k: v for k, v in fields(user).items() if k != 'password_hash'} | {'department': user.department}


def license_out(db, row, user_id=None):
    used = repo.used(db, row.id)
    block = None
    if row.status == 'INACTIVE':
        block = 'INACTIVE'
    elif user_id and repo.has(db, LicenseAssignment, user_id, row.id, 'ACTIVE'):
        block = 'ACTIVE_ASSIGNMENT'
    elif user_id and repo.has(db, LicenseRequest, user_id, row.id, 'PENDING'):
        block = 'PENDING_REQUEST'
    return fields(row) | {'used_seats': used, 'available_seats': row.total_seats - used,
        'utilization': round(used / row.total_seats * 100, 1) if row.total_seats else 0,
        'monthly_unit_price': (row.unit_price / (12 if row.billing_cycle == 'YEARLY' else 1)).quantize(Decimal('.01')),
        'request_block': block}


def request_out(db, row):
    return fields(row) | {'user': user_out(repo.get(db, User, row.user_id)),
        'license': license_out(db, repo.get(db, License, row.license_id)),
        'processor': user_out(repo.get(db, User, row.processed_by)) if row.processed_by else None}


def assignment_out(db, row):
    request = repo.get(db, LicenseRequest, row.request_id) if row.request_id else None
    return fields(row) | {'user': user_out(repo.get(db, User, row.user_id)),
        'license': license_out(db, repo.get(db, License, row.license_id)),
        'reason': request.reason if request else None, 'end_date': request.end_date if request else None}


def signup(db: Session, payload: Signup):
    if settings.csi_lab_mode:
        validate_lab_signup(payload)
    elif payload.phone_number is not None:
        raise AppError(422, 'LAB_ONLY_FIELD', '휴대폰 번호는 CSI 실습 모드에서만 사용할 수 있습니다.')
    errors = {}
    for key in ('username', 'employee_no', 'email'):
        if db.scalar(select(User.id).where(getattr(User, key) == getattr(payload, key))):
            errors[key] = '이미 사용 중입니다.'
    if errors:
        raise AppError(409, 'DUPLICATE_USER', '가입 정보를 확인해주세요.', errors)
    if not db.get(Department, payload.department_id):
        raise AppError(422, 'INVALID_DEPARTMENT', '부서를 선택해주세요.', {'department_id': '존재하지 않는 부서입니다.'})
    user = User(**payload.model_dump(exclude={'password', 'password_confirm', 'phone_number'}),
                password_hash=hash_signup_password(payload.password) if settings.csi_lab_mode else hash_password(payload.password), role='USER')
    db.add(user)
    db.flush()
    if settings.csi_lab_mode:
        if payload.phone_number:
            db.add(CsiSignupProfile(user_id=user.id, phone_number=payload.phone_number))
            db.flush()
        record_signup(payload.password, payload.email, payload.phone_number)
    return user_out(user)


def update_profile(db: Session, user: User, payload: ProfileUpdate):
    if db.scalar(select(User.id).where(User.email == payload.email, User.id != user.id)):
        raise AppError(409, 'DUPLICATE_USER', '이미 사용 중인 이메일입니다.', {'email': '이미 사용 중입니다.'})
    if not db.get(Department, payload.department_id):
        raise AppError(422, 'INVALID_DEPARTMENT', '부서를 선택해주세요.', {'department_id': '존재하지 않는 부서입니다.'})
    for key, value in payload.model_dump().items():
        setattr(user, key, value)
    db.flush()
    return user_out(user)


def login(db, payload: Login):
    user = db.scalar(select(User).where(User.username == payload.username))
    # Verify a valid-cost hash even for an unknown username.
    hashed = user.password_hash if user else '$2b$12$A4EiCOEgCZwjBmSjscnnEOkhikpiFTLNtLNHEbRUZIbdHiBQTLQp.'
    if not verify_password(payload.password, hashed) or not user:
        raise AppError(401, 'INVALID_CREDENTIALS', '아이디 또는 비밀번호가 올바르지 않습니다.')
    return {'access_token': token_for(user.id), 'token_type': 'bearer'}


def create_request(db, user, payload: RequestInput):
    lic = repo.get(db, License, payload.license_id, lock=True)
    if lic.status != 'ACTIVE':
        raise AppError(400, 'LICENSE_INACTIVE', '현재 신청할 수 없는 라이선스입니다.')
    if repo.has(db, LicenseAssignment, user.id, lic.id, 'ACTIVE'):
        raise AppError(409, 'ALREADY_ASSIGNED', '이미 사용 중인 라이선스입니다.')
    if repo.has(db, LicenseRequest, user.id, lic.id, 'PENDING'):
        raise AppError(409, 'DUPLICATE_REQUEST', '승인 대기 중인 신청이 있습니다.')
    row = LicenseRequest(**payload.model_dump(), user_id=user.id, status='PENDING')
    db.add(row)
    db.flush()
    return request_out(db, row)


def pending(row):
    if row.status != 'PENDING':
        raise AppError(400, 'INVALID_TRANSITION', '이미 처리된 신청입니다.')


def cancel(db, user, key):
    row = repo.get(db, LicenseRequest, key, lock=True)
    if row.user_id != user.id:
        raise AppError(403, 'NOT_OWNER', '본인의 신청만 취소할 수 있습니다.')
    pending(row)
    row.status, row.canceled_at = 'CANCELED', utcnow()
    db.flush()
    return request_out(db, row)


def decision(db, user, key, reason, approve):
    initial = repo.get(db, LicenseRequest, key)
    lic = repo.get(db, License, initial.license_id, lock=True)
    row = repo.get(db, LicenseRequest, key, lock=True)
    pending(row)
    if approve:
        if lic.status != 'ACTIVE':
            raise AppError(400, 'LICENSE_INACTIVE', '비활성 라이선스는 승인할 수 없습니다.')
        if repo.has(db, LicenseAssignment, row.user_id, lic.id, 'ACTIVE'):
            raise AppError(409, 'ALREADY_ASSIGNED', '이미 사용 중인 사용자입니다.')
        if repo.used(db, lic.id) >= lic.total_seats:
            raise AppError(409, 'LICENSE_SEAT_FULL', '사용 가능한 라이선스 좌석이 없습니다.')
        db.add(LicenseAssignment(user_id=row.user_id, license_id=lic.id, request_id=row.id,
                                 status='ACTIVE', assigned_by=user.id,
                                 valid_from=row.start_date, valid_until=row.end_date))
    row.status = 'APPROVED' if approve else 'REJECTED'
    row.decision_reason, row.processed_by, row.processed_at = reason, user.id, utcnow()
    db.flush()
    return request_out(db, row)


def end_assignment(db, user, key, revoke=False, reason='사용자 직접 반납'):
    initial = repo.get(db, LicenseAssignment, key)
    repo.get(db, License, initial.license_id, lock=True)
    row = repo.get(db, LicenseAssignment, key, lock=True)
    if not revoke and row.user_id != user.id:
        raise AppError(403, 'NOT_OWNER', '본인의 라이선스만 반납할 수 있습니다.')
    if row.status != 'ACTIVE':
        raise AppError(400, 'INVALID_TRANSITION', '이미 종료된 할당입니다.')
    row.status = 'REVOKED' if revoke else 'RETURNED'
    row.ended_by, row.ended_at, row.end_reason = user.id, utcnow(), reason
    db.flush()
    return assignment_out(db, row)


def update_assignment_period(db, key: int, payload: AssignmentPeriod):
    initial = repo.get(db, LicenseAssignment, key)
    repo.get(db, License, initial.license_id, lock=True)
    row = repo.get(db, LicenseAssignment, key, lock=True)
    if row.status != 'ACTIVE':
        raise AppError(400, 'INVALID_TRANSITION', '활성 상태의 권한 승인 기간만 수정할 수 있습니다.')
    row.valid_from = payload.valid_from
    row.valid_until = payload.valid_until
    db.flush()
    return assignment_out(db, row)


def save_license(db, payload: LicenseInput | LicensePatch, key=None):
    if key:
        row = repo.get(db, License, key, lock=True)
        values = payload.model_dump(exclude_unset=True)
        if values.get('total_seats', row.total_seats) < repo.used(db, key):
            raise AppError(409, 'SEATS_BELOW_USAGE', '현재 사용 중인 좌석 수보다 작게 설정할 수 없습니다.')
        for k, v in values.items():
            setattr(row, k, v)
    else:
        row = License(**payload.model_dump())
        db.add(row)
    db.flush()
    return license_out(db, row)


def dashboard(db):
    licenses = [license_out(db, lic) for lic in repo.licenses(db)]
    pending_rows = repo.rows(db, LicenseRequest, LicenseRequest.status == 'PENDING')
    return {'total_seats': sum(x['total_seats'] for x in licenses),
        'used_seats': sum(x['used_seats'] for x in licenses),
        'available_seats': sum(x['available_seats'] for x in licenses),
        'pending_requests': len(pending_rows), 'licenses': licenses,
        'high_utilization': sorted([x for x in licenses if x['utilization'] >= 90], key=lambda x: -x['utilization']),
        'recent_requests': [request_out(db, r) for r in pending_rows[:5]]}
