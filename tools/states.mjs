import puppeteer from 'puppeteer-core'
const OUT=process.argv[2]
const b=await puppeteer.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:'new',args:['--no-sandbox']})
const B='http://127.0.0.1:8099'
const log=[]

// 1. FAQ open + keyboard operable
{const p=await b.newPage();await p.setViewport({width:1440,height:900})
 await p.goto(B+'/',{waitUntil:'networkidle0'});await new Promise(r=>setTimeout(r,900))
 await p.evaluate(()=>document.querySelector('.faq-item__question').scrollIntoView({block:'center'}))
 await new Promise(r=>setTimeout(r,300))
 // keyboard: focus then Enter
 await p.focus('.faq-item__question'); await p.keyboard.press('Enter')
 await new Promise(r=>setTimeout(r,600))
 const r=await p.evaluate(()=>{const a=document.querySelector('.faq-item__answer');const q=document.querySelector('.faq-item__question')
   return {h:Math.round(a.getBoundingClientRect().height),expanded:q.getAttribute('aria-expanded'),focusRing:getComputedStyle(document.activeElement).outlineWidth}})
 log.push(['FAQ opens via keyboard', r.h>20&&r.expanded==='true', JSON.stringify(r)])
 await p.screenshot({path:`${OUT}/state-faq-open.png`,clip:{x:300,y:200,width:840,height:500}})
 await p.close()}

// 2. Before/after slider drag + keyboard
{const p=await b.newPage();await p.setViewport({width:1440,height:900})
 await p.goto(B+'/',{waitUntil:'networkidle0'});await new Promise(r=>setTimeout(r,900))
 const before=await p.evaluate(()=>getComputedStyle(document.querySelector('.ba')).getPropertyValue('--pos'))
 await p.focus('.ba__range')
 for(let i=0;i<12;i++) await p.keyboard.press('ArrowRight')
 await new Promise(r=>setTimeout(r,300))
 const after=await p.evaluate(()=>getComputedStyle(document.querySelector('.ba')).getPropertyValue('--pos'))
 // pointer drag
 const box=await p.evaluate(()=>{const f=document.querySelector('.ba__frame').getBoundingClientRect();return {x:f.x,y:f.y,w:f.width,h:f.height}})
 await p.mouse.move(box.x+box.w*0.5,box.y+box.h*0.5); await p.mouse.down()
 await p.mouse.move(box.x+box.w*0.18,box.y+box.h*0.5,{steps:12}); await p.mouse.up()
 await new Promise(r=>setTimeout(r,250))
 const dragged=await p.evaluate(()=>getComputedStyle(document.querySelector('.ba')).getPropertyValue('--pos'))
 log.push(['Slider: keyboard arrows move divider', before!==after, `${before.trim()} -> ${after.trim()}`])
 log.push(['Slider: pointer drag moves divider', after!==dragged, `${after.trim()} -> ${dragged.trim()}`])
 await p.screenshot({path:`${OUT}/state-slider-dragged.png`,clip:{x:box.x-10,y:box.y-10,width:box.w+20,height:box.h+50}})
 await p.close()}

// 3. Mobile nav open + focus trap + Escape
{const p=await b.newPage();await p.setViewport({width:390,height:844,isMobile:true,hasTouch:true})
 await p.goto(B+'/',{waitUntil:'networkidle0'});await new Promise(r=>setTimeout(r,800))
 await p.click('#menu-toggle'); await new Promise(r=>setTimeout(r,500))
 const open=await p.evaluate(()=>{const n=document.getElementById('mobile-nav');return{vis:getComputedStyle(n).visibility,hidden:n.getAttribute('aria-hidden'),focus:document.activeElement.className}})
 await p.screenshot({path:`${OUT}/state-mobilenav.png`})
 await p.keyboard.press('Escape'); await new Promise(r=>setTimeout(r,500))
 const closed=await p.evaluate(()=>{const n=document.getElementById('mobile-nav');return{vis:getComputedStyle(n).visibility,expanded:document.getElementById('menu-toggle').getAttribute('aria-expanded'),focus:document.activeElement.id}})
 log.push(['Mobile nav opens, moves focus in',open.vis==='visible'&&open.hidden==='false'&&open.focus.includes('mobile-nav__link'),JSON.stringify(open)])
 log.push(['Escape closes nav + restores focus',closed.vis==='hidden'&&closed.expanded==='false'&&closed.focus==='menu-toggle',JSON.stringify(closed)])
 await p.close()}

// 4. Keyboard focus visibility across the page
{const p=await b.newPage();await p.setViewport({width:1440,height:900})
 await p.goto(B+'/',{waitUntil:'networkidle0'});await new Promise(r=>setTimeout(r,800))
 let noRing=0,checked=0
 for(let i=0;i<25;i++){
   await p.keyboard.press('Tab')
   const r=await p.evaluate(()=>{const e=document.activeElement;if(!e||e===document.body)return null
     const cs=getComputedStyle(e);return {tag:e.tagName,cls:String(e.className).slice(0,24),outline:cs.outlineWidth,style:cs.outlineStyle}})
   if(!r)continue; checked++
   if(r.outline==='0px'||r.style==='none') noRing++
 }
 log.push(['Every tab stop shows a focus ring',noRing===0,`${checked} stops checked, ${noRing} without ring`])
 await p.close()}

// 5. Sticky CTA bar appears past hero, hidden at top
{const p=await b.newPage();await p.setViewport({width:390,height:844,isMobile:true})
 await p.goto(B+'/',{waitUntil:'networkidle0'});await new Promise(r=>setTimeout(r,900))
 const atTop=await p.evaluate(()=>getComputedStyle(document.getElementById('mobile-cta-bar')).visibility)
 await p.evaluate(()=>window.scrollTo(0,2500)); await new Promise(r=>setTimeout(r,700))
 const scrolled=await p.evaluate(()=>getComputedStyle(document.getElementById('mobile-cta-bar')).visibility)
 log.push(['CTA bar hidden at top, shows after hero',atTop==='hidden'&&scrolled==='visible',`${atTop} -> ${scrolled}`])
 await p.close()}

// 6. Reduced motion
{const p=await b.newPage();await p.setViewport({width:390,height:844,isMobile:true})
 await p.emulateMediaFeatures([{name:'prefers-reduced-motion',value:'reduce'}])
 await p.goto(B+'/',{waitUntil:'networkidle0'});await new Promise(r=>setTimeout(r,1500))
 const r=await p.evaluate(()=>{const all=[...document.querySelectorAll('.reveal, .stagger-children > *')].filter(e=>{const b=e.getBoundingClientRect();return b.width||b.height})
   return {cls:document.documentElement.className,hidden:all.filter(e=>parseFloat(getComputedStyle(e).opacity)<0.99).length,total:all.length}})
 log.push(['Reduced motion: all visible, no animation',r.cls.includes('motion-off')&&r.hidden===0,JSON.stringify(r)])
 await p.close()}

// 7. Rail arrows disabled state visible
{const p=await b.newPage();await p.setViewport({width:1440,height:900})
 await p.goto(B+'/',{waitUntil:'networkidle0'});await new Promise(r=>setTimeout(r,900))
 await p.evaluate(()=>document.querySelector('.review-rail').scrollIntoView({block:'center'}))
 await new Promise(r=>setTimeout(r,500))
 const r=await p.evaluate(()=>{const prev=document.querySelector('[data-rail-prev]');const cs=getComputedStyle(prev)
   return {disabled:prev.disabled,opacity:cs.opacity,pe:cs.pointerEvents}})
 log.push(['Disabled rail arrow is visually distinct', !r.disabled || parseFloat(r.opacity)<0.9, JSON.stringify(r)])
 await p.close()}

await b.close()
let fails=0
for(const [name,ok,detail] of log){ if(!ok)fails++; console.log(`${ok?'PASS':'FAIL'}  ${name.padEnd(44)} ${detail}`) }
console.log(`\n${log.length-fails}/${log.length} interaction checks pass`)
