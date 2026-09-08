import {chromium} from '@playwright/test'
import {mkdir} from 'node:fs/promises'
import {resolve} from 'node:path'
const dir=resolve('../docs/screenshots')
await mkdir(dir,{recursive:true})
const browser=await chromium.launch({headless:true})
const page=await browser.newPage({viewport:{width:1440,height:1050},deviceScaleFactor:1})
const base=process.env.FRONTEND_URL||'http://127.0.0.1:5173'
async function shot(name){await page.evaluate(async()=>{await document.fonts.ready;await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))});await page.screenshot({path:resolve(dir,`${name}.png`),fullPage:true})}
async function go(path){await page.goto(base+path);await page.waitForLoadState('networkidle')}
async function login(username,password){await go('/login');await page.getByLabel('아이디',{exact:true}).fill(username);await page.getByLabel('비밀번호',{exact:true}).fill(password);await page.getByRole('button',{name:'로그인',exact:true}).click();await page.waitForURL(username==='master'?'**/admin':'**/licenses');await page.waitForLoadState('networkidle');await page.locator(username==='master'?'.stat-card':'.license-card').first().waitFor()}
try{
  await go('/login');await shot('login')
  await go('/signup');await shot('signup')
  await login('myeongjin',process.env.DEMO_PASSWORD||'LichuDemo2026!')
  await shot('catalog')
  for(const width of [1024,768]){await page.setViewportSize({width,height:1050});await shot(`catalog-${width}`)}
  await page.setViewportSize({width:1440,height:1050})
  await go('/requests');await shot('my-requests')
  await go('/my-licenses');await shot('my-licenses')
  await page.getByRole('button',{name:'로그아웃'}).click()
  await login('master',process.env.MASTER_PASSWORD||'LichuMaster2026!')
  await shot('admin-dashboard')
  await go('/admin/requests');await shot('admin-requests')
  await go('/admin/licenses');await shot('admin-licenses')
  await page.getByRole('button',{name:'Adobe Creative Cloud 사용자 보기',exact:true}).click()
  await page.getByRole('dialog').locator('.assignment-user').first().waitFor()
  await shot('admin-license-users')
  console.log(`Screenshots saved to ${dir}`)
}finally{await browser.close()}
