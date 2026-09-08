import {createRequire} from 'node:module'
import {fileURLToPath} from 'node:url'
import {dirname,resolve} from 'node:path'
import {mkdir,writeFile} from 'node:fs/promises'
const here=dirname(fileURLToPath(import.meta.url)), root=resolve(here,'../../..')
const require=createRequire(resolve(root,'frontend/package.json'))
const {chromium}=require('@playwright/test')
const browser=await chromium.launch({headless:true,channel:'msedge'})
const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1.5})
const out=resolve(here,'assets');await mkdir(out,{recursive:true})
const records={};const base='http://127.0.0.1:5175'
const btn=(name)=>page.getByRole('button',{name,exact:true})
const label=(name)=>page.getByLabel(name,{exact:true})
async function go(path){await page.goto(base+path);await page.waitForLoadState('networkidle')}
async function shot(id,locators=[],modal=false){
  await page.evaluate(()=>document.fonts.ready)
  const target=modal?page.getByRole('dialog'):page.locator('body')
  await target.waitFor()
  for(let i=0;i<locators.length;i++){
    const loc=locators[i].first();await loc.waitFor({state:'visible'})
    await loc.evaluate((el,num)=>{
      const r=el.getBoundingClientRect(),b=document.createElement('span');b.className='doc-marker';b.textContent=num
      Object.assign(b.style,{position:'absolute',left:`${r.left+window.scrollX+3}px`,top:`${r.top+window.scrollY+2}px`,width:'23px',height:'23px',background:'#ba2530',color:'#fff',border:'2px solid #fff',borderRadius:'50%',font:'bold 13px Arial',display:'grid',placeItems:'center',zIndex:100000,pointerEvents:'none'})
      // Keep markers inside the dialog screenshot while preserving page coordinates.
      const dialog=el.closest('[role=dialog]');if(dialog){const dr=dialog.getBoundingClientRect();b.style.left=`${r.left-dr.left+3}px`;b.style.top=`${r.top-dr.top+2}px`;dialog.style.position='relative';dialog.append(b)}else document.body.append(b)
    },String(i+1))
  }
  await target.screenshot({path:resolve(out,id+'.png'),animations:'disabled'})
  records[id]={file:id+'.png',markers:locators.length,source:'실행 화면',viewport:'1440 × 1000',demo:true}
  await page.locator('.doc-marker').evaluateAll(els=>els.forEach(e=>e.remove()))
  console.log('Captured '+id)
}
async function login(user,password){await go('/login');await label('아이디').fill(user);await label('비밀번호').fill(password);await btn('로그인').click();await page.waitForURL(user==='master'?'**/admin':'**/licenses');await page.waitForLoadState('networkidle')}
async function close(){await page.getByRole('dialog').getByRole('button',{name:'닫기',exact:true}).first().click()}
try{
 await go('/login');await shot('SCR-AUTH-001',[label('아이디'),label('비밀번호'),page.locator('.login-options'),btn('로그인'),page.locator('.auth-tabs')])
 await go('/signup');await shot('SCR-SIGNUP-001',[page.locator('.profile-upload'),page.locator('.form-grid'),btn('회원가입'),page.locator('.auth-tabs')])
 await login('myeongjin','CaptureEmployee2026!')
 await shot('SCR-COMMON-001',[page.locator('.brand'),page.locator('.sidebar nav'),btn('회원 정보 수정'),btn('로그아웃')])
 await shot('SCR-LIC-001',[page.locator('.category-tabs'),label('라이선스 검색'),page.locator('.license-card').filter({hasText:'IntelliJ'}),btn('새로고침')])
 await btn('회원 정보 수정').click();await shot('SCR-COMMON-002',[page.locator('.profile-upload'),page.locator('.profile-fixed'),page.locator('[role=dialog] .form-grid'),btn('저장')],true);await close()
 await page.locator('.license-card').filter({hasText:'IntelliJ'}).getByRole('button').click()
 await page.locator('textarea').fill('AI 서비스 백엔드 개발 및 코드 품질 검토');await label('사용 종료 예정일').fill('2026-12-31')
 await shot('SCR-LIC-002',[page.locator('.modal-summary'),page.locator('textarea'),label('사용 시작 예정일'),label('사용 종료 예정일'),btn('신청하기')],true);await close()
 await go('/requests');await shot('SCR-REQ-001',[page.locator('.table-container'),page.locator('.decision-box.rejected'),btn('신청 취소'),btn('새로고침')])
 await btn('신청 취소').click();await shot('SCR-REQ-002',[page.locator('.modal-summary'),page.locator('[role=dialog] .notice'),page.locator('[role=dialog] .modal-actions')],true);await close()
 await go('/my-licenses');await shot('SCR-MYLIC-001',[page.locator('.my-license').first(),page.locator('.my-license dl').first(),btn('반납').first(),page.locator('.heading-actions')])
 await btn('반납').first().click();await shot('SCR-MYLIC-002',[page.locator('.modal-summary'),page.locator('[role=dialog] .notice'),btn('반납 확인')],true);await close()
 await btn('로그아웃').click();await login('master','CaptureMaster2026!')
 await shot('SCR-ADM-001',[page.locator('.stats-grid'),page.locator('.dashboard-columns'),btn('새로고침')])
 await go('/admin/requests');await shot('SCR-ADM-002',[page.locator('.category-tabs'),page.locator('.table-container'),btn('승인').first(),btn('반려').first()])
 await btn('승인').first().click();await page.locator('textarea').fill('프로젝트 수행 기간 동안 사용을 승인합니다.');await shot('SCR-ADM-007',[page.locator('.modal-summary'),page.locator('textarea'),btn('승인 확정')],true);await close()
 await btn('반려').first().click();await page.locator('textarea').fill('프로젝트 범위와 사용 목적을 보완한 뒤 재신청 바랍니다.');await shot('SCR-ADM-008',[page.locator('.modal-summary'),page.locator('textarea'),btn('반려 확정')],true);await close()
 await btn('처리 이력').click();await page.waitForLoadState('networkidle');await shot('SCR-ADM-004',[page.locator('.category-tabs'),label('처리 결과 필터'),page.locator('.table-container'),page.locator('.pagination')])
 await go('/admin/licenses');await shot('SCR-ADM-003',[page.locator('.catalog-toolbar'),btn('라이선스 등록'),page.locator('.license-card').first(),btn('GitHub Copilot 수정')])
 await btn('GitHub Copilot 수정').click();await shot('SCR-ADM-005',[page.locator('.form-grid'),page.locator('.form-hint'),btn('저장')],true);await close()
 await btn('라이선스 등록').click();await shot('SCR-ADM-005-create',[page.locator('.form-grid'),page.locator('.form-hint'),btn('저장')],true);await close()
 await btn('Adobe Creative Cloud 사용자 보기').click();await page.locator('.assignment-user').first().waitFor()
 await shot('SCR-ADM-006',[label('직원 검색'),page.locator('.assignment-user').first(),btn('수정').first(),btn('권한 회수').first()],true)
 await btn('수정').first().click();await shot('SCR-ADM-010',[page.locator('[role=dialog] .notice'),label('권한 승인 시작일'),label('권한 승인 종료일'),btn('저장')],true);await close()
 await btn('Adobe Creative Cloud 사용자 보기').click();await page.locator('.assignment-user').first().waitFor();await btn('권한 회수').first().click();await page.locator('textarea').fill('프로젝트 종료로 사용 권한을 회수합니다.')
 await shot('SCR-ADM-009',[page.locator('.modal-summary'),page.locator('[role=dialog] .notice'),page.locator('textarea'),page.getByRole('dialog').getByRole('button',{name:'권한 회수',exact:true})],true)
}finally{
 await writeFile(resolve(here,'captures.json'),JSON.stringify(records,null,2));await browser.close()
}
