# 회원가입 수정 및 OpenAI 진단 검증

현재 `dev`는 **수정 후 버전**입니다. 수정 전 커밋은 `baa909328b3d52279faa8cf1ba8fc090bf79aa51`이며 같은 브랜치에서 실제 GitHub Push 검사 10건을 기록했습니다.

## 변경 내용

- 고정 Salt + SHA-256 비밀번호 저장을 사용자별 무작위 Salt를 사용하는 bcrypt 비용 12로 변경했습니다.
- 비밀번호·이메일·전화번호 원문 로그를 제거하고 가입 완료 이벤트만 기록합니다.
- 합성 전화번호 필수 입력·저장은 유지합니다. 정책 승인 여부를 확인하기 전에는 해당 필드 후보가 남습니다.
- 기존 SHA-256 실습 계정은 로그인되지 않습니다. **테스트 데이터 채우기**로 새 계정을 생성하세요. 기존 데이터를 삭제하거나 비밀번호를 추측해 이관하지 않습니다.
- `signup-remediation.patch`는 수정 전 커밋용 기록입니다. 현재 소스에 다시 적용하지 마세요.

## 직접 검증 순서

1. CSI Docker와 Cloudflare 터널을 실행하고 Lichu 저장소의 `CSI_BACKEND_URL`이 현재 HTTPS 주소인지 확인합니다. 자세한 설정은 [Actions 가이드](GITHUB_ACTIONS_SETUP.md)를 참고하세요.
2. Lichu `dev`에서 소스 변경을 커밋·Push합니다. GitHub **Actions → CSI Security Scan**에서 해당 커밋의 실행을 엽니다.
3. **Analyze Java and Python snapshot and mask evidence**, **Submit signed findings to CSI** 단계의 성공과 Summary의 Scan ID를 확인합니다. Actions 성공은 접수 성공이지 Agent 분석 완료가 아닙니다.
4. CSI `http://localhost:5173`에 로그인하고 **Scan History**에서 Repository `ymj9608/Lichu`, Branch `dev`, Commit SHA, Scan ID가 일치하는 검사를 엽니다.
5. 상태 **COMPLETED**, 분석 모드 **LLM**, 탐지 결과 **5건**을 확인합니다. `LLM_FALLBACK`이면 OpenAI 호출 또는 응답 검증에 실패해 규칙 기반으로 대체된 상태입니다. `RULE_BASED`이면 LLM 비활성 설정입니다.
6. 이전 동일 브랜치 검사와 비교해 **신규 0 / 미탐지 5 / 유지 5**인지 확인합니다. SEC-02 1건, SEC-03 1건, SEC-05 3건이 사라지고 POL-01 5건이 남는 것이 예상 결과입니다. 미탐지는 취약점 상태의 자동 RESOLVED 처리가 아닙니다.
7. 남은 Finding에서 **AI Analysis**, **Security References**를 열어 설명과 실제 문서 조항·페이지를 확인합니다. **Execution Logs**에서 MCP 호출, 문서 검색, 보고서 저장을 확인합니다. 정책 후보는 법률 위반 확정이 아닙니다.

`LLM`은 GPT가 기존 정적 분석 후보의 설명·개선 권고를 보완했다는 의미입니다. 도구 선택은 LangGraph 코드가 수행하며 외부 LLM에는 코드 원문·개인정보 값·PDF 전체 원문을 보내지 않습니다. 이미 완료된 수정 전 검사는 RULE_BASED 기록으로 유지됩니다.

## 회원가입 동작 검증

GitHub Push는 로컬 앱을 자동 배포하지 않습니다. 소스 변경을 로컬 사이트에도 반영하려면 Lichu 디렉터리에서 실행합니다.

```sh
docker compose --env-file .env.csi -f compose.csi-lab.yml up -d --build backend frontend
```

`http://127.0.0.1:8081/signup`에서 **수정 후 버전** 표시를 확인하고, **테스트 데이터 채우기**로 합성 계정을 만들어 가입·로그인합니다. 전화번호가 없으면 가입할 수 없습니다. 실제 개인정보는 입력하지 마세요.

백엔드 회귀 테스트는 합성 값의 로그 미노출, bcrypt 비용, 무작위 Salt, 기존 SHA-256 로그인 거절, 새 계정 가입·로그인과 전화번호 검증을 확인합니다.
