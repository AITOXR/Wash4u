import puppeteer from 'puppeteer-core';
const CHROME='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const b=await puppeteer.launch({executablePath:CHROME,headless:'new',args:['--no-sandbox']});
for (const s of ['sofa-cleaning','curtains-cleaning','carpet-cleaning','eco-friendly-laundry']) {
  for (const vw of [1440,390]) {
    const pg=await b.newPage();
    await pg.setViewport({width:vw,height:vw===1440?900:844,deviceScaleFactor:1});
    await pg.evaluateOnNewDocument(()=>{window.__cls=0;new PerformanceObserver(l=>{for(const e of l.getEntries()) if(!e.hadRecentInput) window.__cls+=e.value;}).observe({type:'layout-shift',buffered:true});
      window.__lcp=null;new PerformanceObserver(l=>{const e=l.getEntries().pop();window.__lcp={tag:e.element?e.element.tagName+'.'+(e.element.className||''):'?',size:e.size};}).observe({type:'largest-contentful-paint',buffered:true});});
    await pg.goto('http://localhost:8080/services/'+s+'/',{waitUntil:'networkidle0'});
    await new Promise(r=>setTimeout(r,1500));
    const m=await pg.evaluate(()=>({cls:+(window.__cls||0).toFixed(4),h:Math.round(document.querySelector('.page-hero').getBoundingClientRect().height),lcp:window.__lcp}));
    console.log('BASE',s,vw,JSON.stringify(m));
    await pg.close();
  }
}
await b.close();
