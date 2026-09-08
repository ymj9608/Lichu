# LiChU. 요구사항정의서
작성자: 판교5 / P157 / 윤명진 · 작성일: 2026-09-08 · v1.2

실제 구현에 맞춘 제출용 요구사항 정의서. 원문 명세 docs/requirements.md는 변경하지 않는다.

## REQ-FUNC-001 직원 회원가입
사번·이름·부서·직급/직책·회사 이메일·아이디·비밀번호·확인을 입력하고 JPG/PNG/WEBP 프로필 사진을 선택 등록한다. 사진 미등록 시 기본 프로필을 사용한다. 사번/아이디/이메일은 중복 불가(409), 아이디 4자 이상, 비밀번호 8자 이상·UTF-8 72바이트 이하 및 확인 일치. 부서는 DB 목록에서 선택한다. USER로만 생성하며 성공 시 로그인 화면으로 이동한다.
수요자: USER | 우선순위: High | 참고 공수: 중 / 0.5MD
화면: SCR-SIGNUP-001 — 회원가입 /signup
API: GET /api/departments; POST /api/auth/signup
DB: departments.id/name; users.employee_no/name/department_id/job_title/email/username/password_hash/profile_image/role

## REQ-FUNC-002 로그인
아이디·비밀번호로 인증하고 JWT Access Token을 발급한다. 로그인 정보 저장은 비밀번호 대신 아이디만 브라우저에 보관한다. ID/비밀번호 찾기 버튼에서 사내 계정 문의 절차를 안내한다. USER는 라이선스 탐색, MASTER는 관리자 대시보드로 이동한다. 인증 실패는 401과 오류 메시지를 표시한다.
수요자: 공통 | 우선순위: High | 참고 공수: 중 / 0.25MD
화면: SCR-AUTH-001 — 로그인 /login
API: POST /api/auth/login; GET /api/auth/me
DB: users.username/password_hash/role; users.department_id → departments.id

## REQ-FUNC-003 사용자 정보·로그아웃
헤더에 이름·부서·직급/직책과 역할을 표시한다. 로그아웃하면 브라우저 토큰과 사용자 상태를 제거하고 로그인으로 이동한다. 토큰 만료 또는 401 발생 시 재로그인한다. 별도의 로그아웃 API나 Refresh Token은 사용하지 않는다.
수요자: 공통 | 우선순위: High | 참고 공수: 하 / 0.25MD
화면: SCR-COMMON-001 — 공통 헤더·사이드바 / 인증 후 전체
API: GET /api/auth/me
DB: users.name/job_title/role/department_id; departments.name (로그아웃은 DB 변경 없음)

## REQ-FUNC-020 회원 정보·프로필 사진 수정
헤더의 사용자 정보를 선택하면 이름·부서·직급/직책·회사 이메일과 프로필 사진을 수정한다. JPG/PNG/WEBP를 허용하며 별도의 파일 용량 제한은 두지 않는다. 사진을 등록하지 않거나 제거하면 공통 기본 프로필 이미지를 표시하고, 등록된 사진은 헤더·승인 대기·사용자 관리에 표시한다. 사번과 아이디는 읽기 전용이며 이메일 중복과 부서 유효성을 서버에서 검사한다.
수요자: 공통 | 우선순위: High | 참고 공수: 중 / 0.5MD
화면: SCR-COMMON-002 — 회원 정보 수정 모달 / 인증 후 전체
API: PATCH /api/auth/me; GET /api/departments
DB: users.name/department_id/job_title/email/profile_image/updated_at; departments.id

## REQ-FUNC-004 라이선스 탐색·검색
이름·공급사 검색과 카테고리 필터를 제공한다. 카드에 이름·공급사·플랜·분류·설명·단가/청구 주기·총/사용/잔여 좌석·사용률·활성 상태를 표시한다. 기존 ACTIVE 할당, PENDING 신청, INACTIVE 상태는 신청 버튼을 제한한다. 잔여 0석은 신청 가능으로 안내한다.
수요자: USER | 우선순위: High | 참고 공수: 중 / 0.5MD
화면: SCR-LIC-001 — 라이선스 탐색 /licenses
API: GET /api/licenses
DB: licenses 전체 정보; license_assignments.status=ACTIVE 집계; license_requests.status=PENDING

## REQ-FUNC-005 라이선스 사용 신청
모달에서 SaaS 상세를 확인하고 사용 목적·시작/종료 예정일을 입력한다. 목적은 필수이며 시작일≤종료일이어야 한다. 동일 라이선스의 ACTIVE 할당 또는 PENDING 신청은 409, INACTIVE는 400으로 차단한다. 잔여 0석에서도 PENDING 신청은 생성한다.
수요자: USER | 우선순위: High | 참고 공수: 상 / 0.5MD
화면: SCR-LIC-002 — 사용 신청 모달 /licenses 내부
API: GET /api/licenses/{license_id}; POST /api/license-requests
DB: license_requests.user_id/license_id/reason/start_date/end_date/status/created_at; licenses; license_assignments

## REQ-FUNC-006 내 신청·처리 결과
본인 신청의 SaaS·목적·신청일·예정 기간·상태와 승인/반려 사유·처리자·처리일을 확인한다. 반려 사유는 강조 표시한다. PENDING만 취소 버튼을 제공하고 CANCELED는 취소 상태를 표시한다. 화면에서 목록을 10건씩 표시한다.
수요자: USER | 우선순위: High | 참고 공수: 중 / 0.25MD
화면: SCR-REQ-001 — 내 신청 /requests
API: GET /api/license-requests/me
DB: license_requests 상태/기간/목적/decision_reason/processed_by/processed_at; users; licenses

## REQ-FUNC-007 본인 신청 취소
취소 확인 모달을 거쳐 본인의 PENDING 신청만 CANCELED로 변경하고 canceled_at을 저장한다. 타인의 신청은 403, 이미 처리된 신청은 400으로 거부한다. 신청 행은 삭제하지 않으며 취소 후 필요하면 새로 신청할 수 있다.
수요자: USER | 우선순위: High | 참고 공수: 하 / 0.25MD
화면: SCR-REQ-002 — 신청 취소 확인 /requests 내부
API: POST /api/license-requests/{request_id}/cancel
DB: license_requests.user_id/status/canceled_at

## REQ-FUNC-008 내 라이선스 조회
본인의 ACTIVE 할당만 표시한다. SaaS·공급사·플랜·상태·사용 목적과 권한 승인 시작일/종료일을 확인한다. 목적은 연결된 신청에서 읽으며 연결이 없는 직접 배정은 별도 안내한다.
수요자: USER | 우선순위: High | 참고 공수: 중 / 0.25MD
화면: SCR-MYLIC-001 — 내 라이선스 /my-licenses
API: GET /api/license-assignments/me
DB: license_assignments.user_id/status/valid_from/valid_until/request_id; licenses; license_requests.reason

## REQ-FUNC-009 사용자 직접 반납
확인 모달 후 본인의 ACTIVE 할당을 RETURNED로 변경한다. ended_by/ended_at과 “사용자 직접 반납” 사유를 저장한다. 타인 건은 403, 종료된 건은 400으로 차단한다. 완료 후 사용 목록을 재조회하고 잔여 좌석 집계에 반영한다.
수요자: USER | 우선순위: High | 참고 공수: 중 / 0.25MD
화면: SCR-MYLIC-002 — 반납 확인 /my-licenses 내부
API: POST /api/license-assignments/{assignment_id}/return
DB: license_assignments.status/ended_by/ended_at/end_reason; ACTIVE 집계 감소

## REQ-FUNC-010 관리자 대시보드
전체·사용 중·잔여 좌석과 승인 대기 수를 표시한다. 라이선스별 사용 현황과 승인 대기 목록은 하단이 맞는 동일 높이 패널에서 각각 스크롤한다. 비활성 라이선스도 전체 좌석 합계에 포함하며 실제 ACTIVE 할당으로 사용량을 계산한다.
수요자: MASTER | 우선순위: High | 참고 공수: 중 / 0.5MD
화면: SCR-ADM-001 — 대시보드 /admin
API: GET /api/admin/dashboard
DB: licenses.total_seats/status; license_assignments.status; license_requests.status/created_at; users

## REQ-FUNC-011 승인 대기 요청 조회
승인 대기 탭에 PENDING만 표시한다. 신청자 이름·부서, SaaS·사용 목적·신청일과 한 줄의 사용 예정 기간, 현재 잔여 좌석을 확인한다. 잔여 0석 또는 비활성이면 승인 버튼을 비활성화한다. 승인/반려 후 재조회하여 대기 목록에서 제거한다.
수요자: MASTER | 우선순위: High | 참고 공수: 중 / 0.25MD
화면: SCR-ADM-002 — 승인 대기 /admin/requests
API: GET /api/admin/license-requests
DB: license_requests.status=PENDING/start_date/end_date; users.name/department_id; licenses; ACTIVE 집계

## REQ-FUNC-012 사유 입력·승인 및 할당
승인 사유는 필수다. PENDING 여부, 라이선스 활성 여부, 기존 ACTIVE 할당 없음, 잔여 좌석>0을 서버에서 확인한다. 동일 트랜잭션에서 APPROVED·사유·처리자·시각을 저장하고, 신청 기간을 권한 승인 기간으로 복사한 ACTIVE 할당을 생성한다. 좌석 부족/기존 할당은 409, 재처리는 400이다.
수요자: MASTER | 우선순위: High | 참고 공수: 상 / 0.5MD
화면: SCR-ADM-007 — 승인 모달 /admin/requests 내부
API: POST /api/admin/license-requests/{request_id}/approve
DB: license_requests.status/decision_reason/processed_by/processed_at/start_date/end_date; license_assignments.user_id/license_id/request_id/status/assigned_by/assigned_at/valid_from/valid_until

## REQ-FUNC-013 사유 입력·반려
반려 사유를 필수 입력하고 PENDING 신청을 REJECTED로 변경한다. decision_reason/processed_by/processed_at을 저장한다. 완료 건은 대기에서 제거되어 처리 이력과 신청자의 내 신청에 나타난다. 할당은 생성하지 않으며 재처리는 400으로 거부한다.
수요자: MASTER | 우선순위: High | 참고 공수: 중 / 0.25MD
화면: SCR-ADM-008 — 반려 모달 /admin/requests 내부
API: POST /api/admin/license-requests/{request_id}/reject
DB: license_requests.status/decision_reason/processed_by/processed_at

## REQ-FUNC-014 승인·반려 이력 조회
처리 이력 탭에는 APPROVED/REJECTED만 표시하고 전체·승인·반려 필터를 제공한다. 신청자·SaaS·결과·처리자·사유·처리일을 표시한다. CANCELED는 관리자 처리 이력에 포함하지 않는다. 목록은 화면에서 10건씩 나누어 표시한다.
수요자: MASTER | 우선순위: High | 참고 공수: 중 / 0.25MD
화면: SCR-ADM-004 — 처리 이력 /admin/requests 탭
API: GET /api/admin/license-requests/history
DB: license_requests.status/decision_reason/processed_by/processed_at; users; licenses

## REQ-FUNC-015 라이선스 관리 목록
등록된 라이선스의 이름·공급사·플랜·분류·총/사용/잔여 좌석·사용률·단가·청구 주기·상태를 카드로 표시한다. 연간 단가는 월 환산액도 표시한다. 검색·분류 필터, 등록·수정 버튼과 카드 클릭을 통한 현재 사용자 관리를 제공한다.
수요자: MASTER | 우선순위: High | 참고 공수: 중 / 0.25MD
화면: SCR-ADM-003 — 라이선스 관리 /admin/licenses
API: GET /api/admin/licenses
DB: licenses 전체 필드; license_assignments.status=ACTIVE 집계

## REQ-FUNC-016 라이선스 등록
이름·공급사·플랜·분류·설명·총 좌석·사용자당 단가(USD)·청구 주기(MONTHLY/YEARLY)·상태(ACTIVE/INACTIVE)를 입력하여 등록한다. 총 좌석과 단가는 0 이상이어야 한다. 저장 후 관리 목록을 재조회한다.
수요자: MASTER | 우선순위: High | 참고 공수: 중 / 0.5MD
화면: SCR-ADM-005 — 등록 모달 /admin/licenses 내부
API: POST /api/admin/licenses
DB: licenses.name/vendor/plan_name/category/description/total_seats/unit_price/billing_cycle/status/created_at/updated_at

## REQ-FUNC-017 라이선스 수정·비활성화
기존 정보를 수정한다. 총 좌석을 현재 ACTIVE 할당 수 미만으로 줄이면 409로 거부한다. 삭제 대신 INACTIVE로 설정하며 기존 신청·할당 이력을 유지한다. 비활성 상태는 새 신청·승인을 막지만 기존 할당을 자동 종료하지 않는다.
수요자: MASTER | 우선순위: High | 참고 공수: 중 / 0.5MD
화면: SCR-ADM-005 — 수정 모달 /admin/licenses 내부
API: PATCH /api/admin/licenses/{license_id}
DB: licenses 수정 필드/updated_at; license_assignments.status=ACTIVE 집계

## REQ-FUNC-018 현재 라이선스 사용자 조회·검색
라이선스 카드를 클릭하면 해당 라이선스의 ACTIVE 사용자 목록을 모달로 연다. 이름·부서·직급/직책·이메일·권한 승인 기간과 수정·회수 버튼을 표시한다. 이름·부서·직급·이메일 통합 검색을 제공하고 사용자가 없거나 검색 결과가 없으면 각각 빈 상태를 안내한다.
수요자: MASTER | 우선순위: High | 참고 공수: 중 / 0.25MD
화면: SCR-ADM-006 — 라이선스 사용자 관리 모달 /admin/licenses 내부
API: GET /api/admin/licenses/{license_id}/assignments
DB: license_assignments.status/valid_from/valid_until/request_id; users.name/department_id/job_title/email/profile_image; departments.name

## REQ-FUNC-021 권한 승인 기간 수정
라이선스 사용자 관리에서 수정 버튼을 선택하여 ACTIVE 할당의 권한 승인 시작일과 종료일을 변경한다. 시작일≤종료일을 클라이언트와 서버에서 검증하고 종료된 할당은 400으로 거부한다. 완료 후 사용자 목록을 재조회하여 변경 기간을 표시한다.
수요자: MASTER | 우선순위: High | 참고 공수: 중 / 0.25MD
화면: SCR-ADM-010 — 권한 승인 기간 수정 모달 /admin/licenses 내부
API: PATCH /api/admin/license-assignments/{assignment_id}
DB: license_assignments.status/valid_from/valid_until

## REQ-FUNC-019 관리자 권한 회수
사용자·SaaS·권한 승인 기간을 확인하고 회수 사유를 필수 입력한다. ACTIVE만 REVOKED로 변경하고 ended_by/ended_at/end_reason을 저장한다. 종료된 건은 400이다. 완료 후 현재 사용자/내 라이선스에서 제외되고 잔여 좌석이 증가한다. 할당 행은 보존한다.
수요자: MASTER | 우선순위: High | 참고 공수: 중 / 0.5MD
화면: SCR-ADM-009 — 회수 모달 /admin/licenses 내부
API: POST /api/admin/license-assignments/{assignment_id}/revoke
DB: license_assignments.status/valid_from/valid_until/ended_by/ended_at/end_reason; ACTIVE 집계 감소

## 비기능 요구사항
### REQ-NFN-001 비밀번호 보호
bcrypt 단방향 해시로 저장하며 평문 및 password_hash를 사용자 API 응답에 포함하지 않는다.
중요도: High | 화면: SCR-SIGNUP-001 / SCR-AUTH-001

### REQ-NFN-002 인증·역할·소유권
JWT Access Token과 서버 권한 검증을 적용한다. USER의 관리자 API는 403, 타인 신청 취소·할당 반납도 403이다. 프런트엔드에도 역할별 Route Guard를 둔다.
중요도: High | 화면: SCR-COMMON-001 / 전체 보호 화면

### REQ-NFN-003 중복·초과 할당 방지
사용자+라이선스의 PENDING 신청/ACTIVE 할당을 부분 UNIQUE 인덱스로 제한한다. 좌석 변경 시 License 행 잠금, 승인+할당 생성의 단일 트랜잭션으로 동시 초과 승인을 방지한다.
중요도: High | 화면: SCR-LIC-002 / SCR-ADM-007

### REQ-NFN-004 좌석 단일 집계·이력 보존
used_seats 컬럼을 저장하지 않는다. 사용량은 ACTIVE Assignment COUNT, 잔여량은 총 좌석−사용량이다. 요청·할당 행을 삭제하지 않고 상태와 처리/종료 정보를 보존한다.
중요도: High | 화면: SCR-LIC-001 / SCR-ADM-001 / SCR-ADM-003

### REQ-NFN-005 Loading·Empty·Error
주요 화면에 로딩·빈 목록·API 오류 및 재시도를 제공한다. 승인/반려는 사유를 표시하고 반납/회수/취소는 확인 절차를 둔다. 오류는 code/message/fields 형식으로 처리한다.
중요도: High | 화면: 전체 주요 목록·모달

### REQ-NFN-006 데스크톱 반응형
1440/1024/768px에서 레이아웃이 유지되도록 구성한다. 좁은 폭의 테이블은 내부 가로 스크롤한다. Chromium 기반 화면 흐름과 넘침을 검증했으며 모바일 앱 최적화는 범위 밖이다.
중요도: Medium | 화면: 전체 화면

### REQ-NFN-007 변경 결과 반영
처리 완료 후 관련 목록을 서버에서 다시 조회한다. 다른 사용자의 변경은 창 복귀 또는 화면이 보이는 동안 30초 주기로 재조회한다. WebSocket 실시간 전파는 사용하지 않는다.
중요도: High | 화면: SCR-LIC-001 / SCR-REQ-001 / 관리자 목록

### REQ-NFN-008 구조·재현 가능성
Vue 3/Vite/TypeScript/Pinia/Axios/Tailwind와 FastAPI/SQLAlchemy/Pydantic/PostgreSQL을 사용한다. Router/Service/Repository를 분리하고 Compose·Alembic·seed·환경 예제·의존성 잠금 파일을 제공한다.
중요도: High | 화면: 전체 / 배포·개발 환경

### REQ-NFN-009 기능·계약 검증
업무 규칙과 동시 승인 pytest, 핵심 표시 로직 Vitest, 실제 API 기반 Playwright 및 frontend build를 검증한다. OpenAPI는 실제 API에서, DBML은 ORM에서 생성하여 명세와 구현을 맞춘다.
중요도: High | 화면: 전체 / API·DB 산출물
