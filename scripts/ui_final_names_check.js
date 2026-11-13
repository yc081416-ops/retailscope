async(page)=>{
 const checked_at=new Date().toISOString(),checks=[];
 for(const pageKey of ['products','delivery']){
  await page.goto('http://127.0.0.1:5174/'+pageKey);await page.getByTestId('analysis-kpi-0').waitFor();
  for(const [code,name] of [['cool_stuff','Cool Stuff'],['la_cuisine','La Cuisine'],['seguros_e_servicos','Seguros e Serviços']]){
   const picker=page.getByRole('combobox',{name:'商品类目',exact:true});await picker.click();await page.getByRole('searchbox',{name:'搜索商品类目',exact:true}).fill(code);await page.getByRole('option',{name,exact:true}).waitFor();await page.getByRole('searchbox',{name:'搜索商品类目',exact:true}).fill(name);await page.getByRole('option',{name,exact:true}).click();
   const request=page.waitForResponse(r=>r.url().includes(`/api/analysis/${pageKey}?`)&&new URL(r.url()).searchParams.get('category')===code);await page.getByRole('button',{name:'应用筛选',exact:true}).click();const response=await request;const payload=await response.json();await page.getByTestId('analysis-kpi-0').waitFor();if(payload.scope.category!==code||!(await picker.innerText()).includes(name))throw Error('Display/raw value mismatch');
   if(pageKey==='products'){
    const table=page.getByRole('table',{name:'品类贡献排行',exact:true});await table.getByRole('button',{name:`筛选类目 ${code}`,exact:true}).waitFor();if(!(await table.innerText()).includes(name))throw Error('Ranking name mismatch');
    const trend=page.getByRole('img',{name:'品类月度金额趋势',exact:true});await trend.scrollIntoViewIfNeeded();if(!(await trend.locator('svg').innerHTML()).includes(name))throw Error('Legend name mismatch');
    const chart=page.getByRole('img',{name:'TOP10品类商品金额',exact:true});await chart.scrollIntoViewIfNeeded();const b=await chart.boundingBox();await page.mouse.move(b.x+b.width*.65,b.y+b.height*.48);const tip=chart.locator('div[style*="z-index"]:visible').last();await tip.waitFor();if(!(await tip.innerText()).includes(name))throw Error('Tooltip name mismatch');await chart.screenshot({path:`output/playwright/ui-final-fixes/${code}.png`});
   }
   const button=page.getByRole('button',{name:'导出 CSV',exact:true});await button.scrollIntoViewIfNeeded();await page.waitForTimeout(200);const event=page.waitForEvent('download');await button.click();const file=`${pageKey}-${code}.csv`;await(await event).saveAs('reports/ui-final-fixes/'+file);checks.push({page:pageKey,code,display_name:name,raw_query_value:payload.scope.category,search_by_code:true,search_by_display_name:true,export:file});
  }
 }
 await page.goto('http://127.0.0.1:5174/');await page.getByTestId('kpi-0').waitFor();return {checked_at,checks};
}
