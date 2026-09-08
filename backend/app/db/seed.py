"""Idempotent development-only seed. Passwords are required environment values."""
from datetime import date, timedelta
from sqlalchemy import select
from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.entities import Department, User, License, LicenseRequest, LicenseAssignment, utcnow


def seed():
    if len(settings.master_password) < 8 or len(settings.demo_password) < 8:
        raise RuntimeError('MASTER_PASSWORD and DEMO_PASSWORD must be at least 8 characters.')
    with SessionLocal.begin() as db:
        if db.scalar(select(User.id).where(User.username == 'master')):
            print('Seed already present; no existing data changed.')
            return
        departments = [Department(name=n) for n in ['IT 자산관리팀', '개발팀', '디자인팀', '기획팀', '마케팅팀', '경영지원팀']]
        db.add_all(departments)
        db.flush()
        master = User(employee_no='MST000001', name='LiChU. Master', department_id=departments[0].id,
            job_title='IT Asset Manager', email='master@lichu.example', username='master',
            password_hash=hash_password(settings.master_password), role='MASTER')
        db.add(master)
        demo_hash = hash_password(settings.demo_password)
        people = [('myeongjin', '윤명진', 1, 'Backend Developer'), ('seoyeon', '김서연', 2, 'Product Designer'),
                  ('jihoon', '박지훈', 3, 'Product Manager'), ('haeun', '이하은', 4, 'Brand Marketer')]
        surnames = ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', '한', '오', '서', '신', '권', '황', '안', '송', '전']
        given_names = ['민준', '서준', '도윤', '예준', '시우', '하준', '주원', '지호', '지후', '준서', '서연', '서윤', '지우', '하윤', '민서', '지민', '채원', '수아', '지아', '다은']
        people += [(f'employee{i:03}', f'{surnames[(i-1)//20]}{given_names[(i-1)%20]}', 1 + i % 5, '팀원') for i in range(1, 77)]
        users = [User(employee_no=f'EMP{i+1:06}', name=name, department_id=departments[dept].id,
            job_title=title, email=f'{username}@lichu.example', username=username, password_hash=demo_hash, role='USER')
            for i, (username, name, dept, title) in enumerate(people)]
        db.add_all(users)
        specs = [('GitHub Copilot', 'GitHub', 'Business', '개발', 50, 19, '코드 작성부터 리뷰까지, 개발의 다음 단계를 함께합니다.'),
                 ('Figma Professional', 'Figma', 'Professional', '디자인', 30, 15, '아이디어를 시각화하고 팀과 함께 제품을 설계하세요.'),
                 ('IntelliJ IDEA Ultimate', 'JetBrains', 'Ultimate', '개발', 20, 16, '더 깊이 있는 코드 분석과 효율적인 개발 환경.'),
                 ('Adobe Creative Cloud', 'Adobe', 'All Apps', '디자인', 20, 60, '브랜드의 가능성을 넓히는 크리에이티브 도구 모음.'),
                 ('Notion Business', 'Notion', 'Business', '생산성', 40, 15, '문서와 지식을 연결하는 팀의 하나 된 워크스페이스.'),
                 ('Slack Pro', 'Slack', 'Pro', '생산성', 80, 9, '프로젝트의 대화와 협업을 한곳에서 이어가세요.')]
        licenses = [License(name=n, vendor=v, plan_name=p, category=c, total_seats=s, unit_price=price,
                    description=desc, billing_cycle='MONTHLY', status='ACTIVE') for n,v,p,c,s,price,desc in specs]
        db.add_all(licenses)
        db.flush()
        counts = [47, 28, 20, 8, 31, 74]
        today = date.today()
        for j, (lic, count) in enumerate(zip(licenses, counts)):
            # Real users, requests and assignments; no aggregate baseline shortcuts.
            chosen = users if j in (0, 4) else users[1:] + users[:1]
            for i, user in enumerate(chosen[:count]):
                req = LicenseRequest(user_id=user.id, license_id=lic.id, reason='팀 프로젝트 협업 및 업무 생산성 향상',
                    start_date=today - timedelta(days=14), end_date=today + timedelta(days=90), status='APPROVED',
                    decision_reason='프로젝트 기간 동안 사용 승인', processed_by=master.id, processed_at=utcnow())
                db.add(req)
                db.flush()
                db.add(LicenseAssignment(user_id=user.id, license_id=lic.id, request_id=req.id, assigned_by=master.id,
                    valid_from=req.start_date, valid_until=req.end_date, status='ACTIVE'))
        for user, lic, purpose in [(users[0], licenses[1], '신규 서비스 UI 프로토타입 협업'),
                (users[-1], licenses[0], 'AI 기반 개발 프로젝트 코드 작성 지원'),
                (users[-2], licenses[3], '브랜드 리뉴얼 캠페인 디자인')]:
            db.add(LicenseRequest(user_id=user.id, license_id=lic.id, reason=purpose,
                start_date=today, end_date=today + timedelta(days=60), status='PENDING'))
        db.add(LicenseRequest(user_id=users[0].id, license_id=licenses[3].id, reason='캠페인 디자인 작업',
            start_date=today, end_date=today + timedelta(days=30), status='REJECTED',
            decision_reason='디자인팀과 작업 범위를 먼저 협의한 후 다시 신청해주세요.', processed_by=master.id, processed_at=utcnow()))
    print('Seed complete: 81 users, 6 licenses, 208 active assignment rows.')


if __name__ == '__main__':
    seed()
