async(page)=>{
 await page.goto('http://127.0.0.1:5174/');await page.getByRole('button',{name:'重新连接',exact:true}).waitFor();
 const home=await page.request.get('http://127.0.0.1:8000/api/overview');if(home.status()!==503)throw new Error('Expected real DB failure');
 const quality=await (await page.request.get('http://127.0.0.1:8000/api/evidence/quality')).json();
 if(quality.live.status!=='unavailable'||quality.live.raw_counts.length||quality.historical.tables.length!==9)throw new Error('Live failure must not replace history with fake current values');
 await page.screenshot({path:'output/playwright/v2-04/database-unavailable.png'});
 return {actual_database_failure:true,overview_status:home.status(),history_preserved:9,stale_kpis_hidden:await page.getByTestId('kpi-0').count()===0};
}
