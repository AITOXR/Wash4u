import puppeteer from 'puppeteer-core';
const CHROME='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const b=await puppeteer.launch({executablePath:CHROME,headless:'new',args:['--no-sandbox']});
const PAGES=['/','/pricing/','/services/','/services/premium-dry-cleaning/','/about-us/','/locate-us/','/packages/','/blog/','/contact-us/','/terms-and-conditions/','/laundry-service-sushant-lok/','/dry-cleaning-sushant-lok/'];
const FULL=`
:root{--t-sm:0.9375rem !important}
.mega__svc{font-size:1rem !important}
.mega--services{width:min(46rem,92vw) !important}
.mobile-nav__sub a{font-size:1rem !important}
@media(min-width:48rem){.header__phone{display:none !important}}
@media(min-width:75rem){.header__phone{display:inline-flex !important}}
.footer h3{font-size:0.8125rem !important}
`;
const XS=FULL+':root{--t-xs:0.8125rem !important}';
const out={};
for(const [vname,css] of [['base',''],['full',FULL],['full+xs',XS]]){
  out[vname]={};
  for(const w of [320,390,768,1024,1200,1216,1280,1440]){
    const bad=[];
    for(const url of PAGES){
      const p=await b.newPage();
      await p.setViewport({width:w,height:900,isMobile:w<500,hasTouch:w<500,deviceScaleFactor:1});
      await p.goto('http://localhost:8080'+url,{waitUntil:'networkidle0'});
      if(css) await p.addStyleTag({content:css});
      await new Promise(r=>setTimeout(r,120));
      const r=await p.evaluate(()=>{
        const docOver=document.documentElement.scrollWidth-window.innerWidth;
        const hi=document.querySelector('.header__inner');
        const hdrOver=hi?hi.scrollWidth-hi.clientWidth:0;
        const cta=document.querySelector('.header__cta');
        const ctaClip=cta&&getComputedStyle(cta).display!=='none'?Math.round(cta.getBoundingClientRect().right-window.innerWidth):0;
        const tb=document.querySelector('.topbar__inner');
        const tbOver=tb?tb.scrollWidth-tb.clientWidth:0;
        // any nowrap element overflowing its own box
        let nowrapClip=0;const samples=[];
        document.querySelectorAll('.kw,.tag,.plan-card__benefit,.topbar__phone,.topbar__area,th,.price-chip').forEach(e=>{
          if(e.scrollWidth-e.clientWidth>1){nowrapClip++;if(samples.length<3)samples.push(e.className+':'+(e.scrollWidth-e.clientWidth));}});
        return {docOver,hdrOver,ctaClip:Math.max(0,ctaClip),tbOver,nowrapClip,samples};
      });
      if(r.docOver>0||r.ctaClip>0||r.tbOver>0||r.nowrapClip>0) bad.push({url,...r});
      await p.close();
    }
    out[vname]['w'+w]=bad.length?bad:'clean';
  }
}
console.log(JSON.stringify(out,null,1));
await b.close();
