async(page)=>{
  await page.getByText('指标说明与历史观察范围',{exact:true}).waitFor();
  await page.waitForFunction(()=>document.querySelectorAll('.js-plotly-plot').length===3);
  const metrics=await page.locator('[data-testid="stMetricValue"]').allTextContents();
  if(metrics[0]!=='BRL 13,221,498.11'||metrics[1]!=='96,478')throw new Error('Legacy baseline mismatch');
  await page.screenshot({path:'output/playwright/v2-01/legacy-streamlit.png'});
  return {legacy_available:true,metrics,plots:3,exceptions:await page.locator('[data-testid="stException"]').count()};
}
