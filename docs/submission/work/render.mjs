import {createRequire} from 'node:module'
import {dirname,resolve} from 'node:path'
import {fileURLToPath,pathToFileURL} from 'node:url'
import {readFile,writeFile,mkdir} from 'node:fs/promises'
import {createServer} from 'node:http'
const here=dirname(fileURLToPath(import.meta.url)),root=resolve(here,'../../..')
const require=createRequire(resolve(root,'frontend/package.json'))
const runtime=createRequire(resolve(here,'runtime/package.json'))
const {chromium}=require('@playwright/test')
const {Parser}=runtime('@dbml/core')
const {instance}=runtime('@viz-js/viz')
const prefix='판교5-P157-윤명진', out=resolve(here,'..',prefix)
const mode=process.argv[2]||'visuals'
const browser=await chromium.launch({headless:true,channel:'msedge'})
const page=await browser.newPage({viewport:{width:1600,height:1100},deviceScaleFactor:2})
page.on('pageerror',e=>console.log('Browser error: '+e.message))
page.on('console',m=>{if(m.type()==='error')console.log('Browser console: '+m.text())})
let server
const escape=(s)=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;')
await mkdir(resolve(here,'assets'),{recursive:true})
try{
 if(mode==='visuals'){
  const dbml=await readFile(resolve(out,prefix+'-DB.dbml'),'utf8')
  const parsed=Parser.parse(dbml,'dbml');console.log('DBML parsed: '+parsed.schemas[0].tables.length+' tables')
  const data=JSON.parse(await readFile(resolve(here,'db-model.json'),'utf8'))
  const viz=await instance()
  const colors=['#446a9f','#655091','#0c7a83','#a73549','#287d57']
  let dot='digraph ERD { graph [rankdir=LR, bgcolor="white", nodesep=0.55, ranksep=0.72, pad=0.2, splines=true]; node [shape=plain, fontname="Malgun Gothic"]; edge [fontname="Malgun Gothic", fontsize=10, arrowsize=0.6, color="#657d9d"]; '
  for(let i=0;i<data.length;i++){
   const t=data[i]
   dot+=`${t.name} [label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="6" COLOR="#cbd3e0"><TR><TD COLSPAN="3" BGCOLOR="${colors[i]}"><FONT COLOR="white" POINT-SIZE="15"><B>${t.name}</B></FONT></TD></TR>`
   for(const c of t.cols)dot+=`<TR><TD WIDTH="48" BGCOLOR="#f1f3f8"><FONT POINT-SIZE="10">${escape(c.keys.join('/')||'-')}</FONT></TD><TD WIDTH="165" PORT="${c.name}" ALIGN="LEFT"><FONT POINT-SIZE="12">${escape(c.name)}</FONT></TD><TD WIDTH="135" ALIGN="LEFT"><FONT POINT-SIZE="10" COLOR="#687585">${escape(c.type)}${c.nullable?' ?':''}</FONT></TD></TR>`
   dot+='</TABLE>>];'
  }
  dot+='{rank=same; users;licenses;}'
  let n=0
  for(const t of data)for(const c of t.cols)for(const ref of c.refs){n++;const [p]=ref.split('.');dot+=`${t.name} -> ${p} [label="${n}", constraint=false, color="${['#627fbe','#9070a7','#39828b'][n%3]}"];`}
  dot+='departments -> users [style=invis]; users -> license_requests [style=invis]; licenses -> license_requests [style=invis]; license_requests -> license_assignments [style=invis];}'
  const svg=viz.renderString(dot,{format:'svg',engine:'dot'})
  await writeFile(resolve(here,'assets/erd.svg'),svg)
  await page.setContent('<html><body style="margin:0;background:white">'+svg+'</body></html>')
  await page.locator('svg').screenshot({path:resolve(here,'assets/erd.png')})
  const flow=`digraph FLOW { graph [rankdir=TB,bgcolor="white",pad=0.3,nodesep=0.4,ranksep=0.55];node [shape=box,style="rounded,filled",fillcolor="#f3f5f8",color="#bdc7d6",fontname="Malgun Gothic",fontsize=12,margin="0.15,0.12"];edge [fontname="Malgun Gothic",fontsize=10,color="#687b98"];
   login[label="로그인\\nSCR-AUTH-001"]; signup[label="회원가입\\nSCR-SIGNUP-001"]; profile[label="공통 메뉴 / 회원 정보 수정\\nSCR-COMMON-001 / 002"];
   subgraph cluster_user {label="USER · 임직원";fontname="Malgun Gothic";color="#c4d9cc";catalog[label="라이선스 탐색\\nSCR-LIC-001",fillcolor="#e8f3ed"];request[label="사용 신청\\nSCR-LIC-002"];myreq[label="내 신청\\nSCR-REQ-001"];cancel[label="신청 취소\\nSCR-REQ-002"];mylic[label="내 라이선스\\nSCR-MYLIC-001"];ret[label="반납\\nSCR-MYLIC-002"];
   catalog->request->myreq;myreq->cancel[label="PENDING"];mylic->ret;}
   subgraph cluster_admin {label="MASTER · 관리자";fontname="Malgun Gothic";color="#c5d1e3";dash[label="대시보드\\nSCR-ADM-001",fillcolor="#e8eef9"];pending[label="승인 대기\\nSCR-ADM-002"];approve[label="승인 / 반려\\nSCR-ADM-007 / 008"];history[label="처리 이력\\nSCR-ADM-004"];manage[label="라이선스 관리\\nSCR-ADM-003"];edit[label="등록 / 수정\\nSCR-ADM-005"];users[label="사용자 관리\\nSCR-ADM-006"];period[label="승인 기간 수정 / 회수\\nSCR-ADM-010 / 009"];
   dash->pending->approve->history;dash->manage;manage->edit;manage->users->period;}
   signup->login[label="201"];login->catalog[label="USER"];login->dash[label="MASTER"];login->profile[style=dashed];login->login[label="401: 오류 안내"];
   myreq->pending[style=dashed,label="PENDING 신청"];approve->mylic[style=dashed,label="승인 + ACTIVE 할당"];history->myreq[style=dashed,label="결과 / 사유 확인",constraint=false];request->request[label="400/409/422: 입력 유지"];approve->approve[label="400/409/422: 재확인"];ret->catalog[style=dashed,label="잔여 좌석 반영",constraint=false];
  }`
  const fsvg=viz.renderString(flow,{format:'svg',engine:'dot'})
  await writeFile(resolve(here,'assets/ui-flow.svg'),fsvg)
  await page.setContent('<html><body style="margin:0;background:white">'+fsvg+'</body></html>');await page.locator('svg').screenshot({path:resolve(here,'assets/ui-flow.png')})
  const swaggerRoot=dirname(runtime.resolve('swagger-ui-dist/package.json'))
  const spec=JSON.parse(await readFile(resolve(here,'openapi.json'),'utf8'))
  await page.setViewportSize({width:1100,height:1200})
  server=createServer((req,res)=>{res.setHeader('Content-Type','text/html; charset=utf-8');res.end('<html lang="ko"><head><meta charset="utf-8"></head><body style="margin:0;background:white"><div id="swagger"></div></body></html>')})
  await new Promise(done=>server.listen(0,'127.0.0.1',done))
  await page.goto('http://127.0.0.1:'+server.address().port)
  await page.addStyleTag({path:resolve(swaggerRoot,'swagger-ui.css')})
  await page.addScriptTag({path:resolve(swaggerRoot,'swagger-ui-bundle.js')})
  await page.evaluate((spec)=>{window.ui=SwaggerUIBundle({spec,dom_id:'#swagger',deepLinking:false,docExpansion:'list',defaultModelsExpandDepth:-1,tryItOutEnabled:false,supportedSubmitMethods:[],validatorUrl:null})},spec)
  await page.locator('.opblock').first().waitFor();await page.evaluate(()=>document.fonts.ready)
  await page.locator('.swagger-ui').screenshot({path:resolve(here,'assets/swagger.png')})
  const approvalSpec={...spec,paths:{'/api/admin/license-requests/{request_id}/approve':spec.paths['/api/admin/license-requests/{request_id}/approve']}}
  await page.evaluate((spec)=>{document.querySelector('#swagger').innerHTML='';window.ui=SwaggerUIBundle({spec,dom_id:'#swagger',deepLinking:false,docExpansion:'full',defaultModelsExpandDepth:-1,defaultModelRendering:'model',supportedSubmitMethods:[],validatorUrl:null})},approvalSpec)
  await page.locator('.responses-wrapper .response').first().waitFor()
  await page.evaluate(()=>document.fonts.ready)
  const operation=await page.locator('.opblock').boundingBox(), responses=await page.locator('.responses-wrapper').boundingBox(), scroll=await page.evaluate(()=>window.scrollY)
  await page.screenshot({path:resolve(here,'assets/swagger-approve.png'),clip:{x:operation.x,y:operation.y+scroll,width:operation.width,height:responses.y-operation.y}})
  console.log('ERD, UI flow, Swagger images generated.')
 }else{
  const reports=[]
  for(const name of ['화면설계서','API','DB']){
   await page.goto(pathToFileURL(resolve(here,name+'.html')).href,{waitUntil:'networkidle'})
   await page.evaluate(()=>Promise.all([document.fonts.ready,...[...document.images].map(i=>i.decode())]))
   const report=await page.evaluate(()=>{
    return [...document.querySelectorAll('.page')].map((p,i)=>{
     const footer=p.querySelector('.foot').getBoundingClientRect(),bounds=p.getBoundingClientRect()
     const elements=[...p.querySelectorAll('p,td,th,h1,h2,h3,img,pre,.meta,.flow,.intro,.placeholder')].filter(e=>!e.closest('.running,.foot'))
     const bottom=Math.max(...elements.map(e=>e.getBoundingClientRect().bottom))
     const horizontal=elements.filter(e=>{const r=e.getBoundingClientRect();return r.right>bounds.right-4||r.left<bounds.left-1}).map(e=>e.tagName+': '+e.textContent.slice(0,80))
     return {page:i+1,title:p.querySelector('h1')?.textContent,bottom:Math.round(bottom-bounds.top),limit:Math.round(footer.top-bounds.top-8),overflow:Math.max(0,Math.ceil(bottom-footer.top+8)),horizontal}
    })
   })
   reports.push({name,pages:report})
   const bad=report.filter(x=>x.overflow||x.horizontal.length);console.log(name+': '+report.length+' pages; overflow='+JSON.stringify(bad))
   await page.pdf({path:resolve(out,prefix+'-'+name+'.pdf'),printBackground:true,preferCSSPageSize:true,tagged:true})
  }
  await writeFile(resolve(here,'layout-check.json'),JSON.stringify(reports,null,2))
 }
}finally{await browser.close();if(server)await new Promise(done=>server.close(done))}
