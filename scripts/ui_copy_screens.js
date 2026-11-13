async(page)=>{
 const pages=[];
 for(const [path,key,test] of [['/','overview','kpi-0'],['/users','users','analysis-kpi-0'],['/products','products','analysis-kpi-0'],['/delivery','delivery','analysis-kpi-0'],['/findings','findings',null],['/quality','quality',null]]){
  await page.goto('http://127.0.0.1:5174'+path);if(test)await page.getByTestId(test).waitFor();else await page.locator(path==='/findings'?'.finding-card':'.trust-status').first().waitFor();
  for(const [width,height] of [[1440,1000],[1280,900]]){
   await page.setViewportSize({width,height});await page.mouse.move(5,5);await page.evaluate(()=>window.scrollTo(0,0));await page.waitForTimeout(300);
   const layout=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth,clippedKpis:[...document.querySelectorAll('.kpi-value,.kpi-label')].some(e=>e.scrollWidth>e.clientWidth),h1:parseFloat(getComputedStyle(document.querySelector('h1')).fontSize),defaultText:document.querySelector('main').innerText}));
   if(layout.overflow||layout.clippedKpis||/\bP[0-4]\b|\bV2\b|SHA-256|\d+ passed/.test(layout.defaultText))throw Error('Final copy/layout failure '+key);
   await page.screenshot({path:`docs/screenshots/ui-copy/${key}-${width}.png`});await page.screenshot({path:`docs/screenshots/ui-copy/${key}-${width}-full.png`,fullPage:true});pages.push({key,width,height,...layout});
  }
 }
 await page.goto('http://127.0.0.1:5174/findings');await page.getByTestId('evidence-F05').locator(':scope > summary').click();await page.getByTestId('mean-ci').waitFor();await page.waitForTimeout(300);await page.getByTestId('evidence-F05').screenshot({path:'docs/screenshots/ui-copy/findings-evidence.png'});
 await page.goto('http://127.0.0.1:5174/');await page.getByTestId('kpi-0').waitFor();return {pages,final_screens_verified:true};
}
