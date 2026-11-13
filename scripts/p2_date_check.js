async(page) => {
  // Uses the visible, keyboard-accessible date segments (no internal session mutation).
  await page.locator('[data-testid="stMain"]').evaluate(el => el.scrollTop=0);
  const values = [
    ['year','start','2018'],['month','start','01'],['day','start','01'],
    ['year','end','2018'],['month','end','01'],['day','end','31'],
  ];
  for (const [part,side,value] of values) {
    const field=page.getByRole('spinbutton',{name:`${part}, 购买日期（含首尾） ${side} date`,exact:true});
    await field.click();
    await field.press('ControlOrMeta+A');
    await field.pressSequentially(value);
    await field.press('Tab');
    await page.waitForTimeout(250);
  }
  await page.keyboard.press('Escape');
  await page.getByRole('heading',{name:'商品与品类分析',exact:true,level:1}).click();
  await page.getByText('当前范围：2018-01-01 至 2018-01-31',{exact:false}).waitFor();
  await page.waitForTimeout(500);
  const metrics=await page.locator('[data-testid="stMetricValue"]').allTextContents();
  await page.screenshot({path:'output/playwright/10-date-filter.png'});
  return {date_start:'2018-01-01',date_end_inclusive:'2018-01-31',metrics};
}
