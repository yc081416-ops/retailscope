async(page)=>{
  await page.getByRole('button',{name:'刷新数据',exact:true}).click();
  await page.getByRole('button',{name:'重新连接',exact:true}).waitFor();
  const response=await page.request.get('http://127.0.0.1:8000/api/overview');
  const error=await response.json();
  if(response.status()!==503||!await page.getByRole('alert').isVisible())throw new Error('Failure state not surfaced');
  if(await page.getByTestId('kpi-0').count())throw new Error('Stale KPI should not remain after failed query');
  await page.screenshot({path:'output/playwright/v2-01/database-unavailable.png'});
  return {http_status:response.status(),api_error:error,curated_message_visible:true,stale_kpis_hidden:true};
}
