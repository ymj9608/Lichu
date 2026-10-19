# 전화번호 회원가입 진단 실습

`dev` 브랜치는 기존 전화번호 입력·저장 기능에 필수 입력 검증과 의도적인 전화번호 로그 노출을 추가한 수정 전 실습 버전입니다. `CSI_LAB_MODE=true`인 별도 실습 DB에서만 사용합니다. 일반 회원가입 모드는 전화번호 입력을 거절하며 이 로그 함수를 호출하지 않습니다.

## 직접 확인

1. CSI Docker 서비스와 외부 HTTPS 터널을 실행합니다. 설정은 [GitHub Actions 가이드](GITHUB_ACTIONS_SETUP.md)를 따릅니다.
2. Lichu 실습 사이트 `http://127.0.0.1:8081/signup`에서 **테스트 데이터 채우기**를 누릅니다. 전화번호는 `010-0000-1234` 같은 합성 값만 사용합니다.
3. 전화번호를 지우면 가입할 수 없습니다. 합성 번호를 입력하면 가입·로그인할 수 있고, 실습 서버 로그에 번호가 마스킹 없이 기록됩니다.
4. `dev`에서 소스 변경을 커밋하고 Push하면 **CSI Security Scan**이 실행됩니다. 회원가입 버튼 자체가 보안 검사를 트리거하지는 않습니다.
5. Actions Summary의 Scan ID를 CSI Scan History에서 찾습니다. Repository `ymj9608/Lichu`, Branch `dev`, Commit SHA가 Push한 커밋과 같고 상태가 `COMPLETED`인지 확인합니다.

## 예상 탐지와 수정

- 이전 `main` 기준 9건 → 이 버전 10건: `backend/app/core/csi_signup.py`의 전화번호 로그가 **SEC-05 / HIGH / SUSPECTED**로 추가됩니다. 파일 선언을 근거로 한 기존 정책 후보는 별도로 유지됩니다.
- GitHub로 전송하는 코드 근거에서는 문자열을 마스킹합니다. 취약한 앱 로그와 CSI에 저장되는 근거는 별개입니다.
- `git apply --check docs/csi/signup-remediation.patch` 후 `git apply docs/csi/signup-remediation.patch`로 비밀번호 저장 및 모든 민감정보 로그를 수정할 수 있습니다. 패치 적용 후 예상 결과는 **5건**이며 모두 정책 검토 후보입니다.
- 패치 적용 후 기존 실습 계정은 다시 가입해야 합니다. 로컬 앱 반영에는 Docker 재빌드가 필요합니다. Push는 검사만 실행하며 앱을 자동 배포하지 않습니다.

현재 정책 후보와 `SUSPECTED`는 법률 위반 확정이 아닙니다. Agent가 `RULE_BASED`로 설정되어 있으면 LangGraph·MCP·RAG 경로를 실행하되 외부 LLM은 사용하지 않습니다.

## 로컬 검증

변경 전 9건, 변경 후 10건, 수정 패치 적용 복사본 5건을 실제 Semgrep으로 검증했습니다. 변경 전후 fingerprint 비교에서 전화번호 로그 1건만 추가되었습니다. 변경 버전과 패치 버전 모두 백엔드 테스트 29개 통과·1개 건너뜀(기존 PostgreSQL 동시성 테스트)이며, 브라우저에서 전화번호 필수 입력·가입·로그인과 모바일 가로 넘침 없음을 확인했습니다. 실제 GitHub 실행 결과는 Actions와 CSI에서 해당 커밋으로 확인합니다.
