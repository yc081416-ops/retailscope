async(page)=>{
 const checked_at=new Date().toISOString(),pages=[];await page.setViewportSize({width:1440,height:1000});
 if(Math.abs(await page.evaluate(()=>devicePixelRatio)-1)>.01)throw Error('Showcase requires 100% browser zoom');
 for(const [path,key,test] of [['/','overview','kpi-0'],['/users','users','analysis-kpi-0'],['/products','products','analysis-kpi-0'],['/delivery','delivery','analysis-kpi-0'],['/findings','findings',null],['/quality','quality',null]]){
  await page.goto('http://127.0.0.1:5174'+path);if(test)await page.getByTestId(test).waitFor();else await page.locator(path==='/findings'?'.finding-card':'.trust-status').first().waitFor();
  await page.mouse.move(5,5);await page.evaluate(()=>window.scrollTo(0,0));await page.waitForTimeout(300);await page.screenshot({path:`docs/screenshots/showcase/${key}.png`});pages.push({path,title:await page.locator('h1').innerText(),screenshot:`docs/screenshots/showcase/${key}.png`});
  if(key==='users'){
   await page.locator('.analysis-panel').first().screenshot({path:'docs/screenshots/showcase/rfm.png'});
   const cohort=page.getByRole('img',{name:'Cohort回购活跃留存热力图',exact:true});await cohort.scrollIntoViewIfNeeded();await page.mouse.move(5,5);await cohort.screenshot({path:'docs/screenshots/showcase/cohort.png'});
  }
  if(key==='findings'){
   await page.getByTestId('evidence-F05').locator(':scope > summary').click();await page.getByTestId('mean-ci').waitFor();await page.getByTestId('mean-ci').scrollIntoViewIfNeeded();await page.waitForTimeout(250);await page.locator('.association-proof').screenshot({path:'docs/screenshots/showcase/statistical-evidence.png'});
  }
 }
 await page.goto('http://127.0.0.1:5174/');await page.getByTestId('kpi-0').waitFor();return {checked_at,pages,real_database_kpi:await page.getByTestId('kpi-0').innerText()};
}
