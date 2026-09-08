import os
os.environ.setdefault('JWT_SECRET', 'test-secret-that-is-at-least-32-characters')
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import get_db
from app.models.entities import Base, Department, User, License
from app.core.security import hash_password, token_for

@pytest.fixture()
def context():
    url = os.environ.get('TEST_DATABASE_URL', 'sqlite://')
    if url != 'sqlite://' and not url.rsplit('/', 1)[-1].endswith('_test'):
        raise RuntimeError('TEST_DATABASE_URL must end with _test; tests recreate tables.')
    engine = create_engine(url, **({'connect_args': {'check_same_thread': False}, 'poolclass': StaticPool} if url == 'sqlite://' else {}))
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory.begin() as db:
        dep = Department(name='개발팀')
        db.add(dep)
        db.flush()
        hashed = hash_password('Password123!')
        for i, role in enumerate(['MASTER', 'USER', 'USER']):
            db.add(User(employee_no=f'E{i}', name=f'사용자{i}', department_id=dep.id, job_title='팀원',
                email=f'user{i}@example.com', username=f'user{i}', password_hash=hashed, role=role))
        db.add(License(name='Test SaaS', vendor='Vendor', plan_name='Business', category='개발',
            description='개발 협업 도구', total_seats=1, unit_price=19, billing_cycle='MONTHLY', status='ACTIVE'))
    def override():
        with factory() as db:
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise
    app.dependency_overrides[get_db] = override
    with TestClient(app) as client:
        yield client, factory, engine
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()

def auth(key=2):
    return {'Authorization': f'Bearer {token_for(key)}'}

def apply(client, user=2):
    return client.post('/api/license-requests', headers=auth(user), json={
        'license_id': 1, 'reason': '프로젝트 개발', 'start_date': '2026-09-08', 'end_date': '2026-12-31'})
