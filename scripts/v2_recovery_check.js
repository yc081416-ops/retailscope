async(page)=>{
  await page.getByRole('button',{name:'重新连接',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('[data-testid="kpi-0"]')?.textContent==='BRL 13,221,498.11');
  return {recovered:true,kpis:await Promise.all([0,1,2,3].map(i=>page.getByTestId(`kpi-${i}`).innerText()))};
}
