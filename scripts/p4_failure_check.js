async(page)=>{
  await page.getByRole('button',{name:'刷新查询缓存',exact:true}).click();
  await page.getByRole('button',{name:'重新连接',exact:true}).waitFor();
  await page.locator('[data-testid="stMain"]').evaluate(el=>el.scrollTop=0);
  await page.screenshot({path:'reports/p4/db_unavailable.png'});
  return {database_failure_message_visible:await page.getByText('数据暂时无法读取。',{exact:false}).isVisible(),
    exceptions:await page.locator('[data-testid="stException"]').count()};
}
