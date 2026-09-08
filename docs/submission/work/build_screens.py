from build_docs import HERE, PREFIX, REQ, FUNCTIONS, AUTHOR, DATE, VERSION, esc, table, page, document
from screen_specs import SPECS


def build():
    screens={}
    for r in FUNCTIONS:
        for sid in r['screens']:
            screens.setdefault(sid,[]).append(r)
    assert set(screens)==set(SPECS)
    pages=[]
    rows=[[sid,' / '.join(dict.fromkeys(r['screen_desc'] for r in rs)),', '.join(r['id'] for r in rs)] for sid,rs in screens.items()]
    pages.append(page('<h1>LiChU. 화면설계서</h1><p>사내 SaaS 라이선스 신청 · 승인 · 할당 · 반납 · 회수</p><div class="meta">작성자: '+AUTHOR+'　 작성일: '+DATE+'　 버전: '+VERSION+'<br>ID 체계: REQ-FUNC-### ↔ SCR-XXX-###</div><h2>화면 목록</h2>'+table(['화면 ID','화면명 / 경로','관련 요구사항'],rows)+'<p class="muted">수정 이력: 2026-09-08 v1.2 · 현재 구현 및 기존 요구사항 정의서 기준 작성.</p>'))
    flow='<img style="width:100%;height:163mm;object-fit:contain" src="assets/ui-flow.png">' if (HERE/'assets/ui-flow.png').exists() else '<div class="placeholder">캡처 필요: 사용자 신청→관리자 승인·반려→할당→반납·회수 흐름도</div>'
    pages.append(page('<h1>전체 사용자 흐름</h1>'+flow+'<h2>문서 읽기 기준</h2><p>각 화면은 ① 기본 정보 ② 번호가 붙은 실제 화면 ③ 사용자 흐름 ④ 디스크립션 ⑤ 예외 처리 및 정책으로 구성한다. 캡처 번호와 설명 표 NO는 1:1 대응한다. 등록·수정은 같은 SCR-ADM-005의 두 상태이다.</p><p>캡처는 현재 Vue/FastAPI 코드를 별도 SQLite 시연 DB와 기본 seed 데이터로 실행한 화면이다. 운영 데이터 캡처나 PostgreSQL 동시성 검증 결과가 아니다. 데이터 모델의 기준 DB는 PostgreSQL이다.</p><p>화면 이미지에는 설명용 번호만 덧붙였다. 정상 화면은 1440 × 1000 뷰포트에서 전체 문서를 촬영하고, 모달은 표시 영역을 촬영했다. 이미지 안 인명·이메일·좌석 수는 시연 데이터다.</p>'))
    for sid,rs in screens.items():
        spec=SPECS[sid]
        title=rs[0]['screen_desc'].split(' /')[0]
        reqs=', '.join(r['id'] for r in rs)
        meta='<div class="meta">화면 ID: '+sid+'　 화면명: '+esc(title)+'<br>Depth / 경로: '+esc(rs[0]['screen_desc'])+'<br>관련 요구사항: '+reqs+'　 작성·수정: '+DATE+' '+VERSION+'</div>'
        pic=f'<img class="shot" style="height:180mm" src="assets/{sid}.png">'
        if not (HERE/'assets'/f'{sid}.png').exists():pic='<div class="placeholder">캡처 필요: '+esc(title)+'에서 '+esc(', '.join(x[0] for x in spec['rows']))+'가 모두 보이는 화면</div>'
        pages.append(page('<h1>'+esc(title)+'</h1>'+meta+'<h2>② 화면 구성</h2>'+pic+'<p class="caption">실제 실행 화면 · 빨간 번호는 다음 페이지의 디스크립션 NO와 대응</p><h2>③ 사용자 흐름</h2><div class="flow">'+esc(spec['flow'])+'</div>','','LiChU. 화면설계서 · '+sid))
        if sid=='SCR-ADM-005':
            pages.append(page('<h1>라이선스 등록 · 초기 상태</h1>'+meta+'<h2>② 등록 모드</h2><img class="shot" style="height:177mm" src="assets/SCR-ADM-005-create.png"><p class="caption">수정 모드와 동일한 번호·필드 구조. 생성 API만 POST로 달라진다.</p><div class="flow">기본값: 카테고리 개발 / 총 좌석 1 / 단가 0 / 월간 / 활성. 필수 내용을 입력하고 저장 → 201 생성 → SCR-ADM-003 목록 갱신.</div>','','LiChU. 화면설계서 · '+sid))
        desc=[]
        for i,(element,numbers,logic,api,destination) in enumerate(spec['rows'],1):
            ids=', '.join('REQ-FUNC-'+n for n in numbers.split(','))
            desc.append([str(i),element,ids,logic+'\n이동: '+destination,api])
        body='<h1>'+esc(title)+' · 상세 동작</h1>'+meta+'<h2>④ 디스크립션</h2>'+table(['NO','UI 요소명','관련 요구사항 ID','인터랙션 및 로직 / 이동','호출 API'],desc)
        body+='<h2>⑤ 예외 처리 및 정책</h2><div class="intro">'+esc(spec['policy'])+'</div>'
        body+=table(['상태','처리'],[
            ['정상',spec['flow']],
            ['로딩 / 중복 클릭','목록은 로딩 상태를 표시. 저장 처리 중 버튼을 비활성화한다. 필수 입력은 브라우저 기본 검증과 서버 검증을 함께 사용한다.'],
            ['빈 화면','목록의 빈 상태는 위 화면별 정책에 따른다. 입력 모달에서는 빈 데이터 대신 필수 입력 안내를 사용한다.'],
            ['네트워크 / 500','오류 문구를 표시하고 사용자가 재시도한다. 변경 API 실패 후에는 먼저 목록에서 반영 여부를 확인한다.'],
            ['400 / 401 / 403 / 404 / 409 / 422','화면별 적용 코드는 위 정책 및 API 명세 참조. 입력 형식은 422, 잘못된 상태 전이는 400으로 구분한다.']])
        body+='<h2>인수 조건 (AC)</h2>'+''.join('<p>AC-'+str(i).zfill(2)+'　'+esc(x)+'</p>' for i,x in enumerate(spec['ac'],1))
        body+='<h2>데이터 연결</h2><p class="mono">'+esc(' / '.join(r['db'] for r in rs))+'</p>'
        pages.append(page(body,'screen','LiChU. 화면설계서 · '+sid))
    pages.append(page('<h1>공통 상태 및 예외 정책</h1>'+table(['상태','사용자 화면','API / 데이터'],[
        ['정상','성공 안내 후 대상 목록 또는 사용자 정보 갱신.','조회·수정 200 / 생성 201'],
        ['형식/필수 입력','HTML required/min/max 등으로 1차 검증. 서버 오류는 화면 상단 또는 모달, 회원가입은 필드 하단도 표시.','422 VALIDATION_ERROR / INVALID_DEPARTMENT'],
        ['업무 상태 오류','이미 처리된 요청·종료된 할당·비활성 라이선스 안내.','400 INVALID_TRANSITION / LICENSE_INACTIVE'],
        ['미인증/만료','토큰 제거 후 로그인 및 만료 안내. 로그인 자격 실패는 현재 폼에 오류.','401 UNAUTHORIZED / INVALID_CREDENTIALS'],
        ['권한/소유권','역할별 메뉴·Route Guard 및 서버 역할/소유권 검사.','403 FORBIDDEN / NOT_OWNER'],
        ['대상 없음','없는 단일 라이선스·신청·할당 오류. 빈 목록과 구분.','404 NOT_FOUND'],
        ['중복·좌석·동시 충돌','오류 표시 후 최신 목록 재조회. 승인·신청 등 재판단.','409 DUPLICATE_USER / ALREADY_ASSIGNED / DUPLICATE_REQUEST / LICENSE_SEAT_FULL / SEATS_BELOW_USAGE / CONFLICT'],
        ['빈 목록','검색 결과 없음·대기 없음·할당 없음 등 문맥에 맞는 안내.','200 및 빈 배열 / 집계 0'],
        ['로딩','ResourceState의 로딩 표시. 변경 요청 busy 동안 중복 제출 제한.','요청 완료 후 상태 해제'],
        ['네트워크 실패','연결 오류 표시. 목록은 재시도, 폼은 입력 보존 후 다시 제출.','HTTP 응답이 없을 수 있음'],
        ['서버 오류','목록·모달 오류를 표시. 완료 여부 확인 후 수동 재시도.','500 INTERNAL_ERROR']])+'<h2>갱신 및 기간 정책</h2><p>주요 목록은 창 복귀와 화면이 보이는 동안 30초 주기로 재조회한다. 실시간 WebSocket은 사용하지 않는다. 승인은 즉시 ACTIVE 할당을 생성하고, 승인 종료일 도달에 따른 자동 회수는 하지 않는다. 반납·회수는 별도 확정 동작이다.</p><h2>범위</h2><p>외부 SaaS 계정 발급·실제 사용량 측정·SSO·결제·알림·다단계 승인·자동 대기열은 포함하지 않는다. API나 화면이 없는 기능을 문서에 추가하지 않았다.</p>'))
    for offset in range(0,len(FUNCTIONS),10):
        rows=[[r['id'],', '.join(r['screens']),'\n'.join(r['apis']),r['db']] for r in FUNCTIONS[offset:offset+10]]
        pages.append(page('<h1>추적성 · 화면 ↔ 요구사항 ↔ API ↔ DB</h1><p>기존 요구사항 정의서의 ID를 그대로 사용하며, 전체 21개 기능 요구사항이 20개 화면 ID로 연결된다.</p>'+table(['요구사항 ID','화면 ID','호출 API','DB 데이터'],rows)))
    document('화면설계서',pages)
    print(f'Screen specification: {len(screens)} screen IDs, {len(pages)} pages.')


if __name__=='__main__':build()
