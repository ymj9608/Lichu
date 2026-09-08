# 검증 기록

2026-09-08, macOS, Python 3.11.9, Node 26.7.0. 설치 버전은 frontend/package-lock.json 및 backend/requirements.lock.txt에 고정했습니다.

|검증|결과|
|---|---|
|Docker Compose 설정 문법|`docker compose config --quiet` 통과|
|Docker PostgreSQL 16|`docker compose up -d --wait db` healthy, 127.0.0.1:55434|
|Alembic|초기 upgrade, downgrade→upgrade 왕복 통과; `alembic check` 차이 없음|
|Seed|81 User / 6 License / 208 ACTIVE Assignment; 실제 집계 240 전체 / 208 사용 / 32 잔여 / 3 대기|
|Seed 재실행|기존 데이터 변경 없이 종료|
|Backend pytest|PostgreSQL에서 25 passed (업무 규칙 23 + 제출 계약 2)|
|마지막 좌석 동시 승인|2개 독립 트랜잭션 중 1개 승인, 1개 409; ACTIVE Assignment 1개|
|Vue TypeScript / Vite|`npm run build` 성공|
|Vitest|`npm test`: 3 passed|
|Playwright|`npm run smoke`: 2 passed|
|반응형|1440/1024/768px 페이지 가로 넘침 없음, 768 캡처 확인|
|OpenAPI|23개 operation의 실제 Router 매핑 및 요청/성공 응답 예제 Pydantic 검증|
|DBML|ORM metadata에서 PK/FK/타입/NULL/UNIQUE/관계·제약 설명 생성|
|Screenshot|로그인·가입·탐색·내 신청·내 라이선스·관리자 화면 및 1024/768 총 11 PNG|
|PDF|Chromium A4 출력 성공; SVG UI Flow + 핵심 화면 6개 포함, 약 1.1MB|

## 실제 브라우저 검증 범위

직원 회원가입 → 로그인 → 회원 정보 수정 진입 → 관리자 경로 접근 시 직원 화면 복귀 → 관리자 라이선스 등록 → 직원 신청 → 관리자 승인 및 Pending에서 제거 → 처리 이력·반려 필터 → 사용자 승인 사유 확인 → 내 라이선스 반납 → 재신청·반려·사유 확인 → 재신청·취소 → 재신청·승인 → 관리자 직원 검색 → 권한 승인 기간 수정 → 사유 입력·회수 → 사용 중 목록에서 제거 → 관리자 비활성 수정. 별도 테스트로 검색 Empty, API Error, 재시도를 확인했습니다. pageerror는 없었습니다.

## 해결한 검증 문제

- 샌드박스 네트워크 제한은 의존성 설치 권한 확장으로 해결했습니다.
- Docker 데몬 시작 후 기존 5433 충돌을 발견하여 기존 서비스를 유지하고 Lichu 포트를 55434로 변경했습니다.
- 초기 PostgreSQL 17에서 migration/seed 및 E2E를 먼저 검증하고, 최종 Compose PostgreSQL 16에서도 migration/seed/pytest를 검증했습니다.
- Playwright 이름 선택자는 이름+사번 복합 요소에 맞게 수정했습니다.
- Vitest가 Playwright 파일을 수집하지 않도록 `src/**/*.test.ts`로 범위를 지정했습니다.
- 스크린샷은 데이터·폰트·프레임 렌더 완료 후 캡처하도록 수정했습니다.
- 이력은 10건씩 표시하며 필터 변경과 주기 조회가 겹쳐도 후속 재조회를 누락하지 않습니다.

## 남은 구현 TODO와 범위

명세 MVP 구현 TODO는 없습니다. 제출 파일명은 제공되지 않은 반/이름 대신 CLASS_NAME 기본값입니다. `SUBMISSION_CLASS`, `SUBMISSION_NAME`으로 재생성할 수 있습니다. 테스트 실행 시 제3자 Starlette/httpx·anyio의 deprecation warning 2건이 있으나 실패는 없습니다. 외부 SaaS 발급·SSO·HR·알림·자동 회수 등 명세 제외 기능은 구현하지 않았습니다.
