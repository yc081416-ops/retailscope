async(page)=>{
 await page.goto('http://127.0.0.1:5174/');await page.getByTestId('kpi-0').waitFor();
 await page.getByLabel('开始日期',{exact:true}).fill('2017-05-10');await page.getByLabel('结束日期',{exact:true}).fill('2017-06-20');await page.getByLabel('客户州',{exact:true}).selectOption('SP');await page.getByRole('button',{name:'应用筛选',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('[data-testid="kpi-0"]')?.textContent==='BRL 250,817.27');
 await page.getByRole('button',{name:'导出 CSV',exact:true}).scrollIntoViewIfNeeded();await page.waitForTimeout(200);const event=page.waitForEvent('download');await page.getByRole('button',{name:'导出 CSV',exact:true}).click();await (await event).saveAs('reports/v2-04/overview-filtered.csv');
 await page.getByLabel('结束日期',{exact:true}).fill('2020-01-02');await page.getByLabel('开始日期',{exact:true}).fill('2020-01-01');await page.getByRole('button',{name:'应用筛选',exact:true}).click();await page.waitForFunction(()=>document.querySelector('[data-testid="kpi-0"]')?.textContent==='BRL 0.00');
 if(await page.getByTestId('kpi-1').innerText()!=='0')throw Error('Empty order count');
 await page.getByRole('button',{name:'重置',exact:true}).click();await page.waitForFunction(()=>document.querySelector('[data-testid="kpi-0"]')?.textContent==='BRL 13,221,498.11');
 await page.goto('http://127.0.0.1:5174/findings');await page.getByTestId('mean-difference').waitFor();
 const detail=page.getByTestId('finding-F05').locator('details');await detail.locator('summary').click();if(!await detail.getAttribute('open')&&await detail.getAttribute('open')!== '')throw Error('Evidence details not open');
 await page.goto('http://127.0.0.1:5174/quality');await page.getByTestId('latest-test-record').waitFor();
 await page.getByText('展开当前表与视图目录',{exact:true}).click();if(!await page.getByRole('table',{name:'当前架构对象目录',exact:true}).isVisible())throw Error('Catalogue not opened');
 await page.getByText('展开当前主键、外键及唯一约束',{exact:true}).click();if(!await page.getByRole('table',{name:'当前数据库主外键约束',exact:true}).isVisible())throw Error('Constraints not opened');
 await page.goto('http://127.0.0.1:5174/');await page.getByTestId('kpi-0').waitFor();
 return {overview_filtered_csv:true,overview_real_empty:true,overview_reset:true,findings_detail:true,quality_catalogue_and_constraints:true};
}
