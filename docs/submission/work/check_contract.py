"""Validate document coverage and request/response examples against actual code."""
import json
from pathlib import Path
from pydantic import TypeAdapter
import yaml
import capture_server
from app.main import app
from app.api.routes import router
from app.schemas import dto
from app.models.entities import Base
from openapi_spec_validator import validate
from screen_specs import SPECS

HERE=Path(__file__).resolve().parent
PREFIX='판교5-P157-윤명진'
OUT=HERE.parent/PREFIX
spec=yaml.safe_load((OUT/(PREFIX+'-API.yml')).read_text(encoding='utf-8'))
validate(spec)
assert 'securitySchemes' not in spec['components']
operations={(m.upper(),p):o for p,ops in spec['paths'].items() for m,o in ops.items()}
routes={(m,r.path):r for r in router.routes if hasattr(r,'response_model') for m in r.methods}
assert operations.keys()==routes.keys(), (operations.keys()-routes.keys(),routes.keys()-operations.keys())
examples=0
for key,op in operations.items():
    assert op['x-requirements'] and op['x-screens'] and op['x-tables']
    assert set(op['x-screens'])<=set(SPECS)
    if 'requestBody' in op:
        media=op['requestBody']['content']['application/json']
        name=media['schema']['$ref'].rsplit('/',1)[1]
        TypeAdapter(getattr(dto,name)).validate_python(media['example'])
        examples+=1
    for status,response in op['responses'].items():
        for media in response.get('content',{}).values():
            if status.startswith('2'):
                TypeAdapter(routes[key].response_model).validate_python(media['example'])
                examples+=1
            else:
                for value in media['examples'].values():
                    dto.ErrorOut.model_validate(value['value']);examples+=1
    assert '500' in op['responses']
for name,schema in spec['components']['schemas'].items():
    if name.endswith('Out'):assert not ({'password','password_hash'}&schema.get('properties',{}).keys())
data=json.loads((HERE/'db-model.json').read_text(encoding='utf-8'))
assert len(data)==len(Base.metadata.tables)==5
assert all(set(c['name'] for c in t['cols'])==set(Base.metadata.tables[t['name']].columns.keys()) for t in data)
captures=json.loads((HERE/'captures.json').read_text(encoding='utf-8'))
assert set(SPECS)<=set(captures)
assert all(captures[sid]['markers']==len(s['rows']) for sid,s in SPECS.items())
html_api=(HERE/'API.html').read_text(encoding='utf-8')
for (method,path) in operations:
    import html
    assert html.escape(path) in html_api
files=sorted(p.name for p in OUT.iterdir() if p.is_file())
assert len(files)==5,files
report={'operations':len(operations),'validated_examples':examples,'tables':len(data),'columns':sum(len(t['cols']) for t in data),'foreign_keys':sum(len(c['refs']) for t in data for c in t['cols']),'screens':len(SPECS),'captures':len(captures),'submission_files':files,'requirements_definition':'unchanged','result':'PASS'}
(HERE/'contract-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=True,indent=2))
