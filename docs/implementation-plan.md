# 조사 · 설계 · 구현 순서

## 저장소 조사와 Gap
기존 파일은 reference/license_hub_prototype_v2.html, reference/lichu-mascot.png, frontend/public/lichu-mascot.png뿐이다. 패키지나 기존 앱은 없다. 외부 라이브러리 없는 HTML/JS 메모리 기반 데모는 가상 baselineUsed, 평문 암호, 취소 행 삭제, 브라우저 역할 판정을 사용한다. DB/API/실제 인증/회원가입 검증/등록·수정/테스트/제출 문서를 새로 구현해야 한다. reference 원본은 보존한다. 상위 홈 디렉터리가 Git 루트로 감지되어 Git 전역 작업은 하지 않는다.

## 최종 구조
```
Lichu/
  frontend/ src/{api,components,layouts,router,stores,views,types,utils}/
            public/lichu-mascot.png scripts/ tests/
  backend/ app/{api,core,db,models,schemas,services,repositories}/
           alembic/versions/ tests/ scripts/
  docs/ requirements.md project-overview.md project-overview.html
        implementation-plan.md CLASS_NAME_Lichu-API.yml CLASS_NAME_Lichu-DB.dbml
        screenshots/ presentation-script.md
  reference/ docker-compose.yml .env.example README.md
```

## 확정 가정
- 부서 선택은 공개 GET /api/departments로 DB에서 제공한다. 신규 부서 관리 UI는 범위 외다.
- start_date/end_date는 신청 필수값, 날짜 역전 금지. 과거 날짜 자체는 명세대로 금지하지 않는다.
- 단가는 USD, MONTHLY/YEARLY 두 청구 주기. 월 환산 단가는 서버가 계산한다. 데모 가격은 실제 판매가가 아니다.
- 비활성 전환은 기존 할당을 종료하지 않는다. 비활성 라이선스의 기존 대기도 승인할 수 없다(400). 반려·취소·반납·회수는 가능하다.
- 모든 라이선스(비활성 포함)를 대시보드 좌석 합계에 포함한다.
- JWT는 sessionStorage에 보관하고 만료/401 시 로그인으로 이동한다. 기간은 환경변수 설정.
- 제출자 정보가 없으므로 CLASS_NAME 기본값, export 환경변수 SUBMISSION_CLASS/SUBMISSION_NAME 지원.
- 수정은 PATCH(부분 갱신), 삭제 endpoint 없음. 새로고침 및 화면 진입 때 서버 재조회, 변경 후 즉시 재조회, 탭 복귀와 주기적 재조회로 다른 사용자의 변경을 반영한다.

## Entity / 상태 검증
Department(name unique); User(employee_no, username, email unique, department FK, role USER|MASTER); License(total_seats >= 0, unit_price >= 0, ACTIVE|INACTIVE); Request(reason, dates, audit); Assignment(request_id nullable unique, audit).

Request: PENDING → APPROVED / REJECTED / CANCELED만 허용.
Assignment: ACTIVE → RETURNED / REVOKED만 허용.
승인 이유/처리자/시각, 취소 시각, 반납·회수 종료자/시각/이유를 저장한다. used_seats 컬럼은 없다. License → Request/Assignment 잠금 순서를 일관되게 유지한다.

## API · 화면 · 필드 매핑
|Method|API (/api)|Actor / Screen|입력 → DB / 응답|성공|
|---|---|---|---|---|
|GET|/departments|Public / Signup|Department id/name 목록|200|
|POST|/auth/signup|Public / Signup|사번·이름·부서ID·직책·이메일·아이디·암호·확인 → User(USER)|201|
|POST|/auth/login|Public / Login|username/password → access_token|200|
|GET|/auth/me|로그인 / Header|User + Department, 해시 제외|200|
|GET|/licenses|로그인 / Catalog|q/category → License + 실제 좌석 집계·신청 가능 상태|200|
|GET|/licenses/{license_id}|로그인 / Request modal|License 상세|200|
|POST|/license-requests|USER / Request modal|license_id/reason/start_date/end_date → Request|201|
|GET|/license-requests/me|USER / My Requests|본인 Request + 사유·처리자·License|200|
|POST|/license-requests/{request_id}/cancel|USER / My Requests|본인 PENDING → CANCELED|200|
|GET|/license-assignments/me|USER / My Licenses|본인 ACTIVE + License/Request 목적·종료예정일|200|
|POST|/license-assignments/{assignment_id}/return|USER / Return modal|본인 ACTIVE → RETURNED|200|
|GET|/admin/dashboard|MASTER / Dashboard|좌석 합계·사용률·고사용률·최근 대기|200|
|GET|/admin/license-requests|MASTER / Pending|PENDING + User/License 잔여|200|
|GET|/admin/license-requests/history|MASTER / History|status 필터 APPROVED/REJECTED|200|
|POST|/admin/license-requests/{request_id}/approve|MASTER / Approval|reason → Request audit + Assignment|200|
|POST|/admin/license-requests/{request_id}/reject|MASTER / Rejection|reason → Request audit|200|
|GET|/admin/licenses|MASTER / License Management|License + 집계|200|
|POST|/admin/licenses|MASTER / Create modal|License 전체 필드|201|
|PATCH|/admin/licenses/{license_id}|MASTER / Edit modal|License 부분 필드|200|
|GET|/admin/licenses/{license_id}/assignments|MASTER / Users drawer|ACTIVE + User 인사정보 / Request 목적|200|
|POST|/admin/license-assignments/{assignment_id}/revoke|MASTER / Revoke|reason → Assignment audit|200|

모든 API의 정확한 request/response schema, 예제, 오류 status는 실행 앱에서 export한 API YAML을 기준으로 한다. 공통 오류 400/401/403/404/409/422.

## 구현 TODO
- [x] Phase 1: 저장소·프로토타입 조사 및 Gap 분석
- [x] Phase 2: requirements 원문 보존, 프로젝트 기술서 선작성
- [x] Phase 3: Entity/State/Business Rule/API·UI 매핑 확정
- [x] Phase 4: DB 모델·Alembic·PostgreSQL
- [x] Phase 5: API·인증·서비스·seed
- [x] Phase 6: 업무 규칙 pytest
- [x] Phase 7: Vue 레이아웃·라우팅·인증
- [x] Phase 8: USER 기능
- [x] Phase 9: MASTER 기능
- [x] Phase 10: Loading/Empty/Error
- [x] Phase 11: 디자인·반응형 검증
- [x] Phase 12: OpenAPI/DBML export
- [x] Phase 13: 스크린샷·HTML/PDF
- [x] Phase 14: README·발표 스크립트


## 최종 Phase 기록

|Phase|구현·주요 변경 파일|검증|다음 작업 / 발견 사항|
|---|---|---|---|
|1|reference 조사, 본 문서|기존 HTML 및 파일 확인|기존 가상 집계와 삭제 로직 재사용하지 않음|
|2|requirements.md, project-overview.md|명세 원문·16개 기술서 항목 확인|설계 확정|
|3|Entity/State/API·화면 매핑 표|명세의 11개 핵심 규칙 매핑|부서 공개 조회 API 추가를 가정에 기록|
|4|models/entities.py, alembic, Compose|upgrade/downgrade/upgrade, alembic check 통과|기존 5433 충돌 → 55434 사용|
|5|api, services, repositories, schemas, seed|실제 PostgreSQL seed 및 재실행 검증|bcrypt 해시 노출 없음, 이력 보존|
|6|backend/tests|PostgreSQL 업무 규칙·동시 승인·계약 검증|결과는 verification.md|
|7|router, stores/auth, layouts, AuthView|가입·로그인·역할 가드 E2E|부서 목록 실제 DB 연결|
|8|LicensesView, RequestsView, MyLicensesView|신청·취소·반납 E2E|모든 데이터 실제 API|
|9|DashboardView, 관리자 모드와 모달|승인·반려·회수·등록·수정 E2E|감사 사유와 좌석 일치|
|10|ResourceState, useResource, 오류 처리|Empty/API Error/재시도 E2E|진행 중 조회와 재조회 충돌 보완|
|11|style.css, 공통 컴포넌트|build, 1440/1024/768 가로 넘침 없음|실제 캡처 시각 검토|
|12|export_docs.py, YAML, DBML|모든 API·요청/응답 예제 Pydantic 검증|제출용 보안 스키마 제외|
|13|screenshots.mjs, pdf.mjs, HTML, PNG, PDF|11개 화면 캡처·PDF 생성|렌더 완료 대기로 전체 높이 캡처|
|14|README, presentation-script, verification|실행 명령·링크·산출물 확인|구현 TODO 없음; 제출자 파일명만 환경변수로 지정 가능|

완료 범위는 명세 MVP이다. 실제 SaaS provisioning 등 제외 기능은 구현하지 않았다. 이후 추가된 사용자 `.pages` 파일은 변경하지 않았다.
