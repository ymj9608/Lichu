import {chromium} from '@playwright/test'
import {resolve} from 'node:path'
import {pathToFileURL} from 'node:url'
const prefix=`${process.env.SUBMISSION_CLASS||'CLASS'}_${process.env.SUBMISSION_NAME||'NAME'}_Lichu`
const browser=await chromium.launch({headless:true})
try{
 const page=await browser.newPage()
 await page.goto(pathToFileURL(resolve('../docs/project-overview.html')).href,{waitUntil:'networkidle'})
 await page.evaluate(()=>Promise.all([...document.images].map(img=>img.decode())))
 await page.pdf({path:resolve(`../docs/${prefix}-개요.pdf`),format:'A4',printBackground:true,preferCSSPageSize:true})
 console.log(`Generated docs/${prefix}-개요.pdf`)
}finally{await browser.close()}
