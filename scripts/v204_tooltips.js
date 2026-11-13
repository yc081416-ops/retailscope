async(page)=>{
 const checks=[];
 for(const [path,label] of [['/','月度商品成交额与订单趋势'],['/users','RFM分层用户数'],['/products','TOP10品类商品金额'],['/delivery','逾期与订单评价关联'],['/findings','P3全样本逾期与评价均分']]){
  await page.goto('http://127.0.0.1:5174'+path);const chart=page.getByRole('img',{name:label,exact:true});await chart.locator('svg').waitFor();await chart.scrollIntoViewIfNeeded();await page.waitForTimeout(200);
  const box=await chart.boundingBox();await page.mouse.move(box.x+box.width*.6,box.y+box.height*.4);await page.waitForTimeout(300);
  const tooltip=chart.locator('div[style*="z-index"]:visible').last();await tooltip.waitFor();const text=await tooltip.innerText();if(!text.trim())throw new Error('Empty chart tooltip');
  checks.push({path,label,text});await page.screenshot({path:`output/playwright/v2-04/${path.slice(1)||'overview'}-tooltip.png`});await page.mouse.move(10,10);
 }
 await page.goto('http://127.0.0.1:5174/');await page.getByTestId('kpi-0').waitFor();return {tooltips:checks,all_visible:true};
}
