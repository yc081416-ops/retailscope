async(page)=>{
  await page.getByRole('button',{name:'重新连接',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('[data-testid="stMetricValue"]')?.textContent==='96,478');
  await page.getByText('P1 已验收描述性事实',{exact:true}).waitFor();
  await page.locator('[data-testid="stMain"]').evaluate(el=>el.scrollTop=0);
  await page.screenshot({path:'reports/p4/db_recovered.png'});
  return {recovered:true,metrics:await page.locator('[data-testid="stMetricValue"]').allTextContents(),
    exceptions:await page.locator('[data-testid="stException"]').count()};
}
