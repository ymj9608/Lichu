from concurrent.futures import ThreadPoolExecutor
import pytest
from sqlalchemy import select, func
from app.models.entities import LicenseRequest, LicenseAssignment, User
from app.services.hub import decision
from app.core.errors import AppError
from conftest import auth, apply

def registration():
    return dict(employee_no='NEW001', name='새 직원', department_id=1, job_title='개발자',
        email='new@example.com', username='newuser', password='Password123!', password_confirm='Password123!',
        profile_image='data:image/png;base64,iVBORw0KGgo=')

def approve(c, key=1):
    return c.post(f'/api/admin/license-requests/{key}/approve', headers=auth(1), json={'reason':'개발 기간 사용 승인'})

def test_signup_login(context):
    c, _, _ = context
    r = c.post('/api/auth/signup', json=registration())
    assert r.status_code == 201
    assert r.json()['role'] == 'USER' and 'password_hash' not in r.json()
    assert r.json()['profile_image'].startswith('data:image/png;base64,')
    assert c.post('/api/auth/login', json={'username':'newuser','password':'Password123!'}).status_code == 200
    for username in ['newuser','unknown']:
        assert c.post('/api/auth/login', json={'username':username,'password':'wrong'}).status_code == 401

def test_profile_update(context):
    c, _, _ = context
    body = {'name':'수정 사용자','department_id':1,'job_title':'선임 개발자',
        'email':'updated@example.com','profile_image':'data:image/webp;base64,UklGRg=='}
    r = c.patch('/api/auth/me', headers=auth(), json=body)
    assert r.status_code == 200 and r.json()['name'] == '수정 사용자'
    assert r.json()['profile_image'].startswith('data:image/webp;base64,')
    assert c.get('/api/auth/me', headers=auth()).json()['email'] == 'updated@example.com'
    assert c.patch('/api/auth/me', headers=auth(), json=body | {'email':'user0@example.com'}).status_code == 409
    assert c.patch('/api/auth/me', headers=auth(), json=body | {'profile_image':'https://example.com/a.png'}).status_code == 422
    large_image = 'data:image/png;base64,' + ('A' * 710_000)
    r = c.patch('/api/auth/me', headers=auth(), json=body | {'profile_image':large_image})
    assert r.status_code == 200 and len(r.json()['profile_image']) > 700_000

@pytest.mark.parametrize('field,value',[('username','user1'),('employee_no','E1'),('email','user1@example.com')])
def test_duplicate_signup(context, field, value):
    r = context[0].post('/api/auth/signup',json=registration() | {field:value})
    assert r.status_code == 409 and field in r.json()['fields']

@pytest.mark.parametrize('change',[{'role':'MASTER'},{'password_confirm':'mismatch'},{'employee_no':' '},
    {'username':'abc'},{'password':'short'},{'email':'invalid'},{'department_id':999},
    {'password':'가'*30,'password_confirm':'가'*30}])
def test_signup_validation(context, change):
    assert context[0].post('/api/auth/signup',json=registration() | change).status_code == 422

def test_auth_admin_forbidden(context):
    c, _, _ = context
    assert c.get('/api/licenses').status_code == 401
    assert c.get('/api/licenses',headers={'Authorization':'Bearer bad'}).status_code == 401
    assert c.get('/api/admin/dashboard',headers=auth()).status_code == 403
    assert c.get('/api/licenses/999',headers=auth()).status_code == 404

def test_request_duplicate_cancel_ownership(context):
    c, _, _ = context
    assert apply(c).status_code == 201
    assert apply(c).status_code == 409
    assert c.post('/api/license-requests/1/cancel',headers=auth(3)).status_code == 403
    r = c.post('/api/license-requests/1/cancel',headers=auth())
    assert r.status_code == 200 and r.json()['status'] == 'CANCELED' and r.json()['canceled_at']
    assert c.post('/api/license-requests/1/cancel',headers=auth()).status_code == 400
    assert len(c.get('/api/license-requests/me',headers=auth()).json()) == 1
    assert apply(c).status_code == 201

def test_approve_atomic_history_seats(context):
    c, factory, _ = context
    apply(c)
    r = approve(c)
    assert r.status_code == 200, r.text
    assert r.json()['decision_reason'] == '개발 기간 사용 승인'
    assert r.json()['processed_by'] == 1 and r.json()['processed_at']
    assert c.get('/api/admin/license-requests',headers=auth(1)).json() == []
    assert len(c.get('/api/admin/license-requests/history?status=APPROVED',headers=auth(1)).json()) == 1
    assignments = c.get('/api/license-assignments/me',headers=auth()).json()
    assert len(assignments) == 1 and assignments[0]['request_id'] == 1
    assert assignments[0]['end_date'] == '2026-12-31'
    assert assignments[0]['valid_from'] == '2026-09-08' and assignments[0]['valid_until'] == '2026-12-31'
    assert c.patch('/api/admin/license-assignments/1',headers=auth(),json={
        'valid_from':'2026-09-10','valid_until':'2026-12-20'}).status_code == 403
    changed = c.patch('/api/admin/license-assignments/1',headers=auth(1),json={
        'valid_from':'2026-09-10','valid_until':'2026-12-20'})
    assert changed.status_code == 200 and changed.json()['valid_until'] == '2026-12-20'
    assert c.patch('/api/admin/license-assignments/1',headers=auth(1),json={
        'valid_from':'2027-01-01','valid_until':'2026-12-20'}).status_code == 422
    assert apply(c).status_code == 409
    assert approve(c).status_code == 400
    assert c.post('/api/admin/license-requests/1/reject',headers=auth(1),json={'reason':'반려'}).status_code == 400
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(LicenseAssignment)) == 1

def test_reject_visible(context):
    c, _, _ = context
    apply(c)
    r = c.post('/api/admin/license-requests/1/reject',headers=auth(1),json={'reason':'업무 범위 협의 필요'})
    assert r.status_code == 200 and r.json()['status'] == 'REJECTED'
    assert c.get('/api/license-requests/me',headers=auth()).json()[0]['decision_reason'] == '업무 범위 협의 필요'
    assert c.get('/api/admin/license-requests',headers=auth(1)).json() == []
    assert len(c.get('/api/admin/license-requests/history?status=REJECTED',headers=auth(1)).json()) == 1

def test_full_seat_request_allowed_approval_forbidden(context):
    c, factory, _ = context
    apply(c)
    approve(c)
    assert apply(c,3).status_code == 201
    r = approve(c,2)
    assert r.status_code == 409 and r.json()['code'] == 'LICENSE_SEAT_FULL'
    with factory() as db:
        assert db.get(LicenseRequest,2).status == 'PENDING'
        assert db.scalar(select(func.count()).select_from(LicenseAssignment)) == 1

@pytest.mark.parametrize('action',['return','revoke'])
def test_assignment_end(context, action):
    c, factory, _ = context
    apply(c)
    approve(c)
    assert c.post('/api/license-assignments/1/return',headers=auth(3)).status_code == 403
    path = '/api/license-assignments/1/return' if action == 'return' else '/api/admin/license-assignments/1/revoke'
    kwargs = {'headers':auth(2 if action == 'return' else 1)}
    if action == 'revoke':
        kwargs['json'] = {'reason':'프로젝트 종료'}
    r = c.post(path,**kwargs)
    assert r.status_code == 200
    assert r.json()['status'] == ('RETURNED' if action == 'return' else 'REVOKED')
    assert r.json()['ended_at'] and r.json()['ended_by']
    assert r.json()['end_reason'] == ('사용자 직접 반납' if action == 'return' else '프로젝트 종료')
    assert c.post(path,**kwargs).status_code == 400
    assert c.patch('/api/admin/license-assignments/1',headers=auth(1),json={
        'valid_from':'2026-09-08','valid_until':'2026-12-31'}).status_code == 400
    assert c.get('/api/license-assignments/me',headers=auth()).json() == []
    assert c.get('/api/licenses/1',headers=auth()).json()['available_seats'] == 1
    with factory() as db:
        assert db.get(LicenseAssignment,1) is not None

def test_edit_seats_inactive_validation(context):
    c, _, _ = context
    apply(c)
    assert c.post('/api/admin/license-requests/1/approve',headers=auth(1),json={'reason':' '}).status_code == 422
    approve(c)
    assert c.patch('/api/admin/licenses/1',headers=auth(1),json={'total_seats':0}).status_code == 409
    assert c.patch('/api/admin/licenses/1',headers=auth(1),json={'total_seats':1}).status_code == 200
    assert c.patch('/api/admin/licenses/1',headers=auth(1),json={'name':None}).status_code == 422
    assert c.patch('/api/admin/licenses/1',headers=auth(1),json={'status':'INACTIVE'}).status_code == 200
    assert apply(c,3).status_code == 400
    assert c.post('/api/license-assignments/1/return',headers=auth()).status_code == 200

def test_dates_create_license(context):
    c, _, _ = context
    assert c.post('/api/license-requests',headers=auth(),json={'license_id':1,'reason':'목적',
        'start_date':'2026-10-01','end_date':'2026-09-01'}).status_code == 422
    r = c.post('/api/admin/licenses',headers=auth(1),json=dict(name='새 도구',vendor='Vendor',plan_name='Pro',
        category='생산성',description='팀 업무',total_seats=0,unit_price='120',billing_cycle='YEARLY',status='ACTIVE'))
    assert r.status_code == 201 and r.json()['monthly_unit_price'] == '10.00'

def test_concurrent_last_seat(context):
    c, factory, engine = context
    if engine.dialect.name != 'postgresql':
        pytest.skip('Requires TEST_DATABASE_URL PostgreSQL.')
    apply(c,2)
    apply(c,3)
    def attempt(key):
        try:
            with factory.begin() as db:
                decision(db,db.get(User,1),key,'동시 승인 검증',True)
            return 200
        except AppError as exc:
            return exc.status
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt,[1,2])) == [200,409]
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(LicenseAssignment)) == 1
        assert db.scalar(select(func.count()).select_from(LicenseRequest).where(LicenseRequest.status == 'PENDING')) == 1
