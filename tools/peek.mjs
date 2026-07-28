import puppeteer from 'puppeteer-core'
const out=process.argv[2]
const b=await puppeteer.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:'new',args:['--no-sandbox']})
for(const v of [{n:'desktop',w:1440,h:940,m:false},{n:'mobile',w:390,h:844,m:true}]){
  const p=await b.newPage(); await p.setViewport({width:v.w,height:v.h,isMobile:v.m,hasTouch:v.m})
  const errs=[]; p.on('pageerror',e=>errs.push(String(e))); p.on('console',m=>{if(m.type()==='error')errs.push(m.text())})
  await p.goto('http://127.0.0.1:8099/',{waitUntil:'networkidle0'})
  await new Promise(r=>setTimeout(r,900))
  await p.screenshot({path:`${out}/live-${v.n}.png`})
  const s=await p.evaluate(()=>{
    const btn=document.querySelector('.btn--cta')
    return {cta:getComputedStyle(btn).backgroundColor, imgs:[...document.images].filter(i=>i.naturalWidth>0).length+'/'+document.images.length}
  })
  console.log(`${v.n}: CTA ${s.cta}  images loaded ${s.imgs}  errors ${errs.length}`)
  await p.close()
}
await b.close()
