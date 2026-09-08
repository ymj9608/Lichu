"""Inspect generated PDFs for counts, searchable text, images, and page boundaries."""
import json
import re
from pathlib import Path
import pymupdf

HERE=Path(__file__).resolve().parent
PREFIX='판교5-P157-윤명진'
OUT=HERE.parent/PREFIX
REVIEW=HERE/'review'
REVIEW.mkdir(exist_ok=True)
result=[]
for name,selected in [('화면설계서',[0,2,3,12,13,32,42]),('API',[0,1,4,18,29,43]),('DB',[0,1,3,5,6])]:
    pdf=pymupdf.open(OUT/(PREFIX+'-'+name+'.pdf'))
    texts=[p.get_text() for p in pdf]
    issues=[]
    for i,p in enumerate(pdf):
        if len(texts[i].strip())<40:issues.append(f'page {i+1}: unexpectedly little text')
        if '\ufffd' in texts[i]:issues.append(f'page {i+1}: replacement character')
        if '캡처 필요:' in texts[i]:issues.append(f'page {i+1}: placeholder')
        for block in p.get_text('dict')['blocks']:
            if block['type']!=0:continue
            for line in block['lines']:
                for span in line['spans']:
                    x0,y0,x1,y1=span['bbox']
                    if x0 < -1 or y0 < -1 or x1>p.rect.width+1 or y1>p.rect.height+1:
                        issues.append(f'page {i+1}: text outside page: '+span['text'])
    for i in selected:
        if i<len(pdf):pdf[i].get_pixmap(matrix=pymupdf.Matrix(1.35,1.35)).save(REVIEW/(name+'-'+str(i+1)+'.png'))
    record={'name':name,'pages':len(pdf),'bytes':(OUT/(PREFIX+'-'+name+'.pdf')).stat().st_size,'embedded_images':sum(len(p.get_images()) for p in pdf),'issues':issues}
    if name=='화면설계서':record['screen_ids']=sorted(set(re.findall(r'SCR-[A-Z]+-\d{3}','\n'.join(texts))))
    result.append(record)
(HERE/'pdf-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
