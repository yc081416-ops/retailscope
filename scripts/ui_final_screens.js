async(page)=>{
 const zoom=await page.evaluate(()=>devicePixelRatio),tag=zoom>1.2?'125':'100',pages=[];
 for(const [path,key,test] of [['/','overview','kpi-0'],['/users','users','analysis-kpi-0'],['/products','products','analysis-kpi-0'],['/delivery','delivery','analysis-kpi-0'],['/findings','findings',null],['/quality','quality',null]]){
  await page.goto('http://127.0.0.1:5174'+path);if(test)await page.getByTestId(test).waitFor();else await page.locator(path==='/findings'?'.finding-card':'.trust-status').first().waitFor();
  for(const [width,height] of [[1440,1000],[1280,900]]){
   await page.setViewportSize({width,height});await page.mouse.move(5,5);await page.evaluate(()=>window.scrollTo(0,0));await page.waitForTimeout(400);
   const metrics=await page.evaluate(()=>({dpr:devicePixelRatio,innerWidth,innerHeight,horizontalOverflow:document.documentElement.scrollWidth>innerWidth,clippedKpis:[...document.querySelectorAll('.kpi-value')].some(e=>e.scrollWidth>e.clientWidth)}));
   await page.screenshot({path:`docs/screenshots/ui-final/${key}-${width}-z${tag}.png`});if(tag==='100')await page.screenshot({path:`docs/screenshots/ui-final/${key}-${width}-z${tag}-full.png`,fullPage:true});pages.push({key,width,height,zoom:tag,...metrics});
  }
 }
 return {pages,zoom:tag};
}
