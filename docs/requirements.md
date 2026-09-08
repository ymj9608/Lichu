references/license_hub_prototype_v2.html은 초기 UX 프로토타입이다. 기능과 사용자 흐름은 참고하되, 코드 구조나 시각 디자인을 그대로 복사할 필요는 없다. requirements가 prototype과 충돌하면 이 프롬프트의 requirements를 우선한다.

너는 이 프로젝트의 Principal Full-stack Engineer이자 Product Designer다.

내 목표는 교육용 장난감 수준의 CRUD 앱이 아니라,
3일짜리 AI 웹서비스 Mini-project 평가 기준을 충족하면서
실제 기업 내부에서 사용할 법한 완성도 높은 B2B 웹서비스 프로토타입을 만드는 것이다.

프로젝트를 임의로 확장하거나 요구사항을 생략하지 말고,
아래 명세를 Source of Truth로 사용하라.

==================================================
0. 프로젝트 기본 정보
==================================================

서비스명: Lichu

이름 의미:
LIcense + CHoose + yoU

서비스 유형:
B2B 사내 SaaS 라이선스 신청·승인·할당·회수 관리 시스템

핵심 문제:

기업에서는 GitHub Copilot, Figma, IntelliJ, Adobe CC 등
사용자 수(Seat)가 제한된 여러 SaaS 라이선스를 운영한다.

그러나 실제 조직에서는 다음 문제가 발생할 수 있다.

1. 직원이 어떤 SaaS 라이선스를 사용할 수 있는지 한눈에 알기 어렵다.
2. 현재 잔여 라이선스 수를 알기 어렵다.
3. 라이선스 신청이 Slack, 메일, 구두 요청 등으로 분산될 수 있다.
4. 관리자는 승인 대기 요청과 현재 사용자를 별도로 관리해야 한다.
5. 프로젝트 종료/업무 변경 후 불필요한 라이선스가 계속 점유될 수 있다.
6. 승인/반려/회수 사유와 처리 이력이 남지 않을 수 있다.

Lichu는 이를 다음 workflow로 통합한다.

직원:
라이선스 탐색
→ 사용 신청
→ 승인/반려 결과 확인
→ 라이선스 사용
→ 직접 반납

관리자:
신청 확인
→ 승인 또는 반려
→ 사용자 할당 관리
→ 필요 시 관리자 강제 회수
→ 처리 이력 확인

중요:
이번 프로젝트에서는 GitHub/Figma/Adobe 등 외부 SaaS Provider API를
직접 호출하여 실제 계정을 provisioning하는 기능은 구현하지 않는다.

Lichu에서의 "할당"은
사내 관리 시스템상 해당 사용자에게 라이선스 사용 권한을 배정한 상태를 의미한다.

향후 확장 기능으로 Vendor API 자동 provisioning을 제시할 수 있지만
현재 MVP에는 절대 포함하지 않는다.

==================================================
1. 과제 특성 및 최우선 설계 원칙
==================================================

이 프로젝트는 Front-End 중심 서비스 기획 프로젝트다.

중요 우선순위:

1. 서비스가 실제로 어떤 문제를 해결하는지 명확해야 한다.
2. Actor별 기능이 명확해야 한다.
3. 모든 기능이 UI에 표현되어야 한다.
4. UI에 표시되는 데이터는 DB 모델에 존재해야 한다.
5. UI에서 수행하는 행동에는 대응하는 API가 존재해야 한다.
6. API Request/Response는 DB 모델과 모순되면 안 된다.
7. 상태 변화와 예외 상황을 명확히 처리한다.
8. 불필요한 엔터프라이즈 기능을 추가하지 않는다.
9. 기능 수보다 전체 설계의 일관성을 우선한다.
10. 실제 회사에서 사용할 법한 UX를 만든다.

항상 다음 연결을 검증하라.

Requirement
→ Actor
→ Screen
→ UI Component
→ API
→ Entity / Field

하나라도 끊어지면 구현 전에 수정하라.

==================================================
2. 기술 스택
==================================================

Monorepo 구조로 구현하라.

Frontend:
- Vue 3
- Vite
- TypeScript
- Vue Router
- Pinia
- Axios
- Composition API
- Tailwind CSS
- lucide-vue-next

Backend:
- Python
- FastAPI
- SQLAlchemy 2.x
- Pydantic
- Alembic
- PostgreSQL

Authentication:
- JWT Access Token
- 비밀번호 bcrypt hashing
- Refresh Token은 구현하지 않는다.

Development:
- Docker Compose로 PostgreSQL 실행
- frontend/backend는 로컬 실행 가능하게 구성
- .env.example 제공

Testing:
- Backend: pytest
- Frontend: Vitest는 핵심 로직 위주
- 가능하다면 Playwright smoke test 추가

불필요한 기술:
- Redis
- Kafka
- WebSocket
- Celery
- Kubernetes
- MSA
- 외부 AI
- Vendor SaaS API
- 복잡한 RBAC

위 기술은 사용하지 않는다.

==================================================
3. 사용자 유형
==================================================

역할은 정확히 두 종류만 사용한다.

USER
- 일반 임직원

MASTER
- 라이선스 관리자

회원가입으로 MASTER 권한을 생성할 수 없어야 한다.

MASTER는 seed 데이터 또는 환경 변수 기반으로만 생성한다.

일반 직원은 회원가입 가능하다.

==================================================
4. 회원가입
==================================================

회원가입 화면에서는 실제 사내 업무 시스템처럼 다음 정보를 받는다.

필수:
- 사번 employee_no
- 이름 name
- 부서 department
- 직급/직책 job_title
- 회사 이메일 email
- 로그인 아이디 username
- 비밀번호 password
- 비밀번호 확인

Validation:

employee_no:
- unique
- 빈 문자열 불가

username:
- unique
- 4자 이상

email:
- valid email
- unique

password:
- 최소 8자
- password_confirm 일치

role:
- Client가 전달하지 않는다.
- Backend에서 무조건 USER로 생성한다.

회원가입 성공 후 로그인 화면으로 이동한다.

회원가입 실패 시 필드별 오류 메시지를 표시한다.

실제 기업에서는 SSO/HR 연동을 사용하는 것이 더 현실적일 수 있지만,
이번 프로젝트에서는 별도 외부 시스템 없이 self signup 방식으로 제한한다.
이 내용은 "향후 고려사항" 문서에 기록한다.

==================================================
5. 로그인
==================================================

로그인 입력:

- username
- password

성공:
JWT 발급

로그인 후:

USER:
라이선스 탐색 화면으로 이동

MASTER:
관리자 Dashboard로 이동

Sidebar/Header에는 다음 사용자 정보를 표시한다.

- 이름
- 부서
- 직급/직책

로그아웃 가능.

Route Guard를 구현한다.

MASTER 전용 화면에 USER 접근:
403 또는 Frontend redirect

==================================================
6. 라이선스 데이터
==================================================

각 SaaS 라이선스는 최소 다음 정보를 가진다.

License

- id
- name
- vendor
- plan_name
- category
- description
- total_seats
- unit_price
- billing_cycle
- status
- created_at
- updated_at

예시 Seed:

GitHub Copilot
- vendor: GitHub
- category: 개발
- total_seats: 50

Figma Professional
- vendor: Figma
- category: 디자인
- total_seats: 30

IntelliJ IDEA Ultimate
- vendor: JetBrains
- category: 개발
- total_seats: 20

Adobe Creative Cloud
- vendor: Adobe
- category: 디자인
- total_seats: 20

Notion Business
- vendor: Notion
- category: 생산성
- total_seats: 40

Slack Pro
- vendor: Slack
- category: 생산성
- total_seats: 80

중요:

used_seats 값을 별도 컬럼으로 저장하지 않는다.

사용 중 좌석 수는 다음으로 계산한다.

COUNT(
 LicenseAssignment
 WHERE license_id = X
 AND status = ACTIVE
)

available_seats =
total_seats - active_assignment_count

DB 값이 이중 관리되지 않도록 한다.

==================================================
7. USER - 라이선스 탐색
==================================================

URL:
 /licenses

화면:

- 제목
- 간략 설명
- 검색 Input
- Category Filter
- License Card Grid

각 카드:

- SaaS 이름
- Vendor
- Plan
- Category
- 가격
- 총 Seat
- 사용 Seat
- 잔여 Seat
- 사용률 Progress Bar
- 상태 Badge
- 사용 신청 버튼

예:

GitHub Copilot

47 / 50 사용 중
3 Seats Available

[██████████████████░░]

[사용 신청]

잔여 Seat가 0이어도 신청 자체는 가능하게 할 것인지 판단하라.

현재 MVP 정책:

신청은 가능하다.
다만 관리자는 잔여 Seat가 없는 경우 승인할 수 없다.

이를 UI에 명확히 표현한다.

==================================================
8. 라이선스 사용 신청
==================================================

사용 신청 Modal 또는 페이지:

- SaaS 정보
- 사용 목적 reason
- 사용 시작 예정일 start_date
- 사용 종료 예정일 end_date

Validation:

reason:
필수

start_date <= end_date

다음 경우 신청 불가:

1. 해당 사용자에게 동일 License ACTIVE Assignment가 존재
2. 해당 사용자에게 동일 License PENDING Request가 존재
3. License 상태가 INACTIVE

중복 신청은 Backend에서도 반드시 검증한다.

HTTP:
409 Conflict

신청 완료:

status = PENDING

==================================================
9. LicenseRequest 상태
==================================================

정확히 다음 상태만 사용한다.

PENDING
APPROVED
REJECTED
CANCELED

State Transition:

PENDING
→ APPROVED

PENDING
→ REJECTED

PENDING
→ CANCELED

그 외 상태 전이는 허용하지 않는다.

==================================================
10. USER - 내 신청
==================================================

URL:
 /requests

목록에 표시:

- SaaS
- 신청일
- 사용 예정 기간
- 사용 목적
- 상태
- 처리 결과
- 승인/반려 사유

PENDING:
[신청 취소] 버튼

APPROVED:
초록색 Badge
승인 사유 표시

REJECTED:
빨간색 Badge
반려 사유를 눈에 띄게 표시

예:

반려

반려 사유
"현재 Copilot 좌석이 모두 사용 중입니다.
기존 라이선스 회수 후 다시 신청해주세요."

사용자가 왜 반려됐는지 반드시 확인 가능해야 한다.

CANCELED:
취소 상태만 표시

==================================================
11. USER - 내 라이선스
==================================================

URL:
 /my-licenses

ACTIVE LicenseAssignment만 기본 표시.

Card:

- SaaS
- Vendor
- 할당일
- 상태
- 사용 종료 예정일이 있으면 표시
- 직접 반납 버튼

반납 시:

ACTIVE
→ RETURNED

반납 전에 Confirmation Modal 제공.

반납 후 즉시 잔여 Seat +1 효과가 UI에 반영되어야 한다.

==================================================
12. MASTER Dashboard
==================================================

URL:
 /admin

Summary Card:

- 전체 Seat
- 사용 중 Seat
- 잔여 Seat
- 승인 대기 Request 수

추가:

- SaaS별 사용률
- 사용률 높은 라이선스
- 최근 승인 대기 Request

과도한 Chart Library는 사용하지 말고
Card / Progress Bar 중심으로 구현한다.

==================================================
13. MASTER - 신청 관리
==================================================

URL:
 /admin/requests

두 Tab:

[승인 대기]
[처리 이력]

-----------------------------------
승인 대기
-----------------------------------

오직 status=PENDING Request만 표시한다.

Column:

- 신청자 이름
- 사번
- 부서
- SaaS
- 사용 목적
- 신청일
- 사용 기간
- 현재 잔여 Seat
- 승인
- 반려

승인 Button 클릭:

Approval Modal 표시

필수 입력:

승인 사유

예:
"Backend AI 프로젝트 개발 기간 동안 사용 승인"

승인 확인 시:

1. Request가 아직 PENDING인지 검증
2. 해당 사용자에게 ACTIVE Assignment가 없는지 검증
3. 잔여 Seat > 0인지 검증
4. 동일 DB Transaction 내에서:
   - LicenseRequest.status = APPROVED
   - decision_reason 저장
   - processed_by 저장
   - processed_at 저장
   - LicenseAssignment 생성

승인 완료 후:

해당 Request는 즉시 "승인 대기 목록"에서 사라져야 한다.

처리 이력에서는 보여야 한다.

-----------------------------------
반려
-----------------------------------

Reject Modal 표시

반려 사유는 필수다.

반려 완료:

status = REJECTED

decision_reason
processed_by
processed_at 저장

완료 후 승인 대기 목록에서 제거.

사용자의 "내 신청"에서는 반려 사유 확인 가능.

-----------------------------------
처리 이력
-----------------------------------

APPROVED / REJECTED 요청 표시

- 신청자
- SaaS
- 처리 결과
- 처리자
- 처리 사유
- 처리 일시

Filter:
- 승인
- 반려
- 전체

==================================================
14. MASTER - 라이선스 관리
==================================================

URL:
 /admin/licenses

License Card 또는 Table 제공.

각 라이선스:

- 이름
- Vendor
- Plan
- Category
- 총 Seat
- 사용 중 Seat
- 잔여 Seat
- 사용률
- 월 단가
- 상태

각 License Card를 클릭할 수 있어야 한다.

클릭 시 Drawer 또는 Modal:

"현재 라이선스 사용자 목록"

표시:

- 이름
- 사번
- 부서
- 직급
- 이메일
- 할당일
- 사용 목적
- 권한 회수 버튼

==================================================
15. MASTER - 관리자 권한 회수
==================================================

관리자는 ACTIVE Assignment를 직접 회수할 수 있다.

[권한 회수] 클릭

Confirmation Modal:

- 사용자
- SaaS
- 할당일
- 회수 사유 입력

회수 사유 필수.

처리:

ACTIVE
→ REVOKED

저장:

- ended_at
- ended_by
- end_reason

회수 후:

- 사용자 목록에서 제거
- Seat 사용 수 감소
- 잔여 Seat 증가
- 사용자의 My License에서 사라짐

과거 Assignment Row 자체는 삭제하지 않는다.

Audit 목적상 유지한다.

==================================================
16. MASTER - 라이선스 등록/수정
==================================================

관리자가 최소한 다음을 관리할 수 있게 한다.

Create License
Edit License

입력:

- name
- vendor
- plan_name
- category
- description
- total_seats
- unit_price
- billing_cycle
- status

License 삭제는 구현하지 않는다.

과거 Request/Assignment 데이터 보존을 위해
삭제 대신:

ACTIVE
INACTIVE

상태를 사용한다.

total_seats를 줄일 경우:

현재 ACTIVE Assignment 수보다 작은 값으로는 변경 불가.

예:

active_assignments = 18

total_seats를 15로 수정
→ 409 Conflict

==================================================
17. Entity 설계
==================================================

최소 다음 Entity를 사용한다.

Department

- id
- name

User

- id
- employee_no
- name
- department_id
- job_title
- email
- username
- password_hash
- role
- created_at
- updated_at

License

- id
- name
- vendor
- plan_name
- category
- description
- total_seats
- unit_price
- billing_cycle
- status
- created_at
- updated_at

LicenseRequest

- id
- user_id
- license_id
- reason
- start_date
- end_date
- status
- decision_reason nullable
- processed_by nullable
- processed_at nullable
- canceled_at nullable
- created_at

LicenseAssignment

- id
- user_id
- license_id
- request_id nullable
- status
- assigned_by
- assigned_at
- ended_by nullable
- ended_at nullable
- end_reason nullable

Request를 삭제하지 않는다.

Assignment를 삭제하지 않는다.

상태 변경으로 History를 보존한다.

==================================================
18. Assignment 상태
==================================================

ACTIVE
RETURNED
REVOKED

ACTIVE
→ RETURNED

ACTIVE
→ REVOKED

다른 Transition 금지.

RETURNED와 REVOKED의 차이:

RETURNED:
사용자가 직접 반납

REVOKED:
관리자가 권한 회수

==================================================
19. API
==================================================

REST API Prefix:

/api

Auth:

POST /api/auth/signup
POST /api/auth/login
GET /api/auth/me

Licenses:

GET /api/licenses
GET /api/licenses/{license_id}

Requests:

POST /api/license-requests
GET /api/license-requests/me
POST /api/license-requests/{request_id}/cancel

Assignments:

GET /api/license-assignments/me
POST /api/license-assignments/{assignment_id}/return

Admin:

GET /api/admin/dashboard

GET /api/admin/license-requests
GET /api/admin/license-requests/history

POST /api/admin/license-requests/{request_id}/approve
Request:
{
  "reason": "..."
}

POST /api/admin/license-requests/{request_id}/reject
Request:
{
  "reason": "..."
}

GET /api/admin/licenses
POST /api/admin/licenses
PATCH /api/admin/licenses/{license_id}

GET /api/admin/licenses/{license_id}/assignments

POST /api/admin/license-assignments/{assignment_id}/revoke

Request:
{
  "reason": "..."
}

각 API에:

- Request Schema
- Response Schema
- Error Response
- HTTP status
- Example

를 정의한다.

==================================================
20. Error Policy
==================================================

최소 다음 HTTP status를 명확히 사용한다.

400
잘못된 상태 전이 또는 비즈니스 규칙 위반

401
로그인 필요

403
권한 없음

404
Resource 없음

409
중복 신청
이미 사용 중
잔여 Seat 없음
현재 사용 수보다 total_seats를 작게 수정

422
입력 Validation 실패

Error Response format을 통일한다.

예:

{
  "code": "LICENSE_SEAT_FULL",
  "message": "사용 가능한 라이선스 좌석이 없습니다."
}

==================================================
21. UX 원칙
==================================================

서비스는 귀엽지만 실제 회사에서 사용할 수 있는 B2B 디자인이어야 한다.

브랜드:

Lichu

Meaning:
LIcense + CHoose + yoU

UI 톤:

- Professional SaaS
- Clean
- Friendly
- Dashboard 중심
- 지나치게 캐릭터 중심으로 만들지 않는다.

Lichu 마스코트는:

- 로그인
- 회원가입
- Empty State
- 성공 안내
- 작은 Branding 요소

정도로 제한한다.

업무 화면 자체는 Data readability를 우선한다.

브랜드 Color는
Lichu 마스코트와 어울리는 Yellow/Amber를 Accent로 사용하되
텍스트 가독성을 위해 Charcoal / White / Neutral Gray를 기본으로 한다.

예:

Primary:
#F5B82E 계열

Dark:
#26221D

Background:
#F7F8FA

Success:
Green

Error:
Red

Warning:
Amber

중요:
기존 Pokémon 또는 Raichu 공식 이미지를 사용하거나 복제하지 않는다.

`frontend/public/lichu-mascot.png` 파일이 존재하면
그 파일만 Lichu의 공식 프로젝트 마스코트로 사용한다.

없다면 임시 Placeholder를 사용하고
인터넷에서 Pokémon 이미지를 가져오지 않는다.

==================================================
22. Responsive
==================================================

Desktop 우선.

최소:

1440px
1024px
768px

에서 UI가 무너지지 않게 한다.

모바일 앱 수준 최적화는 이번 범위에서 제외한다.

==================================================
23. Seed Data
==================================================

개발용 Seed를 만든다.

MASTER:

username:
master

password:
환경 변수 MASTER_PASSWORD

이름:
Lichu Master

부서:
IT 자산관리팀

일반 USER Demo:

myeongjin
seoyeon
jihoon
haeun
등 여러 사용자

각각 다른 부서로 생성.

여러 Assignment도 Seed하여
라이선스 사용률이 0%만 표시되지 않게 한다.

중요:

used_seats를 fake 숫자로 하드코딩하지 않는다.

실제 Seed Assignment Row를 생성하여 사용량이 계산되게 한다.

==================================================
24. Critical Business Rules
==================================================

Backend가 반드시 보장해야 한다.

1.
동일 User + License에
PENDING Request 중복 생성 금지

2.
동일 User + License에
ACTIVE Assignment가 있으면 신청 불가

3.
Seat가 0인 License 승인 불가

4.
처리 완료된 Request 재승인/재반려 금지

5.
사용자가 다른 사람의 Request 취소 금지

6.
사용자가 다른 사람의 Assignment 반납 금지

7.
USER가 Admin API 호출 금지

8.
INACTIVE License 신청 금지

9.
ACTIVE Assignment가 아닌 건 Return/Revoke 불가

10.
현재 ACTIVE Assignment보다 total_seats를 작게 변경 금지

11.
승인과 Assignment 생성은 하나의 Transaction으로 처리

==================================================
25. 화면 목록
==================================================

최소 화면:

Public

1. Login
2. Signup

USER

3. License Catalog
4. License Request Modal
5. My Requests
6. My Licenses

MASTER

7. Admin Dashboard
8. Request Management - Pending
9. Request Management - History
10. License Management
11. License Create/Edit Modal
12. License Active Users Drawer/Modal
13. Approval Modal
14. Rejection Modal
15. Revoke Modal

==================================================
26. Frontend 상태 표현
==================================================

Badge:

PENDING:
Blue/Gray

APPROVED:
Green

REJECTED:
Red

ACTIVE:
Green

RETURNED:
Gray

REVOKED:
Red/Gray

Seat:

Available > 0:
Green

Available = 0:
Warning / Red

사용률 90% 이상:
Warning 표시

==================================================
27. Loading / Empty / Error UI
==================================================

각 주요 화면에 반드시 고려:

Loading

Empty

API Error

예:

신청 목록 Empty:
"아직 신청한 라이선스가 없습니다."

관리자 Pending Empty:
"현재 승인 대기 중인 요청이 없습니다."

라이선스 User Empty:
"현재 할당된 사용자가 없습니다."

==================================================
28. 프로젝트 구조
==================================================

권장:

/
  frontend/
  backend/
  docs/
  docker-compose.yml
  README.md

Frontend:

src/
  api/
  assets/
  components/
  layouts/
  router/
  stores/
  views/
  types/
  utils/

Backend:

app/
  api/
  core/
  db/
  models/
  schemas/
  services/
  repositories/
  main.py

tests/

Migration은 Alembic 사용.

==================================================
29. Backend Layering
==================================================

과도한 패턴을 만들지 않는다.

Router:
HTTP Request/Response

Service:
Business Rule

Repository:
DB 접근

Model:
ORM

Schema:
Pydantic

으로 역할을 분리한다.

==================================================
30. Test Cases
==================================================

pytest로 최소 다음 테스트를 구현한다.

AUTH

- 정상 회원가입
- 중복 username
- 중복 employee_no
- 중복 email
- 정상 로그인
- 잘못된 password

REQUEST

- 정상 신청
- 동일 PENDING 중복 신청 409
- ACTIVE Assignment 사용자 신청 409
- 타 사용자 Request 취소 금지

ADMIN

- USER Admin API 접근 403
- 정상 승인
- 승인 시 Assignment 생성
- 승인 후 Pending 목록에서 제거
- 승인 사유 저장
- 정상 반려
- 반려 사유 저장
- 반려 후 사용자에게 사유 조회 가능
- 처리된 Request 재처리 금지
- Seat 0 승인 409

ASSIGNMENT

- 사용자 직접 반납
- 관리자 회수
- 회수 사유 저장
- 이미 종료된 Assignment 재회수 금지

LICENSE

- ACTIVE Assignment 수보다 total_seats를 작게 변경 시 409

==================================================
31. OpenAPI 산출물
==================================================

FastAPI 구현과 별도로
과제 제출용 YAML을 생성한다.

파일:

docs/{CLASS}_{NAME}_Lichu-API.yml

OpenAPI 3.x

포함:

- paths
- parameters
- requestBody
- responses
- schemas
- examples
- error responses

과제 요구사항에 따라
Security Schemes는 제출용 YAML에서 제외한다.

그러나 실제 Application의 인증 자체는 구현한다.

API YAML과 실제 Backend endpoint가 불일치하면 안 된다.

가능하면 FastAPI OpenAPI schema로부터
YAML을 Export하는 Script를 만든다.

==================================================
32. DBML 산출물
==================================================

파일:

docs/{CLASS}_{NAME}_Lichu-DB.dbml

실제 SQLAlchemy Model과 동일해야 한다.

포함:

- PK
- FK
- Data Type
- NOT NULL
- UNIQUE
- Relationship

반드시 다음 관계가 보이게 한다.

Department 1:N User

User 1:N LicenseRequest

License 1:N LicenseRequest

User 1:N LicenseAssignment

License 1:N LicenseAssignment

LicenseRequest 1:0..1 LicenseAssignment

==================================================
33. 프로젝트 기술서
==================================================

다음 파일을 먼저 작성한다.

docs/project-overview.md

내용:

1. 서비스명
2. 서비스 한 줄 소개
3. 배경
4. 문제 정의
5. 핵심 가치
6. Target User
7. Actor
8. Actor별 기능
9. 주요 User Flow
10. 화면 구성
11. UI Flow
12. 주요 Error Scenario
13. Data Model 설명
14. API 설계 원칙
15. 현재 한계
16. 향후 확장

특히 UI Flow는 반드시 포함한다.

Employee:

Login
→ License Catalog
→ Request
→ My Requests
→ Approval/Rejection Result
→ My License
→ Return

Admin:

Login
→ Dashboard
→ Pending Request
→ Approve/Reject
→ License Management
→ Active User
→ Revoke

Mermaid 또는 SVG Diagram으로 작성하라.

==================================================
34. PDF 제출 준비
==================================================

최종 제출용 기술서에는 UI 흐름도가 반드시 존재해야 한다.

따라서:

1. 핵심 화면 Screenshot을 자동 또는 수동으로 캡처할 수 있게 한다.
2. docs/screenshots/에 저장할 구조를 만든다.
3. print-friendly한 docs/project-overview.html을 생성한다.
4. project-overview.md의 내용을 기반으로 작성한다.
5. UI Flow Diagram과 핵심 화면 Screenshot을 포함한다.

가능하면 Playwright를 사용하여:

- Login
- License Catalog
- My Requests
- Admin Dashboard
- Admin Request
- Admin License Users

화면 Screenshot 생성 Script를 작성한다.

가능하면 Chromium PDF 출력 script도 만든다.

최종 파일명:

docs/{CLASS}_{NAME}_Lichu-개요.pdf

환경상 PDF 자동 생성이 불가능하면
HTML을 브라우저에서 Print → Save as PDF 할 수 있도록
완성된 Print CSS를 제공한다.

==================================================
35. 발표 준비
==================================================

docs/presentation-script.md 생성.

5분 발표 기준.

구성:

0:00 ~ 0:30
문제

0:30 ~ 1:00
서비스 소개

1:00 ~ 2:30
USER Flow

2:30 ~ 3:40
MASTER Flow

3:40 ~ 4:20
ERD/API 설계

4:20 ~ 5:00
한계 및 확장

발표 핵심 메시지:

"Lichu는 단순한 라이선스 목록 서비스가 아니라,
한정된 SaaS Seat의 신청부터 승인, 할당, 반납과 회수까지
하나의 Workflow로 관리하는 서비스입니다."

==================================================
36. 현재 프로젝트의 명확한 한계
==================================================

다음은 구현하지 않는다.

1. 실제 GitHub/Figma/Adobe License Provisioning
2. SaaS Vendor API
3. HR 시스템 연동
4. SSO
5. Slack 알림
6. Email 알림
7. 자동 사용량 측정
8. 자동 License 회수
9. 부서별 Budget
10. 다단계 결재
11. 대기열 자동 할당
12. 결제 기능

향후 확장 항목으로만 문서에 작성한다.

==================================================
37. 개발 순서
==================================================

무작정 코딩부터 시작하지 않는다.

Phase 1
현재 Repository 구조 확인

Phase 2
requirements.md 작성

Phase 3
Entity / State / Business Rule 확정

Phase 4
DB Model + Migration

Phase 5
Backend API

Phase 6
Backend Test

Phase 7
Frontend Layout / Routing / Auth

Phase 8
USER 기능

Phase 9
MASTER 기능

Phase 10
Error / Empty / Loading 상태

Phase 11
UI polish / Responsive

Phase 12
OpenAPI YAML / DBML 동기화

Phase 13
Screenshot / Overview Document

Phase 14
README / Presentation Script

각 Phase가 끝날 때:

1. 구현한 내용
2. 변경 파일
3. 테스트 결과
4. 남은 TODO
5. 발견된 설계 문제

를 간략히 출력하라.

==================================================
38. 작업 방식
==================================================

IMPORTANT:

- 한 번에 모든 코드를 무리하게 생성하지 않는다.
- 먼저 Repository를 조사한다.
- 이미 존재하는 파일을 확인하고 충돌하지 않게 한다.
- 기존 구현이 있다면 가능한 한 재사용한다.
- 요구사항과 다른 기존 코드는 이유를 설명하고 수정한다.
- 불필요한 Dependency 추가 금지.
- TypeScript에서 any 남발 금지.
- Backend business logic를 Router에 직접 작성하지 않는다.
- UI용 Fake Data를 Production 코드에 하드코딩하지 않는다.
- API가 존재하는 화면은 실제 API를 사용한다.
- Seat 수를 Frontend에서 임의 계산하지 않는다.
- Backend Response 값을 사용한다.
- README 없이 종료하지 않는다.
- TODO comment를 남긴 상태로 완료라고 하지 않는다.
- 오류를 숨기지 않는다.
- 실제 command를 실행하여 build/test 결과를 확인한다.
- 테스트가 실패하면 원인을 해결하고 다시 실행한다.

==================================================
39. 완료 조건 Definition of Done
==================================================

프로젝트 완료라고 판단하려면 다음을 모두 만족해야 한다.

[기능]

□ 회원가입 가능
□ USER 로그인 가능
□ MASTER 로그인 가능
□ License 목록 조회 가능
□ License 신청 가능
□ 중복 신청 방지
□ 사용자 신청 취소 가능
□ 관리자 Pending 목록 확인 가능
□ 승인 사유 입력 가능
□ 반려 사유 입력 가능
□ 승인 후 Pending 목록에서 제거
□ 반려 후 Pending 목록에서 제거
□ 처리 이력에서 결과 확인 가능
□ 사용자에게 승인/반려 사유 표시
□ 승인 시 Assignment 생성
□ 사용자 My License 표시
□ 사용자 직접 반납 가능
□ 관리자 License Card 클릭 가능
□ Active User 목록 조회 가능
□ 관리자 권한 회수 가능
□ 회수 사유 저장
□ Seat 수 실시간 반영
□ License 등록/수정 가능

[품질]

□ UI/API/DB Field 일치
□ Loading 상태
□ Empty 상태
□ Error 상태
□ 주요 API Test 통과
□ Frontend build 성공
□ Backend test 성공
□ Migration 동작
□ Seed 동작

[과제 산출물]

□ project-overview
□ UI Flow
□ OpenAPI YML
□ DBML
□ Screenshot
□ PDF 준비
□ 발표 스크립트
□ README

==================================================
40. 지금 수행할 작업
==================================================

지금은 바로 전체 구현을 시작하지 말고 다음 순서로 시작하라.

1. 현재 Repository를 전부 확인하라.
2. 기존 파일/구현/의존성을 요약하라.
3. 위 요구사항 대비 현재 구현 Gap을 분석하라.
4. 최종 Folder Structure를 제안하라.
5. Entity와 State Transition을 검증하라.
6. API 목록을 표로 정리하라.
7. UI Screen과 API 매핑을 정리하라.
8. 구현 순서를 TODO로 작성하라.

그 후 명백한 요구사항 충돌이 없다면
Phase 1부터 순차 구현을 시작하라.

단,
요구사항이 애매하여 데이터 모델 또는 핵심 workflow가 달라질 정도의
중대한 판단이 필요한 경우에만 나에게 질문하라.

사소한 UI/파일명 문제 때문에 작업을 중단하지 말고
합리적인 기본값을 사용하되 해당 가정을 기록하라.