# LiChU.

**한정된 SaaS Seat의 신청 → 승인·반려 → 할당 → 반납·회수를 하나의 Workflow로 관리합니다.**

Vue 3 + FastAPI + PostgreSQL 모노레포. 모든 업무 화면은 실제 API를 사용합니다. 외부 SaaS 계정 발급이나 Vendor API는 포함하지 않습니다.

## 빠른 실행

필수: Node.js 22.12 이상, Python 3.11 이상, Docker Compose. 아래 명령은 `Lichu/` 루트에서 시작합니다.

```sh
cp .env.example .env
docker compose up -d db
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.lock.txt
cd backend
.venv/bin/alembic upgrade head
.venv/bin/python -m app.db.seed
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

별도 터미널:

```sh
cd Lichu/frontend
npm ci
npm run dev
```

- 서비스: http://127.0.0.1:5173
- 실행 앱 OpenAPI/Swagger: http://127.0.0.1:8000/docs
- Vite `/api` 프록시 → `127.0.0.1:8000`. 다른 API 주소는 `API_PROXY_TARGET` 환경변수 사용.
- PostgreSQL은 로컬 55434 포트, Docker volume `lichu_data`에 저장합니다.
- `.env`는 backend 실행 위치와 무관하게 프로젝트 루트에서 읽습니다. 시스템 환경변수가 우선합니다.

## 개발 계정

| 역할 | 아이디 | 비밀번호 |
|---|---|---|
| MASTER | master | `.env`의 `MASTER_PASSWORD` (예제: `LichuMaster2026!`) |
| USER | myeongjin / seoyeon / jihoon / haeun | `.env`의 `DEMO_PASSWORD` (예제: `LichuDemo2026!`) |

예제 비밀번호는 로컬 데모 전용입니다. MASTER는 seed로만 생성되며 signup의 `role` 필드는 거부합니다. Seed는 master가 이미 있으면 기존 데이터를 변경하지 않습니다. 다른 부서의 임직원 81명, 실제 ACTIVE Assignment 208개, 대기·승인·반려 요청을 생성합니다. 재실행으로 비밀번호가 변경되지는 않습니다.

## 주요 화면

| 사용자 | 경로 | 기능 |
|---|---|---|
| Public | `/login`, `/signup` | 아이디 저장·계정 찾기 안내, 프로필 사진 포함 직원 가입 |
| USER | `/licenses` | 검색·분류, 단가·가용 좌석, 신청 |
| USER | `/requests` | 상태·사유·처리자 확인, 대기 취소 |
| USER | `/my-licenses` | 현재 권한 승인 기간, 확인 후 반납 |
| MASTER | `/admin` | 전체/사용/잔여 좌석, 대기 수, 사용률 |
| MASTER | `/admin/requests` | 대기 처리, 사유 입력, 승인/반려 이력 필터 |
| MASTER | `/admin/licenses` | 등록·수정, 현재 사용자 검색·권한 기간 수정·회수 |

변경 후 API를 재조회하여 좌석과 목록을 즉시 갱신합니다. 다른 사용자의 변경은 창 복귀 또는 30초 주기 조회로 반영됩니다. 처리 이력은 10건씩 표시합니다. 테이블은 좁은 화면에서 내부 스크롤하고 1440/1024/768px에 대응합니다.

## 데이터 및 정책

- `used_seats`는 DB 컬럼이 아닙니다. ACTIVE Assignment의 COUNT로 계산합니다.
- 동일 User + License의 PENDING Request 및 ACTIVE Assignment를 각각 부분 UNIQUE 인덱스로 제한합니다.
- 승인·회수·반납·좌석 수정은 License 행 잠금으로 직렬화합니다. 승인 상태 변경과 Assignment 생성은 같은 트랜잭션입니다.
- Request는 `PENDING → APPROVED / REJECTED / CANCELED`, Assignment는 `ACTIVE → RETURNED / REVOKED`만 가능합니다.
- 잔여 좌석 0에서도 신청 가능, 승인은 409. 기존 사용량 미만으로 좌석 수정도 409.
- 비활성 라이선스는 신청·승인 불가(400), 기존 할당은 유지되며 반납·회수는 가능합니다.
- 목적과 사용 예정 기간은 Request에 저장합니다. 승인 시 기간을 Assignment의 권한 승인 기간으로 복사하며 관리자가 이후 수정할 수 있습니다.
- 회원가입과 회원 정보 수정에서 프로필 사진을 등록할 수 있습니다. 사진이 없으면 기본 프로필을 표시합니다.
- 가격은 USD 데모 단가이며 실제 공급사 판매가가 아닙니다. 월/연 주기를 지원하고 월 환산액은 서버가 제공합니다.
- JWT Access Token만 사용하며 sessionStorage에 저장합니다. 만료 시 재로그인합니다. bcrypt는 UTF-8 기준 72바이트까지 입력받습니다.
- 예정 기간은 정보이며 자동 할당 지연·자동 회수는 없습니다. 요청·할당·라이선스 삭제 API는 없습니다.

## 구조

```text
frontend/src/
  api/          Axios, 통일된 오류 처리
  components/   카드, 모달, 상태·오류·빈 화면
  layouts/      사이드바, 헤더, 사용자 정보
  router/       인증·역할 가드
  stores/       Pinia 인증
  views/        실제 API 기반 USER/MASTER 화면
  types/ utils/ DTO, 날짜·가격, 서버 재조회
backend/app/
  api/          HTTP Router, 인증 의존성
  core/         설정, JWT/bcrypt, 오류
  models/       SQLAlchemy 2.x Entity
  schemas/      Pydantic Request/Response
  services/     상태 전이, 소유권, 트랜잭션 내 업무 규칙
  repositories/ DB 조회, 잠금, 좌석 집계
  db/           Session, seed
backend/alembic/ Migration
backend/tests/  업무 규칙, PostgreSQL 동시 승인
backend/scripts/export_docs.py
frontend/tests/            Playwright 실제 API E2E
frontend/scripts/          스크린샷·PDF
reference/                 원본 UX 프로토타입 (수정하지 않음)
docs/                      설계 및 제출 산출물
```

## 테스트

```sh
cd backend
.venv/bin/pytest -q
```

기본 pytest는 테스트 전용 SQLite를 사용하고 PostgreSQL 동시 잠금 테스트 1개를 건너뜁니다. PostgreSQL 전체 검증은 이름이 `_test`로 끝나는 별도 DB에서 실행합니다. **테스트 DB의 테이블은 매 테스트마다 재생성됩니다. 업무 DB를 지정하지 마세요.**

```sh
# 프로젝트 루트, Compose DB 실행 후
# 테스트용 DB가 처음 필요한 경우 한 번 실행
docker compose exec db createdb -U lichu lichu_test
cd backend
TEST_DATABASE_URL=postgresql+psycopg://lichu:lichu_local@localhost:55434/lichu_test .venv/bin/pytest -q
.venv/bin/alembic check
```

```sh
cd frontend
npm run build
npm test
npx playwright install chromium
# frontend/backend 및 seed가 실행 중이어야 함
npm run smoke
```

Smoke test는 고유 직원과 SaaS를 실제 DB에 생성하고 회원가입 → 신청 → 승인 → 반납 → 반려 → 취소 → 재승인 → 사용자 검색 → 권한 승인 기간 수정 → 회수를 검증합니다. 데모 데이터만 있는 별도 환경에서 실행하세요. `MASTER_PASSWORD`, `DEMO_PASSWORD`, `FRONTEND_URL` 환경변수로 설정할 수 있습니다. 기본값은 `.env.example`의 로컬 데모 값입니다.

검증 결과와 환경 한계는 [docs/verification.md](docs/verification.md)에 기록합니다.

## 과제 산출물 재생성

```sh
cd backend
PYTHONPATH=. .venv/bin/python scripts/export_docs.py
cd ../frontend
npm run screenshots
npm run pdf
```

- [기술서 Markdown](docs/project-overview.md) / [인쇄용 HTML](docs/project-overview.html)
- [제출용 PDF](docs/CLASS_NAME_Lichu-개요.pdf)
- [OpenAPI YAML](docs/CLASS_NAME_Lichu-API.yml) / [DBML](docs/CLASS_NAME_Lichu-DB.dbml)
- [UI 스크린샷](docs/screenshots/)
- [5분 발표 스크립트](docs/presentation-script.md)
- [명세 원문](docs/requirements.md) / [Gap·설계·API 표·구현 순서](docs/implementation-plan.md)

`SUBMISSION_CLASS`와 `SUBMISSION_NAME`을 **export 및 pdf 명령의 환경변수**로 지정하면 제출 파일명을 변경합니다. 기본값은 `CLASS_NAME`입니다. YAML은 실제 FastAPI schema에서 생성하되 과제 지침대로 securitySchemes와 operation security만 제외합니다. 실제 앱의 JWT 인증은 유지됩니다. DBML은 실제 ORM의 타입, PK/FK, NULL, UNIQUE, 체크 및 부분 인덱스 설명을 반영합니다. HTML은 Markdown 원문에 SVG UI Flow와 실제 스크린샷을 결합하고 A4 Print CSS를 포함합니다. PDF 출력이 불가능하면 HTML의 'PDF로 저장' 버튼 또는 브라우저 인쇄를 사용하세요.

## 이번 실행 환경

Docker Desktop을 시작하고 PostgreSQL 16 Compose 컨테이너의 healthy 상태, migration, seed, 테스트를 확인했습니다. 기존 5433 포트가 다른 서비스에서 사용 중이어서 기본 포트를 **55434**로 설정했습니다. `.env.example`, Compose, backend 기본 설정이 같은 포트를 사용합니다.

현재 제공된 개발 서버는 Compose DB에 연결됩니다. 초기 검증에 사용한 임시 PostgreSQL 17 프로세스는 종료했습니다. 기존 서비스와 포트는 변경하지 않았습니다.

## 현재 범위와 향후 고려

실제 SaaS provisioning, Vendor API, HR/SSO, Slack/email 알림, 자동 사용량 측정·회수, 예산, 다단계 결재, 자동 대기열, 결제는 구현하지 않습니다. 실제 기업 도입 시 self signup을 SSO/HR 연동으로 대체하는 것을 우선 검토합니다. 마스코트는 제공된 `frontend/public/lichu-mascot.png`만 사용합니다.
