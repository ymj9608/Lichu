from sqlalchemy import select
import pytest
from app.core.config import settings
from app.models.entities import User, CsiSignupProfile
from app.core.csi_signup import lab_version, hash_signup_password
from app.core.security import verify_password


def synthetic():
    return dict(employee_no='CSI-LAB-001', name='테스트 사용자', department_id=1,
                job_title='테스트 개발자', email='csi.test@example.com', username='csi_test',
                password='Demo-Only-2026!', password_confirm='Demo-Only-2026!',
                phone_number='010-0000-0000', profile_image=None)


def test_lab_signup_persists_logs_and_login(context, monkeypatch, caplog):
    monkeypatch.setattr(settings, 'csi_lab_mode', True)
    client, factory, _ = context
    data = synthetic()
    with caplog.at_level('INFO', logger='uvicorn.error'):
        result = client.post('/api/auth/signup', json=data)
    assert result.status_code == 201, result.text
    assert 'password_hash' not in result.json() and 'phone_number' not in result.json()
    with factory() as db:
        user = db.scalar(select(User).where(User.username == data['username']))
        assert db.get(CsiSignupProfile, user.id).phone_number == '010-0000-0000'
        assert lab_version() == 'after-fix'
        assert user.password_hash.startswith('$2b$12$')
        assert data['password'] not in caplog.text and data['email'] not in caplog.text
        assert data['phone_number'] not in caplog.text
        assert 'DB_COMMITTED' in caplog.text
    login = client.post('/api/auth/login', json={'username':data['username'], 'password':data['password']})
    assert login.status_code == 200
    token = login.json()['access_token']
    assert client.get('/api/licenses', headers={'Authorization':'Bearer '+token}).status_code == 200
    assert client.post('/api/auth/login', json={'username':data['username'], 'password':'wrong'}).status_code == 401
    assert client.post('/api/auth/signup', json=data).status_code == 409


def test_lab_blocks_non_synthetic_input(context, monkeypatch):
    monkeypatch.setattr(settings, 'csi_lab_mode', True)
    for change in ({'email':'user@real-company.com'}, {'name':'Real Person'},
                   {'password':'realpassword','password_confirm':'realpassword'},
                   {'phone_number':'010-1234-5678'}):
        assert context[0].post('/api/auth/signup', json=synthetic() | change).status_code == 422


def test_standard_mode_rejects_lab_field(context, monkeypatch):
    monkeypatch.setattr(settings, 'csi_lab_mode', False)
    assert context[0].post('/api/auth/signup', json=synthetic()).status_code == 422
    assert context[0].get('/api/csi-lab').json()['enabled'] is False


def test_signup_hashes_have_unique_salts_and_reject_legacy(monkeypatch):
    monkeypatch.setattr(settings, 'csi_lab_mode', True)
    password = synthetic()['password']
    first, second = hash_signup_password(password), hash_signup_password(password)
    assert first != second
    assert verify_password(password, first) and verify_password(password, second)
    assert not verify_password('wrong', first)
    import hashlib
    legacy = 'csi-sha256$' + hashlib.sha256((password + 'lichu-csi-shared-salt').encode()).hexdigest()
    assert not verify_password(password, legacy)


@pytest.mark.parametrize('provided', [False, True])
def test_lab_requires_phone_before_persistence_or_logging(context, monkeypatch, caplog, provided):
    monkeypatch.setattr(settings, 'csi_lab_mode', True)
    data = synthetic()
    if provided:
        data['phone_number'] = None
    else:
        data.pop('phone_number')
    client, factory, _ = context
    with caplog.at_level('INFO', logger='uvicorn.error'):
        response = client.post('/api/auth/signup', json=data)
    assert response.status_code == 422
    assert response.json()['code'] == 'LAB_PHONE_REQUIRED'
    assert data['password'] not in caplog.text and data['email'] not in caplog.text
    with factory() as db:
        assert db.scalar(select(User).where(User.username == data['username'])) is None
