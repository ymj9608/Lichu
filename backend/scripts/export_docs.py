"""Generate submission artifacts from live schemas and project-overview.md."""
import copy
import html
import os
from pathlib import Path
import re
import yaml
import markdown
from sqlalchemy import UniqueConstraint
from app.main import app
from app.models.entities import Base

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / 'docs'
PREFIX = f"{os.getenv('SUBMISSION_CLASS', 'CLASS')}_{os.getenv('SUBMISSION_NAME', 'NAME')}_Lichu"


def export_api():
    schema = copy.deepcopy(app.openapi())
    schema['components'].pop('securitySchemes', None)
    schema['info']['description'] += '\n제출용 문서에서 Security Schemes만 제외했습니다. 실제 앱은 Bearer JWT 인증을 요구합니다.'
    components = schema['components']['schemas']
    common = {'id':1, 'user_id':2, 'license_id':1, 'request_id':1, 'department_id':1, 'assigned_by':1,
        'employee_no':'EMP000001', 'name':'윤명진', 'job_title':'Backend Developer', 'email':'myeongjin@example.com',
        'username':'myeongjin', 'password':'LichuDemo2026!', 'password_confirm':'LichuDemo2026!',
        'profile_image':None, 'valid_from':'2026-09-08', 'valid_until':'2026-12-31',
        'reason':'AI 서비스 개발 프로젝트에 사용', 'decision_reason':'프로젝트 기간 사용 승인',
        'start_date':'2026-09-08', 'end_date':'2026-12-31', 'vendor':'GitHub', 'plan_name':'Business',
        'category':'개발', 'description':'코드 개발과 리뷰 지원', 'unit_price':'19.00', 'monthly_unit_price':'19.00',
        'total_seats':50, 'used_seats':47, 'available_seats':3, 'utilization':94, 'request_block':None,
        'code':'LICENSE_SEAT_FULL', 'message':'사용 가능한 라이선스 좌석이 없습니다.'}
    def example(node, depth=0, key=''):
        if depth > 30:
            return None
        if '$ref' in node:
            name = node['$ref'].split('/')[-1]
            value = example(components[name], depth+1)
            if name == 'UserOut':
                value['id'] = 2
            if name == 'LicenseOut':
                value['name'] = 'GitHub Copilot'
            if name == 'DepartmentOut':
                value['name'] = '개발팀'
            if name == 'RequestOut':
                value.update(status='PENDING', decision_reason=None, processed_by=None, processor=None, processed_at=None, canceled_at=None)
            if name == 'AssignmentOut':
                value.update(status='ACTIVE', ended_by=None, ended_at=None, end_reason=None)
            if name == 'DashboardOut':
                value.update(total_seats=50,used_seats=47,available_seats=3,pending_requests=1)
            return value
        if key in common:
            return common[key]
        if 'anyOf' in node:
            return example(next((x for x in node['anyOf'] if x.get('type') != 'null'), node['anyOf'][0]), depth+1, key)
        if 'enum' in node:
            return node['enum'][0]
        if node.get('type') == 'object':
            return {k:example(v,depth+1,k) for k,v in node.get('properties',{}).items()}
        if node.get('type') == 'array':
            return [example(node['items'],depth+1)]
        if node.get('format') == 'date-time':
            return '2026-09-08T09:00:00Z'
        if node.get('format') == 'date':
            return '2026-09-08'
        if node.get('type') in ['integer','number']:
            return 1
        if node.get('type') == 'boolean':
            return True
        return 'example'
    for path, operations in schema['paths'].items():
        for method, operation in operations.items():
            operation.pop('security',None)
            for parameter in operation.get('parameters',[]):
                parameter['example'] = 1 if parameter['in']=='path' else ('GitHub' if parameter['name']=='q' else '개발' if parameter['name']=='category' else 'APPROVED')
            if 'requestBody' in operation:
                for media in operation['requestBody']['content'].values():
                    media['example'] = example(media['schema'])
            operation['responses']['500'] = {'description':'예상하지 못한 서버 오류', 'content':{'application/json':{
                'schema':{'$ref':'#/components/schemas/ErrorOut'}, 'example':{'code':'INTERNAL_ERROR','message':'서버 오류가 발생했습니다.','fields':{}}}}}
            for status, response in operation['responses'].items():
                for media in response.get('content',{}).values():
                    if 'example' not in media:
                        media['example'] = example(media['schema'])
                    if status.startswith('2'):
                        samples = media['example'] if isinstance(media['example'], list) else [media['example']]
                        for sample in samples:
                            if path.endswith(('/approve','/reject','/history')):
                                sample.update(status='REJECTED' if path.endswith('/reject') else 'APPROVED',
                                    decision_reason='프로젝트 사용 검토 완료',processed_by=1,
                                    processed_at='2026-09-08T09:00:00Z')
                                sample['processor'] = example({'$ref':'#/components/schemas/UserOut'})
                                sample['processor'].update(id=1,name='LiChU. Master',username='master',role='MASTER')
                            elif path.endswith('/cancel'):
                                sample.update(status='CANCELED',canceled_at='2026-09-08T09:00:00Z')
                            elif path.endswith(('/return','/revoke')):
                                sample.update(status='RETURNED' if path.endswith('/return') else 'REVOKED',
                                    ended_by=2 if path.endswith('/return') else 1,
                                    ended_at='2026-09-08T09:00:00Z',end_reason='프로젝트 종료')
    (DOCS / f'{PREFIX}-API.yml').write_text(yaml.safe_dump(schema,allow_unicode=True,sort_keys=False),encoding='utf-8')


def export_dbml():
    result = ['// Generated from SQLAlchemy metadata. Partial unique indexes documented below.']
    refs = []
    for table in Base.metadata.sorted_tables:
        result.append(f'Table {table.name} {{')
        unique_columns = {tuple(c.name for c in constraint.columns) for constraint in table.constraints if isinstance(constraint,UniqueConstraint)}
        for col in table.columns:
            attrs = []
            if col.primary_key:
                attrs.extend(['pk','increment'])
            if not col.nullable:
                attrs.append('not null')
            if col.unique or (col.name,) in unique_columns:
                attrs.append('unique')
            typ = str(col.type).lower().replace('datetime','timestamptz')
            if getattr(col.type,'timezone',False):
                typ = 'timestamptz'
            if ' ' in typ:
                typ = f'"{typ}"'
            result.append(f'  {col.name} {typ}' + (f" [{', '.join(attrs)}]" if attrs else ''))
            for fk in col.foreign_keys:
                relation = '-' if col.name == 'request_id' else '>'
                refs.append(f'Ref: {table.name}.{col.name} {relation} {fk.target_fullname}')
        notes = []
        for constraint in table.constraints:
            if hasattr(constraint,'sqltext'):
                notes.append(str(constraint.sqltext))
        for idx in table.indexes:
            if idx.unique:
                notes.append(f"{idx.name}: UNIQUE({', '.join(c.name for c in idx.columns)}) WHERE {idx.dialect_options['postgresql'].get('where')}")
        if notes:
            result.append("  Note: '''\n" + '; '.join(sorted(notes)) + "\n'''")
        result.append('}\n')
    (DOCS / f'{PREFIX}-DB.dbml').write_text('\n'.join(result + refs) + '\n',encoding='utf-8')


def flow_svg():
    flows = [('EMPLOYEE', ['Login','License Catalog','Request','My Requests','Approval / Rejection','My License','Return']),
             ('ADMIN', ['Login','Dashboard','Pending Request','Approve / Reject','License Management','Active User','Revoke'])]
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 980 205" role="img" aria-label="직원 및 관리자 UI 흐름도"><defs><marker id="arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="#b89955"/></marker></defs>']
    for row,(label,steps) in enumerate(flows):
        y=38+row*98
        out.append(f'<text x="5" y="{y-14}" font-family="sans-serif" font-size="11" fill="#a17e32">{label}</text>')
        for i,step in enumerate(steps):
            x=5+i*139
            out.append(f'<rect x="{x}" y="{y}" width="126" height="44" rx="7" fill="#fff8e5" stroke="#e0cfa7"/><text x="{x+63}" y="{y+26}" text-anchor="middle" font-size="10" font-family="sans-serif" fill="#4d422d">{step}</text>')
            if i<6:
                out.append(f'<path d="M{x+126},{y+22} H{x+137}" stroke="#b89955" marker-end="url(#arrow)"/>')
    return ''.join(out)+'</svg>'


def export_html():
    source=(DOCS/'project-overview.md').read_text()
    source=re.sub(r'```mermaid.*?```',flow_svg(),source,flags=re.S)
    body=markdown.markdown(source,extensions=['tables','fenced_code'])
    screenshots=[('login','로그인'),('catalog','라이선스 탐색'),('my-requests','내 신청'),('admin-dashboard','관리자 대시보드'),('admin-requests','관리자 신청 관리'),('admin-license-users','라이선스 사용자 관리')]
    body+='<h2>핵심 화면</h2>'
    for file,title in screenshots:
        body+=f'<figure><figcaption>{html.escape(title)}</figcaption><img src="screenshots/{file}.png" alt="{html.escape(title)} 화면"></figure>'
    css='''html,body{background:#fff}body{font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;color:#26221d;line-height:1.85;max-width:1000px;margin:50px auto;padding:0 30px;font-size:14px}h1{font-size:32px;border-bottom:4px solid #f5b82e;padding-bottom:20px}h2{font-size:20px;margin-top:32px;break-after:avoid}p{margin:12px 0}svg{width:100%;height:auto}figure{margin:30px 0;break-inside:avoid}figcaption{font-weight:700;margin-bottom:10px}img{width:100%;border:1px solid #eee;border-radius:8px}.print-button{position:fixed;right:20px;top:20px;border:0;background:#f5b82e;padding:12px;border-radius:7px;cursor:pointer}@page{size:A4;margin:17mm 15mm}@media print{body{font-size:10pt;margin:0;padding:0;max-width:none}h1{font-size:25pt}h2{font-size:14pt}.print-button{display:none}figure{break-before:page}p{orphans:3;widows:3}*{-webkit-print-color-adjust:exact;print-color-adjust:exact}}'''
    (DOCS/'project-overview.html').write_text(f'<!doctype html><html lang="ko"><head><meta charset="UTF-8"><title>LiChU. 프로젝트 기술서</title><style>{css}</style></head><body><button class="print-button" onclick="window.print()">PDF로 저장</button>{body}</body></html>',encoding='utf-8')


if __name__=='__main__':
    export_api()
    export_dbml()
    export_html()
    print(f'Exported {PREFIX}-API.yml / DB.dbml and project-overview.html')
