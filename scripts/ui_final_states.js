async(page)=>{
 const zoom=await page.evaluate(()=>devicePixelRatio),tag=zoom>1.2?'125':'100',checks=[];
 for(const [width,height] of [[1440,1000],[1280,900]]){
  await page.setViewportSize({width,height});
  for(const key of ['overview','products','delivery']){
   await page.goto('http://127.0.0.1:5174/'+(key==='overview'?'':key));await page.getByTestId(key==='overview'?'kpi-0':'analysis-kpi-0').waitFor();
   await page.getByLabel('开始日期',{exact:true}).fill('2017-05-10');await page.getByLabel('结束日期',{exact:true}).fill('2017-06-20');await page.getByLabel('客户州',{exact:true}).selectOption('SP');
   if(key!=='overview'){
    await page.getByRole('combobox',{name:'商品类目',exact:true}).click();await page.getByRole('searchbox',{name:'搜索商品类目',exact:true}).fill('厨房');await page.screenshot({path:`docs/screenshots/ui-final/picker-${key}-${width}-z${tag}.png`});
    await page.getByRole('searchbox',{name:'搜索商品类目',exact:true}).fill('美容');await page.getByRole('searchbox',{name:'搜索商品类目',exact:true}).press('Enter');
   }
   if(!await page.getByText('更改待应用',{exact:true}).isVisible())throw Error('Pending scope hidden');await page.getByRole('button',{name:'应用筛选',exact:true}).click();
   await page.waitForFunction(({key})=>document.querySelector(`[data-testid="${key==='overview'?'kpi-0':key==='delivery'?'analysis-kpi-3':'analysis-kpi-0'}"]`)?.textContent===(key==='overview'?'BRL 250,817.27':key==='delivery'?'135':'BRL 15,182.76'),{key});
   await page.mouse.move(5,5);await page.screenshot({path:`docs/screenshots/ui-final/${key}-filtered-${width}-z${tag}.png`});
   await page.getByLabel('结束日期',{exact:true}).fill('2020-01-02');await page.getByLabel('开始日期',{exact:true}).fill('2020-01-01');await page.getByRole('button',{name:'应用筛选',exact:true}).click();await page.locator('.empty-notice').waitFor();await page.screenshot({path:`docs/screenshots/ui-final/${key}-empty-${width}-z${tag}.png`});
   await page.getByRole('button',{name:'重置',exact:true}).click();await page.getByTestId(key==='overview'?'kpi-0':'analysis-kpi-0').waitFor();checks.push({key,width,zoom:tag,filtered:true,pending:true,empty:true,reset:true});
  }
  await page.goto('http://127.0.0.1:5174/users');await page.getByTestId('analysis-kpi-0').waitFor();await page.locator('summary').filter({hasText:'RFM分类规则'}).click();await page.locator('summary').filter({hasText:'RFM分类规则'}).scrollIntoViewIfNeeded();await page.screenshot({path:`docs/screenshots/ui-final/rfm-rules-${width}-z${tag}.png`});
  await page.getByRole('img',{name:'Cohort回购活跃留存热力图',exact:true}).scrollIntoViewIfNeeded();await page.screenshot({path:`docs/screenshots/ui-final/cohort-focus-${width}-z${tag}.png`});checks.push({key:'users',width,zoom:tag,rules:true,focus:true,local_filter:'not_applicable_fixed_sample'});
  await page.goto('http://127.0.0.1:5174/findings');await page.getByTestId('evidence-F05').locator(':scope > summary').click();await page.getByTestId('mean-ci').waitFor();await page.getByTestId('mean-ci').scrollIntoViewIfNeeded();await page.screenshot({path:`docs/screenshots/ui-final/findings-expanded-${width}-z${tag}.png`});await page.getByLabel('分析专题',{exact:true}).selectOption('用户与留存');if(await page.locator('.finding-card').count()!==2)throw Error('Topic filter broken');checks.push({key:'findings',width,zoom:tag,expanded:true,topic:true});
  await page.goto('http://127.0.0.1:5174/quality');await page.locator('.trust-status').waitFor();await page.getByText('缺失与重复 · 历史审计',{exact:true}).first().click();await page.getByLabel('字段缺失范围',{exact:true}).selectOption('order_items');await page.getByLabel('字段缺失范围',{exact:true}).scrollIntoViewIfNeeded();await page.screenshot({path:`docs/screenshots/ui-final/quality-audit-${width}-z${tag}.png`});if(!await page.getByText('执行时间：未记录',{exact:true}).count())throw Error('Audit time misrepresented');checks.push({key:'quality',width,zoom:tag,historical_details:true,missing_filter_empty:true});
 }
 return {checks,zoom:tag};
}
