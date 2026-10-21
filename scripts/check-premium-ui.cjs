const {chromium}=require('playwright-core');
const bundled=require('@sparticuz/chromium').default;
const fs=require('fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');process.chdir(root);
const base=process.env.UI_BASE_URL||'http://127.0.0.1:8002';
if(!['127.0.0.1','localhost'].includes(new URL(base).hostname))throw Error('Este teste só pode usar um servidor local sintético');
const artifacts=path.resolve(process.env.UI_SCREENSHOT_DIR||path.join(root,'docs/design'));fs.mkdirSync(artifacts,{recursive:true});
(async()=>{
const browser=await chromium.launch({executablePath:await bundled.executablePath(),args:bundled.args,headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1100},deviceScaleFactor:1});
const errors=[];page.on('pageerror',err=>errors.push(err.message));
const health=await page.request.get(base+'/health');if((await health.json()).mode!=='demo')throw Error('Recusado: só é permitido testar um ambiente DEMO sintético');
await page.goto(base+'/painel');await page.locator('#login:not([hidden])').waitFor();await page.evaluate(()=>document.fonts.ready);
await page.screenshot({path:path.join(artifacts,'premium-login.png'),fullPage:true});
await page.locator('#key').fill('design-preview-only');await page.locator('#login-form button').click();await page.locator('#workspace:not([hidden])').waitFor();await page.locator('.metric').first().waitFor();await page.screenshot({path:path.join(artifacts,'premium-dashboard.png'),fullPage:true});
for(const tab of ['conversations','bookings','settings','simulator']){await page.locator(`nav [data-tab="${tab}"]`).click();await page.locator(`#${tab}:not([hidden])`).waitFor();}
await page.locator('#suggestions button').first().locator('span').click();if(!(await page.locator('#demo-text').inputValue()).includes('produtos'))throw Error('Suggestion nested target broken');
await page.locator('#demo-form button').click();await page.locator('#demo-chat .bubble.assistant').last().waitFor();
await page.locator('nav [data-tab="overview"]').click();
await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(artifacts,'premium-mobile.png'),fullPage:true});
const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth);if(overflow)throw Error('Mobile horizontal overflow');
await page.locator('nav [data-tab="settings"]').click();await page.locator('#settings:not([hidden])').waitFor();
const settingsOverflow=await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth);if(settingsOverflow)throw Error('Mobile settings horizontal overflow');
if(errors.length)throw Error(errors.join('\n'));
console.log('Browser Chromium: login, 5 tabs, nested suggestion click, demo response, 390px viewport and settings — PASS. No JS errors.');
await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
