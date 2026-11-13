async(page)=>{
 await page.getByRole('button',{name:'重新连接',exact:true}).click();await page.waitForFunction(()=>document.querySelector('[data-testid="kpi-0"]')?.textContent==='BRL 13,221,498.11');
 const quality=await (await page.request.get('http://127.0.0.1:8000/api/evidence/quality')).json();
 if(quality.live.status!=='available')throw new Error('Database did not recover');
 return {recovered:true,kpi:await page.getByTestId('kpi-0').innerText(),raw_tables:quality.live.raw_counts.length};
}
