# 회원가입 업무 맥락 로그

회원가입이 실행되면 `BUSINESS_CONTEXT` JSON 로그를 남깁니다. 이름·전화번호·이메일·계정 ID·비밀번호·토큰·요청 본문은 포함하지 않습니다. 추적 ID는 서버가 새 UUID로 생성하며 요청 헤더의 값을 신뢰하지 않습니다. 응답의 `X-Trace-ID`로 해당 요청을 찾을 수 있습니다.

## 확인할 맥락

- `businessProcess=INTERNAL_LICENSE_REQUEST_AND_APPROVAL`: 사내 라이선스 신청·승인 기능.
- `User.name`: 신청자 표시 목적. 실제 사용 위치는 `frontend/src/views/RequestsView.vue`이며 일반 회원가입 저장 경로에도 존재합니다.
- `CsiSignupProfile.phone_number`: 실습용 합성 데이터 진단 목적. 실습 모드에서 합성 입력 검증을 통과했을 때만 포함됩니다.
- `purposeSource=APPLICATION_DECLARATION`: 개발자가 코드의 사용처를 근거로 선언한 목적입니다. 승인된 정책이나 독립적인 감사 결과가 아닙니다.
- `approvalStatus=NOT_CHECKED`, `retentionStatus=NOT_CONFIGURED`, `policyCompliance=NOT_ASSESSED`: 승인·보유기간·정책 준수를 지어내지 않습니다. 보유기간 값을 로그에 쓰는 것만으로 삭제 기능이 구현되는 것도 아닙니다.

`REQUEST_STARTED` → `INPUT_ACCEPTED` → `DB_COMMITTED`는 정상적인 경로입니다. `DB_COMMITTED`는 SQLAlchemy의 실제 커밋 완료 callback에서만 기록합니다. 검증 거절은 `HTTP_FINISHED`의 409/422로 확인하고, DB 실패는 `DB_ROLLED_BACK`을 확인합니다. `HTTP_FINISHED`는 HTTP 응답 단계이며 DB 커밋 증거로 사용하면 안 됩니다. FastAPI dependency 종료 시점에 따라 HTTP 이벤트와 커밋 이벤트의 순서는 달라질 수 있습니다. fieldContext는 다루는 필드의 맥락이며 `INPUT_ACCEPTED`/rollback에서는 저장 완료를 의미하지 않습니다.

## 직접 실행

Lichu 폴더에서 실행합니다. DB 볼륨을 삭제하지 않습니다.

```sh
docker compose --env-file .env.csi -f compose.csi-lab.yml up -d --build backend
```

Backend 재생성 후 frontend nginx가 이전 주소를 기억하면 다음으로 갱신합니다.

```sh
docker compose --env-file .env.csi -f compose.csi-lab.yml exec -T frontend nginx -s reload
docker compose --env-file .env.csi -f compose.csi-lab.yml logs -f --since 1m backend | rg --line-buffered BUSINESS_CONTEXT
```

다른 터미널에서 아래 명령으로 합성 계정 1개를 생성하고 정상/중복/입력 오류를 재현합니다. 스크립트는 활성화된 localhost 실습 서버만 대상으로 하며 응답 개인정보를 출력하지 않습니다.

```sh
python3 scripts/verify_business_context.py
```

출력된 `traceId`로 필터링하면 동일 요청의 로그만 확인할 수 있습니다. UI에서 확인하려면 `http://localhost:8081` 회원가입 화면의 테스트 데이터 채우기를 사용하고 브라우저 개발자 도구 Network에서 회원가입 응답 `X-Trace-ID`를 확인하세요.

## CSI와의 경계

GitHub Push는 기존 정적 분석 workflow를 실행합니다. 현재 Actions는 애플리케이션을 실행하지 않으며 이 런타임 로그를 CSI로 전송하지 않습니다. 따라서 이 변경만으로 CSI Agent가 승인 기록·실제 저장 결과를 자동으로 알게 되지는 않습니다. 이번 기능은 운영자가 실행 맥락을 직접 검증할 수 있는 관측 로그입니다. CSI의 Execution Logs와 Lichu의 BUSINESS_CONTEXT 로그는 별개입니다. 향후 연동에는 인증된 수집 경로와 scan/commit/실행 환경 연결, 보존·접근 통제가 필요합니다.

## 검증 기록

2026-10-19 Backend 테스트 34개 통과, PostgreSQL 전용 테스트 1개는 SQLite 환경에서 skip했습니다. 신규 테스트는 일반/실습 모드 구분, 추적 ID 일치와 클라이언트 ID 무시, 개인정보 비노출, 입력 거절, 커밋 실패 시 rollback 로그만 남는 동작을 검증합니다.

로컬 실습 서버에서도 정상 회원가입 201, 중복 409, 잘못된 전화번호 422를 실제 요청으로 확인했습니다. 정상 trace `524da269-7197-476a-9e78-9389556a9cad`에만 `DB_COMMITTED`가 있고 거절 요청에는 없습니다. 이 요청은 격리된 실습 DB에 합성 계정 1개를 생성했습니다. 실제 관측 순서는 REQUEST_STARTED → INPUT_ACCEPTED → HTTP_FINISHED → DB_COMMITTED였으며, 이를 통해 HTTP 성공 이벤트와 DB 커밋 이벤트가 서로 다른 시점임을 확인했습니다.

전체 테스트 재현 명령(기존 일반 회원가입 테스트는 CSI_LAB_MODE=false에서 실행하고 실습 테스트가 모드를 개별 설정):

```sh
docker compose --env-file .env.csi -f compose.csi-lab.yml run --rm --no-deps -e CSI_LAB_MODE=false -v "$PWD/docs:/docs:ro" backend python -m pytest tests -q -p no:cacheprovider
```
