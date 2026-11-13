async(page)=>{
 const checked_at=new Date().toISOString(),visited_routes=[];
 await page.setViewportSize({width:1440,height:1000});
 for(const [path,key,test] of [['/','overview','kpi-0'],['/users','users','analysis-kpi-0'],['/products','products','analysis-kpi-0'],['/delivery','delivery','analysis-kpi-0'],['/findings','findings',null],['/quality','quality',null]]){
  const response=await page.goto('http://127.0.0.1:5174'+path);
  if(test)await page.getByTestId(test).waitFor();else await page.locator(path==='/findings'?'.finding-card':'.trust-status').first().waitFor();
  await page.mouse.move(5,5);await page.screenshot({path:`reports/github-final/${key}.png`});
  visited_routes.push({path,status:response.status(),title:await page.locator('h1').innerText(),loaded:true});
 }
 await page.goto('http://127.0.0.1:5174/');await page.getByTestId('kpi-0').waitFor();
 return {checked_at,visited_routes,kpi:await page.getByTestId('kpi-0').innerText(),scope:'Current six-page direct navigation and actual data loading, not a full UI interaction re-acceptance.'};
}
