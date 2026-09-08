"""Build five submission artifacts from code, traceability data, and real captures."""
import copy
import html
import json
import re
import sys
from pathlib import Path

import capture_server  # Sets an isolated, non-production application environment.
import yaml
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects import postgresql
from app.main import app
from app.models.entities import Base
from openapi_spec_validator import validate

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREFIX = '판교5-P157-윤명진'
OUT = HERE.parent / PREFIX
OUT.mkdir(exist_ok=True)
REQ = json.loads((HERE.parent / 'requirements-definition.json').read_text(encoding='utf-8'))
FUNCTIONS = REQ['functional']
AUTHOR = '판교5 / P157 / 윤명진'
DATE = '2026-09-08'
VERSION = 'v1.2'


def esc(value):
    return html.escape(str(value))


def table(head, rows, cls=''):
    return '<table class="' + cls + '"><thead><tr>' + ''.join('<th>'+esc(x)+'</th>' for x in head) + '</tr></thead><tbody>' + ''.join('<tr>'+''.join('<td>'+esc(x).replace('\n','<br>')+'</td>' for x in row)+'</tr>' for row in rows) + '</tbody></table>'


CSS = '''
*{box-sizing:border-box}html,body{margin:0;background:white;color:#24262c;font-family:"Malgun Gothic",Arial,sans-serif;letter-spacing:0}body{font-size:9pt;line-height:1.5}h1{font-size:19pt;margin:0 0 5mm}h2{font-size:12pt;margin:4mm 0 2mm;break-after:avoid}h3{font-size:10pt;margin:3mm 0 1.5mm}p{margin:1.5mm 0}table{border-collapse:collapse;width:100%;table-layout:fixed;margin:2mm 0;font-size:8pt}th{background:#eceef2;text-align:left;font-weight:700}td,th{border:1px solid #d3d7df;padding:1.5mm 2mm;vertical-align:top;overflow-wrap:anywhere}tr:nth-child(even) td{background:#fafbfc}code,pre,.mono{font-family:Consolas,"Malgun Gothic",monospace;font-size:8pt}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f6f8;padding:3mm;margin:2mm 0}.page{position:relative;width:210mm;height:297mm;padding:16mm 12mm 13mm;break-after:page;overflow:hidden}.page:last-child{break-after:auto}.running{position:absolute;top:0;left:0;right:0;height:9mm;background:#1b1b20;color:white;padding:2mm 12mm;font-size:8pt;display:flex;justify-content:space-between}.foot{position:absolute;bottom:5mm;left:12mm;right:12mm;border-top:1px solid #e3e5e9;padding-top:2mm;display:flex;justify-content:space-between;color:#7c828d;font-size:7pt}.muted{color:#68707d}.meta{font-size:8pt;background:#f5f6f9;padding:2.5mm;border:1px solid #dce0e7;margin:2mm 0}.intro{border-left:3px solid #ba2530;background:#f7f6fa;padding:3mm;margin:3mm 0}.shot{width:100%;height:94mm;object-fit:contain;border:1px solid #e1e4e8;display:block;background:white}.shot.modal{height:90mm}.caption{text-align:center;font-size:7pt;color:#777;margin:1mm 0 2mm}.flow{background:#f3f4f7;border-left:3px solid #667da0;padding:2mm 3mm;margin:2mm 0;font-size:8pt}.screen table{font-size:7.3pt}.screen table th:nth-child(1){width:7%}.screen table th:nth-child(2){width:16%}.screen table th:nth-child(3){width:18%}.screen table th:nth-child(4){width:34%}.screen table th:nth-child(5){width:25%}.screen td{padding:1.3mm}.policies{font-size:7.7pt;margin:2mm 0}.cover{border-top:6mm solid #b62531;display:flex;align-items:center;justify-content:center;text-align:center}.cover h1{font-size:29pt;color:#bc2530;margin:5mm 0 1mm}.cover .cover-meta{width:100mm;border:1px solid #d03944;border-radius:2mm;padding:4mm;margin:14mm auto}.cover table td{border:0;border-bottom:1px solid #efdadd;background:white;padding:3mm}.cover table td:last-child{text-align:right;font-weight:bold}.endpoint-title{padding:3mm;background:#e8eefb;border:1px solid #d2d9e7;font-weight:bold;font-size:11pt;overflow-wrap:anywhere}.method{display:inline-block;padding:1mm 2mm;background:#3674c1;color:white;border-radius:1mm;margin-right:2mm;font-size:9pt}.method.post{background:#219369}.method.patch{background:#b37822}.endpoint h2{font-size:10pt}.endpoint table{font-size:7.7pt}.endpoint .description{font-size:8pt;padding:2mm 3mm;background:#f0eef8;margin:2mm 0}.endpoint .reqtable th:nth-child(1){width:25%}.endpoint .reqtable th:nth-child(2){width:20%}.endpoint .reqtable th:nth-child(3){width:12%}.endpoint .reqtable th:nth-child(4){width:43%}.schemas table{font-size:8pt}.landscape .page{width:297mm;height:210mm;padding:15mm 9mm 12mm}.landscape .running{padding-left:9mm;padding-right:9mm}.landscape .foot{left:9mm;right:9mm}.landscape h1{font-size:16pt}.landscape table{font-size:8pt}.landscape .dbtable th:nth-child(1){width:6%}.landscape .dbtable th:nth-child(2){width:18%}.landscape .dbtable th:nth-child(3){width:17%}.landscape .dbtable th:nth-child(4){width:7%}.landscape .dbtable th:nth-child(5){width:15%}.landscape .dbtable th:nth-child(6){width:37%}.placeholder{height:90mm;display:grid;place-items:center;border:2px dashed #8a9098;background:#f8f9fb;text-align:center;padding:10mm}.relation-table th:nth-child(1){width:20%}.relation-table th:nth-child(2){width:12%}.relation-table th:nth-child(3){width:25%}.relation-table th:nth-child(4){width:43%}@page{size:A4;margin:0}@media print{*{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
'''


def page(content, kind='', title='LiChU. 사내 SaaS 라이선스 관리'):
    return f'<section class="page {kind}"><div class="running"><b>{esc(title)}</b><span>{VERSION}</span></div>{content}<div class="foot"><span>LiChU. · {AUTHOR} · {DATE}</span><span class="page-number"></span></div></section>'


def document(name, pages, landscape=False):
    body=''.join(pages)
    count=len(pages)
    n=iter(range(1,count+1))
    body=re.sub(r'<span class="page-number"></span>',lambda _:f'<span>{next(n)} / {count}</span>',body)
    extra='@page{size:A4 landscape;margin:0}' if landscape else ''
    extra+=' .apiindex th:nth-child(1){width:8%}.apiindex th:nth-child(2){width:37%}.apiindex th:nth-child(3){width:18%}.apiindex th:nth-child(4){width:14%}.apiindex th:nth-child(5){width:15%}.apiindex th:nth-child(6){width:8%}.responses th:nth-child(1){width:10%}.responses th:nth-child(2){width:25%}.responses th:nth-child(3){width:65%}'
    (HERE/(name+'.html')).write_text(f'<!doctype html><html lang="ko"><meta charset="utf-8"><title>{esc(PREFIX)}-{esc(name)}</title><style>{CSS}{extra}</style><body class="{"landscape" if landscape else ""}">{body}</body></html>',encoding='utf-8')


def refs_for(method,path):
    return [r for r in FUNCTIONS if f'{method.upper()} {path}' in r['apis']]


FIELD = {
 'id':'고유 식별자', 'employee_no':'사번. 중복 불가', 'name':'이름 / 명칭', 'department_id':'소속 부서 ID',
 'department':'소속 부서 상세', 'job_title':'직급 / 직책', 'email':'회사 이메일. 소문자 정규화, 중복 불가',
 'username':'로그인 아이디. 중복 불가', 'password':'비밀번호. 가입 시 8자 이상 및 UTF-8 72바이트 이하',
 'password_confirm':'비밀번호 확인. password와 일치', 'password_hash':'bcrypt 해시. 평문 저장 및 사용자 응답 노출 금지 (REQ-NFN-001)',
 'profile_image':'선택 프로필 Data URL (JPEG/PNG/WEBP). null은 기본 프로필. 별도 용량 제한 없음',
 'role':'USER(임직원) / MASTER(관리자). 가입 시 USER 고정', 'created_at':'생성 시각(UTC)', 'updated_at':'최종 수정 시각(UTC)',
 'vendor':'공급사', 'plan_name':'구독 플랜', 'category':'분류(개발 / 디자인 / 생산성 등)', 'description':'라이선스 설명',
 'total_seats':'전체 좌석 수. 현재 ACTIVE 사용량 미만으로 축소 불가', 'unit_price':'사용자당 USD 단가. 소수 둘째 자리까지, 총 12자리',
 'billing_cycle':'MONTHLY(월간) / YEARLY(연간)', 'used_seats':'ACTIVE 할당 COUNT. 저장 컬럼 아님',
 'available_seats':'total_seats - used_seats. 저장 컬럼 아님', 'utilization':'used_seats / total_seats × 100, 소수 첫째 자리. 0석이면 0',
 'monthly_unit_price':'연간 단가는 12로 나눈 월 환산 금액(소수 둘째 자리)', 'request_block':'기존 할당 / 대기 신청 / 비활성 상태만 차단. 잔여 0석 자체는 차단 사유 아님',
 'user_id':'대상 직원 users.id', 'license_id':'대상 라이선스 licenses.id', 'request_id':'원본 신청 license_requests.id. UNIQUE, 직접 배정 이력은 null 가능',
 'user':'직원 정보(UserOut)', 'license':'라이선스 정보 및 현재 좌석 집계(LicenseOut)', 'reason':'사용 목적 또는 처리 사유. 입력은 공백 제거 후 1~4000자',
 'start_date':'사용 시작 예정일', 'end_date':'사용 종료 예정일. AssignmentOut에서는 원본 신청의 종료일',
 'decision_reason':'승인 / 반려 사유. 처리 전 null', 'processed_by':'처리자 users.id. 처리 전 null', 'processor':'처리자 정보(UserOut), 처리 전 null',
 'processed_at':'승인 / 반려 처리 시각(UTC)', 'canceled_at':'사용자 취소 시각(UTC)', 'assigned_by':'할당 처리자 users.id', 'assigned_at':'할당 시각(UTC)',
 'valid_from':'권한 승인 시작일. 승인 시 신청 시작일 복사', 'valid_until':'권한 승인 종료일. 자동 회수 트리거 아님',
 'ended_by':'반납 / 회수 수행자 users.id', 'ended_at':'반납 / 회수 시각(UTC)', 'end_reason':'종료 사유. 직접 반납은 사용자 직접 반납',
 'access_token':'JWT Access Token (실제 토큰 대신 명세 예시 문자열)', 'token_type':'bearer', 'code':'기계 판독 오류 코드',
 'message':'사용자용 오류 메시지', 'fields':'필드별 오류 메시지 사전. 없으면 빈 객체', 'pending_requests':'전체 PENDING 신청 수',
 'licenses':'라이선스별 현황 배열', 'high_utilization':'사용률 90% 이상 라이선스. 사용률 내림차순', 'recent_requests':'최근 PENDING 신청 최대 5건',
 'q':'라이선스 이름 또는 공급사 검색어', 'status':'업무 상태. 허용값 및 전이 규칙 참조'
}

ERRORS={
 'UNAUTHORIZED':(401,'로그인이 필요합니다.'), 'INVALID_CREDENTIALS':(401,'아이디 또는 비밀번호가 올바르지 않습니다.'),
 'FORBIDDEN':(403,'권한이 없습니다.'), 'NOT_OWNER':(403,'본인의 자원만 처리할 수 있습니다.'),
    'NOT_FOUND':(404,'해당 데이터를 찾을 수 없습니다.'), 'DUPLICATE_USER':(409,'가입 정보 또는 이메일이 중복됩니다.'),
 'INVALID_DEPARTMENT':(422,'부서를 선택해주세요.'), 'VALIDATION_ERROR':(422,'입력값을 확인해주세요.'),
 'LICENSE_INACTIVE':(400,'비활성 라이선스는 신청 또는 승인할 수 없습니다.'), 'INVALID_TRANSITION':(400,'이미 처리된 신청 또는 종료된 할당입니다.'),
 'ALREADY_ASSIGNED':(409,'이미 사용 중인 라이선스입니다.'), 'DUPLICATE_REQUEST':(409,'승인 대기 중인 신청이 있습니다.'),
 'LICENSE_SEAT_FULL':(409,'사용 가능한 라이선스 좌석이 없습니다.'), 'SEATS_BELOW_USAGE':(409,'현재 사용 중인 좌석 수보다 작게 설정할 수 없습니다.'),
 'CONFLICT':(409,'동시에 변경된 데이터 또는 중복 정보가 있습니다. 새로고침 후 확인해주세요.'),
 'INTERNAL_ERROR':(500,'서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.')
}


def operation_errors(method,path):
    public=path in ['/api/departments','/api/auth/signup','/api/auth/login']
    codes=[] if public else ['UNAUTHORIZED']
    if path.startswith('/api/admin/') or 'license-requests' in path or 'license-assignments' in path:
        codes+=['FORBIDDEN']
    if '{' in path or path=='/api/license-requests' and method=='post':
        codes+=['NOT_FOUND']
    if path=='/api/auth/login':codes+=['INVALID_CREDENTIALS']
    if path=='/api/auth/signup' or path=='/api/auth/me' and method=='patch':codes+=['DUPLICATE_USER','INVALID_DEPARTMENT']
    if path=='/api/license-requests' and method=='post':codes+=['LICENSE_INACTIVE','ALREADY_ASSIGNED','DUPLICATE_REQUEST']
    if path.endswith(('/cancel','/return')):codes+=['NOT_OWNER','INVALID_TRANSITION']
    if path.endswith(('/approve','/reject','/revoke')) or path=='/api/admin/license-assignments/{assignment_id}':codes+=['INVALID_TRANSITION']
    if path.endswith('/approve'):codes+=['LICENSE_INACTIVE','ALREADY_ASSIGNED','LICENSE_SEAT_FULL']
    if path=='/api/admin/licenses/{license_id}':codes+=['SEATS_BELOW_USAGE']
    if method!='get' or '{' in path or path.endswith(('/licenses','/history')):codes+=['VALIDATION_ERROR']
    if method!='get' and path!='/api/auth/login':codes+=['CONFLICT']
    codes+=['INTERNAL_ERROR']
    return list(dict.fromkeys(codes))


def schema_name(node):
    if '$ref' in node:return node['$ref'].split('/')[-1]
    if node.get('type')=='array':return schema_name(node['items'])+'[]'
    if 'anyOf' in node:return ' | '.join(schema_name(x) for x in node['anyOf'])
    return node.get('type','object') + (f" ({node['format']})" if 'format' in node else '')


def rules(node):
    bits=[]
    if 'description' in node:bits.append(node['description'])
    if 'enum' in node:bits.append('허용값: '+', '.join(map(str,node['enum'])))
    for k,label in [('minLength','최소 길이'),('maxLength','최대 길이'),('minimum','최솟값'),('maximum','최댓값'),('exclusiveMinimum','초과'),('default','기본값')]:
        if k in node:bits.append(f'{label}: {node[k]}')
    return '; '.join(bits)


def build_api():
    spec=copy.deepcopy(app.openapi())
    spec['components'].pop('securitySchemes',None)
    spec['info'].update(title='LiChU. 사내 SaaS 라이선스 관리 API',version='1.2.0',description='사용 신청 → 관리자 승인·반려 → 할당 → 반납·회수. 실제 구현의 OpenAPI를 기준으로 작성. 제출 지침에 따라 Security Schemes는 제외하며, 실제 보호 API는 Bearer JWT와 역할·소유권 검증을 사용한다. 날짜는 YYYY-MM-DD, 시각은 ISO-8601 UTC. 필드 오류는 422, 잘못된 업무 상태는 400, 동시 충돌·좌석 부족은 409이다.')
    spec['servers']=[{'url':'http://127.0.0.1:8000','description':'기본 로컬 실행 주소 (API Path에 /api 포함)'}]
    schemas=spec['components']['schemas']
    for name,s in schemas.items():
        for key,node in s.get('properties',{}).items():
            if key in FIELD:node['description']=FIELD[key]
        if name in ['RequestInput','AssignmentPeriod']:s['description']='시작일은 종료일 이하. 역전된 기간은 422.'
        if name=='LicensePatch':s['description']='최소 한 필드 필요. 명시적 null은 모두 422. 생략한 필드는 유지.'
        if name=='Signup':s['description']='비밀번호 일치 및 UTF-8 72바이트 이하를 추가 검증. 가입 역할은 USER 고정.'
    common={'id':1,'employee_no':'EMP000001','name':'윤명진','department_id':2,'job_title':'Backend Developer','email':'myeongjin@example.com','username':'myeongjin','password':'ExampleOnly2026!','password_confirm':'ExampleOnly2026!','profile_image':None,'vendor':'GitHub','plan_name':'Business','category':'개발','description':'AI 코드 작성 및 리뷰 지원','total_seats':50,'unit_price':'19.00','used_seats':47,'available_seats':3,'utilization':94.0,'monthly_unit_price':'19.00','request_block':None,'license_id':1,'user_id':2,'request_id':1,'reason':'AI 서비스 개발 프로젝트','start_date':'2026-09-08','end_date':'2026-12-31','valid_from':'2026-09-08','valid_until':'2026-12-31','assigned_by':1,'processed_by':None,'processor':None,'decision_reason':None,'processed_at':None,'canceled_at':None,'ended_by':None,'ended_at':None,'end_reason':None,'access_token':'example.jwt.token','token_type':'bearer','pending_requests':1,'fields':{},'code':'VALIDATION_ERROR','message':'입력값을 확인해주세요.'}
    def example(node,key=''):
        if key in common:return common[key]
        if '$ref' in node:
            name=node['$ref'].split('/')[-1];value=example(schemas[name])
            if name=='UserOut':value.update(id=2)
            if name=='DepartmentOut':value.update(id=2,name='개발팀')
            if name=='LicenseOut':value.update(name='GitHub Copilot')
            return value
        if 'anyOf' in node:return example(next(x for x in node['anyOf'] if x.get('type')!='null'),key)
        if 'enum' in node:return node['enum'][0]
        if 'default' in node:return node['default']
        if node.get('type')=='object':return {k:example(v,k) for k,v in node.get('properties',{}).items()}
        if node.get('type')=='array':return [example(node['items'])]
        if node.get('format')=='date-time':return '2026-09-08T09:00:00Z'
        if node.get('format')=='date':return '2026-09-08'
        if node.get('type') in ['integer','number']:return 1
        if node.get('type')=='boolean':return True
        return 'example'
    endpoints=[]
    for path,ops in spec['paths'].items():
        for method,op in ops.items():
            op.pop('security',None)
            rs=refs_for(method,path)
            assert rs, (method,path)
            reqs=list(dict.fromkeys(r['id'] for r in rs));screens=list(dict.fromkeys(s for r in rs for s in r['screens']))
            db=list(dict.fromkeys(t for r in rs for t in re.findall(r'\b(?:departments|users|licenses|license_requests|license_assignments)\b',r['db'])))
            auth='공개' if path in ['/api/departments','/api/auth/signup','/api/auth/login'] else 'MASTER' if path.startswith('/api/admin/') else 'USER' if 'license-requests' in path or 'license-assignments' in path else 'USER / MASTER'
            op['description']='\n'.join([r['detail'] for r in rs])+f"\n\n요구사항: {', '.join(reqs)}\n화면: {', '.join(screens)}\n테이블: {', '.join(db)}\n접근: {auth}"
            if path=='/api/licenses':op['description']+='\n현재 UI는 전체 목록 로딩 후 검색·분류 필터를 클라이언트에서 적용한다. API q/category도 사용 가능하다.'
            op['x-requirements']=reqs;op['x-screens']=screens;op['x-tables']=db;op['x-access']=auth
            if 'requestBody' in op:
                for media in op['requestBody']['content'].values():media['example']=example(media['schema'])
            for param in op.get('parameters',[]):param['example']=1 if param['in']=='path' else 'GitHub' if param['name']=='q' else '개발' if param['name']=='category' else 'APPROVED'
            op['responses']={k:v for k,v in op['responses'].items() if str(k).startswith('2')}
            for response in op['responses'].values():
                for media in response.get('content',{}).values():
                    value=example(media['schema'])
                    items=value if isinstance(value,list) else [value]
                    for v in items:
                        if not isinstance(v,dict):continue
                        if path.endswith(('/approve','/reject','/history')):
                            v.update(status='REJECTED' if path.endswith('/reject') else 'APPROVED',decision_reason='프로젝트 사용 검토 완료',processed_by=1,processed_at='2026-09-08T09:00:00Z',processor=example({'$ref':'#/components/schemas/UserOut'}))
                            v['processor'].update(id=1,name='LiChU. Master',username='master',role='MASTER')
                        if path.endswith('/cancel'):v.update(status='CANCELED',canceled_at='2026-09-08T09:00:00Z')
                        if path.endswith(('/return','/revoke')):v.update(status='RETURNED' if path.endswith('/return') else 'REVOKED',ended_by=2 if path.endswith('/return') else 1,ended_at='2026-09-08T09:00:00Z',end_reason='사용자 직접 반납' if path.endswith('/return') else '프로젝트 종료')
                    media['example']=value
            for code in operation_errors(method,path):
                status,message=ERRORS[code];key=str(status)
                if key not in op['responses']:op['responses'][key]={'description':'','content':{'application/json':{'schema':{'$ref':'#/components/schemas/ErrorOut'},'examples':{}}}}
                response=op['responses'][key];response['description']+=(' / ' if response['description'] else '')+code+': '+message
                fields={'_form':'필수값·형식·기간을 확인해주세요.'} if status==422 else {}
                response['content']['application/json']['examples'][code]={'summary':code,'value':{'code':code,'message':message,'fields':fields}}
            endpoints.append((method,path,op))
    validate(spec)
    (OUT/(PREFIX+'-API.yml')).write_text(yaml.safe_dump(spec,allow_unicode=True,sort_keys=False,width=120),encoding='utf-8')
    (HERE/'openapi.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
    pages=[page('<div><p style="color:#ba2530">LiChU. 사내 SaaS 라이선스 관리</p><h1>API 명세</h1><p class="muted">API SPECIFICATION</p><div class="cover-meta">'+table(['항목','내용'],[['과정','판교5'],['코드','P157'],['이름','윤명진'],['일자',DATE],['버전',VERSION]])+'</div><p>OpenAPI 3.1 · 엔드포인트 23개</p><p class="muted">신청 · 승인 · 할당 · 반납 · 회수</p></div>','cover','LiChU. API 명세')]
    for offset in range(0,len(endpoints),12):
        rows=[[m.upper(),p,o['summary'],', '.join(o['x-requirements']),', '.join(o['x-screens']),o['x-access']] for m,p,o in endpoints[offset:offset+12]]
        pages.append(page('<h1>API 목록 요약</h1><p>Base URL: http://127.0.0.1:8000 · 총 23개 · '+VERSION+'</p>'+table(['Method','Path','설명','관련 REQ','관련 SCR','접근'],rows,'apiindex')+'<div class="intro">Security Schemes는 제출 지침에 따라 제외했다. 공개 API를 제외한 실제 호출에는 Authorization: Bearer &lt;JWT&gt;가 필요하다. 접근 열은 서버에서 검증하는 역할이다.</div><p>UI 검색·카테고리와 사용자 검색·페이지 이동은 일부 클라이언트 처리이다. 별도의 검색 API, 로그아웃 API, 직접 할당 API, 자동 회수 API를 추가하지 않는다.</p>'))
    for method,path,op in endpoints:
        body='<h1>'+esc(op['summary'])+'</h1><div class="endpoint-title"><span class="method '+method+'">'+method.upper()+'</span>'+esc(path)+'</div>'
        body+='<div class="meta">관련 요구사항: '+esc(', '.join(op['x-requirements']))+'<br>화면: '+esc(', '.join(op['x-screens']))+'<br>테이블: '+esc(', '.join(op['x-tables']))+' · 접근: '+esc(op['x-access'])+'</div>'
        short=' '.join(r['detail'] for r in refs_for(method,path))
        body+='<div class="description">'+esc(short)+'</div>'
        body+='<h2>QUERY · PATH</h2>'
        params=[[p['name'],p['in'],schema_name(p['schema']),'필수' if p.get('required') else '선택',FIELD.get(p['name'],'대상 식별자')+'; '+rules(p['schema'])] for p in op.get('parameters',[])]
        body+=table(['이름','위치','타입','필수','설명'],params) if params else '<p>없음</p>'
        body+='<h2>BODY · application/json</h2>'
        if 'requestBody' in op:
            media=op['requestBody']['content']['application/json'];model=schemas[schema_name(media['schema'])]
            rows=[[k,schema_name(v),'필수' if k in model.get('required',[]) else '선택',rules(v)] for k,v in model['properties'].items()]
            body+=table(['이름','타입','필수','설명 및 규칙'],rows,'reqtable')
            if model.get('description'):body+='<p class="muted">'+esc(model['description'])+'</p>'
        else:body+='<p>요청 본문 없음</p>'
        body+='<h2>응답 · 성공 / 오류</h2>'
        rows=[]
        for code,res in op['responses'].items():
            response_schema=schema_name(res['content']['application/json']['schema'])
            rows.append([code,response_schema,'성공. 상세 필드는 공통 스키마 참조.' if code.startswith('2') else res['description']])
        body+=table(['코드','응답 모델','설명'],rows,'responses')
        pages.append(page(body,'endpoint','LiChU. REST API · 엔드포인트 상세'))
    for name,model in schemas.items():
        if not model.get('properties'):continue
        rows=[[k,schema_name(v),'필수' if k in model.get('required',[]) else '선택',rules(v)] for k,v in model['properties'].items()]
        body='<h1>공통 스키마 · '+esc(name)+'</h1><p>'+esc(model.get('description','요청·응답 필드 정의. 객체형 필드는 같은 이름의 스키마를 참조한다.'))+'</p>'+table(['필드','타입 / 모델','필수','설명 및 제약'],rows,'reqtable')
        body+='<div class="intro">필수 여부는 JSON 키의 존재 조건이다. null 허용 여부는 타입의 null 표기로 구분한다. 날짜는 YYYY-MM-DD, 시각은 ISO-8601 UTC. 입력 모델은 정의되지 않은 필드를 거부한다.</div>'
        if name in ['RequestOut','AssignmentOut','UserOut','LicenseOut','DashboardOut']:body+='<p>password 및 password_hash는 사용자 응답에 포함하지 않는다. used_seats, available_seats 등 집계값과 중첩 사용자·라이선스 객체는 조회 시 조합한다.</p>'
        pages.append(page(body,'schemas endpoint','LiChU. REST API · 공통 스키마'))
    pages.append(page('<h1>공통 오류 및 호출 정책</h1>'+table(['HTTP','code','의미'],[[status,code,msg] for code,(status,msg) in ERRORS.items()])+'<h2>오류 본문 예시</h2><pre>'+esc(json.dumps({'code':'LICENSE_SEAT_FULL','message':'사용 가능한 라이선스 좌석이 없습니다.','fields':{}},ensure_ascii=False,indent=2))+'</pre><p>목록이 비어 있으면 200과 빈 배열을 반환한다. 404는 단일 대상 ID가 없을 때 사용한다. 500 또는 네트워크 실패 후 자동으로 쓰기 요청을 반복하지 않고 현재 상태를 재조회한 뒤 다시 시도한다.</p>'))
    swagger=HERE/'assets/swagger.png'
    pic='<img class="shot" style="height:205mm" src="assets/swagger.png">' if swagger.exists() else '<div class="placeholder">캡처 필요: 제출 API.yml을 Swagger UI에 불러온 뒤 API 목록 및 승인 엔드포인트의 요청·응답을 펼친 화면</div>'
    pages.append(page('<h1>Swagger 렌더링</h1><p>동일한 제출 OpenAPI를 로컬 Swagger UI로 렌더링한 화면.</p>'+pic+'<p class="caption">YAML 원문 화면이 아닌 명세 미리보기. 상세 필드·모든 엔드포인트는 앞쪽 명세 및 YAML에 포함.</p>'))
    if (HERE/'assets/swagger-approve.png').exists():
        pages.append(page('<h1>Swagger · 승인 요청 상세</h1><p>POST /api/admin/license-requests/{request_id}/approve</p><p>REQ-FUNC-012 · SCR-ADM-007 · MASTER</p><img class="shot" style="height:194mm" src="assets/swagger-approve.png"><h2>결과 및 상태</h2><p>200: APPROVED + ACTIVE 할당 생성 / 400: 처리됨·비활성 / 401: 미인증 / 403: 역할 위반 / 404: 대상 없음 / 409: 좌석 부족·기존 할당·충돌 / 422: 사유 검증 / 500: 서버 오류.</p>'))
    document('API',pages)
    return spec


TABLE_INFO={
 'departments':('부서 마스터','REQ-FUNC-001, 020','부서명을 분리하여 사용자별 반복 문자열을 방지한다.'),
 'users':('직원 및 관리자 계정','REQ-FUNC-001, 002, 003, 020','USER와 MASTER를 동일 테이블의 role로 구분한다. 부서 FK, 사번·아이디·이메일 중복 방지.'),
 'licenses':('SaaS 라이선스','REQ-FUNC-004, 010, 015, 016, 017','좌석과 구독 정보를 저장한다. used_seats는 저장하지 않으며 ACTIVE 할당으로 계산한다.'),
 'license_requests':('사용 신청 및 처리 이력','REQ-FUNC-005, 006, 007, 011, 012, 013, 014','신청 목적·예정 기간과 승인·반려·취소 결과를 보존한다. 삭제하지 않는다.'),
 'license_assignments':('사용 권한 할당 및 종료 이력','REQ-FUNC-008, 009, 012, 018, 019, 021','승인 시 생성한다. ACTIVE만 좌석 점유로 집계하며 반납·회수 시 행을 남긴다.')
}


def db_data():
    result=[]
    for name in ['departments','users','licenses','license_requests','license_assignments']:
        t=Base.metadata.tables[name];uniques={tuple(c.name for c in u.columns) for u in t.constraints if isinstance(u,UniqueConstraint)}
        cols=[]
        for c in t.columns:
            flags=[]
            if c.primary_key:flags.append('PK')
            if c.foreign_keys:flags.append('FK')
            if (c.name,) in uniques:flags.append('UQ')
            default='NULL' if c.nullable else '없음 (필수 입력)'
            if c.primary_key:default='자동 증가'
            elif c.default is not None:default='애플리케이션 UTC now()' if c.default.is_callable else str(c.default.arg)+' (앱)'
            desc=FIELD.get(c.name,c.name)
            if c.name=='status':desc={'licenses':'ACTIVE / INACTIVE. 비활성화는 기존 할당을 종료하지 않음','license_requests':'PENDING → APPROVED / REJECTED / CANCELED','license_assignments':'ACTIVE → RETURNED / REVOKED'}[name]
            if c.name=='end_date' and name=='license_requests':desc='사용 종료 예정일. start_date 이상'
            if c.name=='updated_at':desc+='; 수정 시 앱에서 UTC now() 갱신'
            if c.foreign_keys:desc+='; 참조 '+', '.join(fk.target_fullname for fk in c.foreign_keys)
            cols.append({'name':c.name,'type':str(c.type.compile(dialect=postgresql.dialect())).lower().replace('timestamp with time zone','timestamptz'),'keys':flags,'nullable':c.nullable,'default':default,'desc':desc,'refs':[fk.target_fullname for fk in c.foreign_keys]})
        checks=[str(x.sqltext) for x in t.constraints if hasattr(x,'sqltext')]
        indices=[]
        for idx in t.indexes:
            where=idx.dialect_options['postgresql'].get('where')
            indices.append({'name':idx.name,'columns':[c.name for c in idx.columns],'unique':idx.unique,'where':str(where) if where is not None else ''})
        result.append({'name':name,'cols':cols,'checks':sorted(checks),'indices':indices})
    return result


def build_db():
    data=db_data();lines=["Project LiChU {", "  database_type: 'PostgreSQL'", "  Note: '판교5 / P157 / 윤명진; 2026-09-08; v1.2. 실제 SQLAlchemy 모델 기준. 조건부 UNIQUE는 테이블 Note에 기재.'", '}','']
    refs=[]
    for t in data:
        title,req,desc=TABLE_INFO[t['name']];lines.append('Table '+t['name']+' {')
        for c in t['cols']:
            attrs=[]
            if 'PK' in c['keys']:attrs+=['pk','increment']
            if 'UQ' in c['keys']:attrs+=['unique']
            if not c['nullable']:attrs+=['not null']
            attrs+=['note: '+"'"+c['desc'].replace("'","\\'")+"'"]
            typ='"'+c['type']+'"' if ' ' in c['type'] else c['type']
            lines.append('  '+c['name']+' '+typ+' ['+', '.join(attrs)+']')
            for ref in c['refs']:refs.append(f"Ref: {t['name']}.{c['name']} {'-' if 'UQ' in c['keys'] else '>'} {ref}")
        note=title+'; '+req+'; '+desc+'\nCHECK: '+'; '.join(t['checks'])
        for idx in t['indices']:note+='\n'+idx['name']+': UNIQUE('+', '.join(idx['columns'])+') WHERE '+idx['where']
        note+='\nDEFAULT: 모델의 role/status/생성·갱신 시각은 애플리케이션 기본값이며 DB server_default는 없다.'
        lines+=["  Note: '''",note,"'''",'}','']
    lines+=refs
    (OUT/(PREFIX+'-DB.dbml')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (HERE/'db-model.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    pages=[]
    meta=f'<div class="meta">과정: 판교5　 작성자: P157 윤명진　 작성일: {DATE}　 버전: {VERSION}　 기준: PostgreSQL · SQLAlchemy metadata / DBML</div>'
    erd='<img style="width:100%;height:138mm;object-fit:contain" src="assets/erd.png">' if (HERE/'assets/erd.png').exists() else '<div class="placeholder">캡처 필요: DBML의 5개 테이블, PK/FK, 9개 관계선이 모두 보이는 ERD</div>'
    pages.append(page('<h1>[LiChU.] 데이터 모델링 / ERD</h1>'+meta+'<h2>1. 엔티티 관계 다이어그램</h2>'+erd+'<p class="caption">5개 테이블 · 9개 FK. 화살표는 참조 테이블을 가리킨다. 연결 숫자는 다음 페이지 관계 정의와 대응한다. ?는 nullable.</p>','','LiChU. Data Modeling & Table Definition'))
    relrows=[];idx=0
    for t in data:
        for c in t['cols']:
            for ref in c['refs']:
                idx+=1
                relrows.append([str(idx)+' · '+ref,'1 : 0..1' if 'UQ' in c['keys'] else '1 : N',t['name']+'.'+c['name'],('선택 FK. ' if c['nullable'] else '필수 FK. ')+c['desc']])
    pages.append(page('<h1>엔티티 관계 상세 요약</h1>'+meta+table(['부모 PK','카디널리티','자식 FK','규칙 및 참조 무결성'],relrows,'relation-table')+'<h2>정규화 및 삭제 정책</h2><p>사용자와 라이선스의 다대다 관계를 신청 및 할당 테이블로 해소한다. 신청은 업무 요청 이력, 할당은 실제 점유 상태로 분리한다. 1개 신청은 최대 1개 할당에 연결되고, 직접 배정 시연 이력 등을 위해 request_id는 nullable이다. 직접 배정용 API는 제공하지 않는다.</p><p>처리자·승인자·종료자도 users를 참조한다. 외래키에 CASCADE 삭제를 설정하지 않았으며, 신청·할당은 삭제 대신 상태 전이로 보존한다.</p>','','LiChU. Data Modeling & Table Definition'))
    for t in data:
        title,req,desc=TABLE_INFO[t['name']]
        rows=[[' / '.join(c['keys']) or '-',c['name'],c['type'].upper(),'YES' if c['nullable'] else 'NO',c['default'],c['desc']] for c in t['cols']]
        body='<h1>테이블 정의서 · '+t['name'].upper()+'</h1>'+meta+'<h2>'+title+' · '+req+'</h2><p>'+desc+'</p>'+table(['Key','컬럼명','데이터 타입','Nullable','기본값','컬럼 설명 및 비즈니스 규칙'],rows,'dbtable')
        body+='<h2>주요 무결성 제약조건 및 인덱스</h2><p>'+esc('; '.join(t['checks']) or 'PRIMARY KEY(id), UNIQUE(name)')+'</p>'
        for ix in t['indices']:body+='<p class="mono">'+esc(ix['name']+': UNIQUE ('+', '.join(ix['columns'])+') WHERE '+ix['where'])+'</p>'
        body+='<p class="muted">조건부 UNIQUE는 PostgreSQL 부분 인덱스로 적용하며 DBML Note에 함께 기재한다. 앱 기본값은 DB DEFAULT와 구분한다.</p>'
        pages.append(page(body,'','LiChU. Data Modeling & Table Definition'))
    pages.append(page('<h1>상태 전이 · 집계 · UI 필드 매핑</h1>'+meta+table(['대상','허용 전이','처리 규칙'],[
        ['신청','PENDING → APPROVED','MASTER 승인 + ACTIVE 할당 생성. 같은 트랜잭션. 기존 할당 또는 잔여 0석이면 409.'],
        ['신청','PENDING → REJECTED','MASTER 반려. 사유·처리자·시각 저장. 할당 없음.'],
        ['신청','PENDING → CANCELED','본인 취소. canceled_at 저장. 타인 건은 403.'],
        ['할당','ACTIVE → RETURNED / REVOKED','반납 / 회수자·시각·사유 기록. 종료된 건의 재처리는 400.'],
        ['라이선스','ACTIVE ↔ INACTIVE','비활성화는 신규 신청·승인을 차단. 기존 할당을 자동 종료하지 않음.']])+'<h2>화면 표시값의 출처</h2>'+table(['UI 필드','DB 또는 계산식','화면'],[
        ['부서 / 직원 정보','users.department_id → departments.id; users.name/job_title/email/profile_image','SCR-COMMON-001, 002 / SCR-ADM-006'],
        ['사용 / 잔여 / 사용률','COUNT(ACTIVE assignment); total_seats - COUNT; COUNT / total_seats × 100','SCR-LIC-001 / SCR-ADM-001, 003'],
        ['승인 / 반려 결과','license_requests.status/decision_reason/processed_by/processed_at','SCR-REQ-001 / SCR-ADM-004'],
        ['권한 승인 기간 / 목적','license_assignments.valid_from/valid_until; request_id → license_requests.reason','SCR-MYLIC-001 / SCR-ADM-006, 010'],
        ['월 환산 단가','MONTHLY: unit_price / YEARLY: unit_price ÷ 12','SCR-LIC-001 / SCR-ADM-003']])+'<h2>정합성 정책</h2><p>신청 승인·반납·회수·좌석 변경 시 licenses 행을 먼저 잠그고 상태를 재검증한다. 사용량 집계의 단일 기준은 ACTIVE 할당이다. 비활성 라이선스도 대시보드 전체 좌석 합계에 포함한다. 승인 기간은 표시·관리 정보이며 종료일 자동 회수 또는 예약 시작일 지연 할당은 구현 범위가 아니다.</p>','','LiChU. Data Modeling & Table Definition'))
    document('DB',pages,True)
    return data


if __name__=='__main__':
    build_api()
    build_db()
    print('Generated API/DB sources and HTML; requirement definition unchanged.')
