async(page)=>{
 const result={navigation:[],screens:[]};const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const assets=[];page.on('request',r=>{if(r.url().includes('/assets/')&&r.url().endsWith('.js'))assets.push(r.url())});
 await page.setViewportSize({width:1440,height:1000});
 await page.goto('http://127.0.0.1:5174/');await page.getByTestId('kpi-0').waitFor();
 result.home_assets=[...assets];if(assets.some(a=>/\/(FindingsPage|Quality)-/.test(a)))throw new Error('Evidence pages loaded eagerly on home');
 const pages=[['经营总览','经营总览','kpi-0','BRL 13,221,498.11'],['用户价值分析','用户价值分析','analysis-kpi-0','93,358'],['商品与品类','商品与品类分析','analysis-kpi-0','BRL 13,221,498.11'],['履约与评价','履约与评价分析','analysis-kpi-0','12.56 天'],['经营发现','经营发现','mean-difference','-2.0188 分'],['数据质量中心','数据质量中心','latest-test-record',null]];
 for(const [nav,title,test,value] of pages){
   await page.getByRole('link',{name:nav,exact:true}).click();await page.getByRole('heading',{name:title,exact:true}).waitFor();await page.getByTestId(test).waitFor();
   const actual=await page.getByTestId(test).innerText();if(value&&actual!==value)throw new Error(`${nav} data mismatch ${actual}`);
   if(await page.locator('nav a[aria-current="page"]').innerText()!==nav)throw new Error('Navigation highlight mismatch');
   result.navigation.push({nav,title,loaded:true,first_value:actual});
 }
 if(await page.locator('nav a').count()!==6||await page.locator('nav button:disabled').count())throw new Error('All six pages must be usable links');
 await page.goBack();await page.getByRole('heading',{name:'经营发现',exact:true}).waitFor();await page.getByTestId('mean-difference').waitFor();
 await page.goForward();await page.getByRole('heading',{name:'数据质量中心',exact:true}).waitFor();await page.getByTestId('latest-test-record').waitFor();result.history_verified=true;
 const facts=await (await page.request.get('http://127.0.0.1:5174/api/evidence/findings')).json();
 for(const key of ['findings','quality']){
   await page.getByRole('link',{name:key==='findings'?'经营发现':'数据质量中心',exact:true}).click();
   await page.getByTestId(key==='findings'?'mean-difference':'latest-test-record').waitFor();
   for(const [width,height] of [[1440,1000],[1280,900]]){
     await page.setViewportSize({width,height});await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));await page.waitForTimeout(250);
     const layout=await page.evaluate(()=>({horizontalOverflow:document.documentElement.scrollWidth>innerWidth,titleFont:parseFloat(getComputedStyle(document.querySelector('h1')).fontSize),navFont:parseFloat(getComputedStyle(document.querySelector('.nav-link')).fontSize)}));
     if(layout.horizontalOverflow||layout.titleFont!==29||layout.navFont<14)throw new Error('Evidence page overflow or frozen-font regression');
     await page.screenshot({path:`docs/screenshots/v2-03/${key}-${width}.png`});await page.screenshot({path:`docs/screenshots/v2-03/${key}-${width}-full.png`,fullPage:true});
     result.screens.push({key,width,height,...layout});
   }
   await page.setViewportSize({width:1440,height:1000});
   if(key==='findings'){
     if(await page.locator('.finding-card').count()!==7)throw new Error('Seven findings not shown');
     for(const f of facts.findings){const card=page.getByTestId(`finding-${f.id}`);if(await card.locator('.finding-result').innerText()!==f.result)throw new Error('Result text differs from P3');if(!(await card.locator('.finding-sample').innerText()))throw new Error('Missing sample evidence');}
     result.seven_results_match=true;
     if(await page.getByTestId('mean-ci').innerText()!=='[-2.0575, -1.9800]')throw new Error('P3 interval altered');
     await page.locator('.association-proof').screenshot({path:'docs/screenshots/v2-03/findings-association.png'});
     await page.getByLabel('分析专题',{exact:true}).selectOption('经营趋势');await page.waitForFunction(()=>document.querySelectorAll('.finding-card').length===2);
     await page.getByLabel('分析专题',{exact:true}).selectOption('履约体验');await page.waitForFunction(()=>document.querySelectorAll('.finding-card').length===1);
     const details=page.getByTestId('finding-F05').locator('details');await details.locator('summary').click();if(!await details.locator('pre').isVisible())throw new Error('Evidence details did not expand');
     result.topic_filter_and_details=true;
     await page.getByLabel('分析专题',{exact:true}).selectOption('全部专题');await page.waitForFunction(()=>document.querySelectorAll('.finding-card').length===7);
     await page.getByRole('button',{name:'下载 Markdown 报告',exact:true}).scrollIntoViewIfNeeded();await page.waitForTimeout(200);
     const event=page.waitForEvent('download');await page.getByRole('button',{name:'下载 Markdown 报告',exact:true}).click();const file=await event;await file.saveAs('reports/v2-03/downloaded_report.md');result.report_download=file.suggestedFilename();
   }else{
     const table=page.getByRole('table',{name:'九张原始表当前与历史记录数',exact:true});if(await table.locator('tbody tr').count()!==9)throw new Error('Nine source tables missing');
     if(!await page.getByText('记录执行时间：执行时间未记录；文件保存时间不是执行时间',{exact:true}).first().isVisible())await page.getByText('记录执行时间：执行时间未记录；文件保存时间不是执行时间',{exact:true}).first().scrollIntoViewIfNeeded();
     result.audit_time_honest=true;result.nine_tables=true;
     await page.getByLabel('字段缺失范围',{exact:true}).selectOption('order_reviews');await page.getByLabel('仅显示有缺失字段',{exact:true}).uncheck();
     const rows=await page.getByRole('table',{name:'P0历史字段缺失',exact:true}).locator('tbody tr').allTextContents();if(rows.length!==7||rows.some(t=>!t.includes('order_reviews')))throw new Error('Historical field filter mismatch');
     result.missing_field_filter=true;
     await page.getByLabel('字段缺失范围',{exact:true}).selectOption('customers');await page.getByLabel('仅显示有缺失字段',{exact:true}).check();
     await page.getByRole('table',{name:'P0历史字段缺失',exact:true}).getByText('当前范围没有可展示的结果。',{exact:true}).waitFor();result.quality_empty_filter_verified=true;
     await page.getByLabel('字段缺失范围',{exact:true}).selectOption('order_reviews');await page.getByLabel('仅显示有缺失字段',{exact:true}).uncheck();
     await page.getByRole('heading',{name:'02 · 缺失、重复与逻辑唯一键',exact:true}).scrollIntoViewIfNeeded();await page.screenshot({path:'docs/screenshots/v2-03/quality-historical.png'});
     await page.getByRole('button',{name:'下载质量证据',exact:true}).scrollIntoViewIfNeeded();await page.waitForTimeout(200);const event=page.waitForEvent('download');await page.getByRole('button',{name:'下载质量证据',exact:true}).click();await (await event).saveAs('reports/v2-03/downloaded_quality.json');result.quality_download=true;
     const real=await (await page.request.get('http://127.0.0.1:5174/api/evidence/quality')).json();
     await page.route('**/api/evidence/quality',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({...real,live:{...real.live,status:'unavailable',raw_counts:[],objects:[],constraints:[],warehouse_checks:[],error:'当前数据库查询不可用，历史证据不是当前通过记录。'}})}));
     await page.getByRole('button',{name:'刷新数据',exact:true}).click();await page.getByText('当前查询不可用',{exact:true}).waitFor();
     if(await page.getByRole('table',{name:'九张原始表当前与历史记录数',exact:true}).locator('tbody tr').count()!==9)throw new Error('History disappeared during live failure');
     result.quality_partial_live_failure=true;await page.screenshot({path:'output/playwright/v2-03/quality-partial.png'});await page.unroute('**/api/evidence/quality');
   }
   const endpoint=`**/api/evidence/${key}`;
   await page.route(endpoint,route=>route.fulfill({status:503,contentType:'application/json',body:'{"detail":"unavailable"}'}));await page.getByRole('button',{name:'刷新数据',exact:true}).click();await page.getByRole('button',{name:'重新连接',exact:true}).waitFor();
   result[`${key}_error_verified`]=true;await page.screenshot({path:`output/playwright/v2-03/${key}-error.png`});await page.unroute(endpoint);
   await page.route(endpoint,async route=>{await new Promise(r=>setTimeout(r,900));await route.continue()});
   await page.getByRole('button',{name:'重新连接',exact:true}).click();await page.getByLabel('正在加载分析数据',{exact:true}).waitFor();result[`${key}_loading_verified`]=true;
   await page.getByTestId(key==='findings'?'mean-difference':'latest-test-record').waitFor();await page.unroute(endpoint);
   if(key==='findings'){
     await page.route(endpoint,route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({...facts,findings:[]})}));await page.getByRole('button',{name:'刷新数据',exact:true}).click();await page.getByText('当前证据没有可展示的发现，请核对P3快照。',{exact:true}).waitFor();result.findings_empty_verified=true;await page.unroute(endpoint);await page.getByRole('button',{name:'刷新数据',exact:true}).click();await page.getByTestId('mean-difference').waitFor();
   }
 }
 await page.getByRole('link',{name:'经营总览',exact:true}).click();await page.getByTestId('kpi-0').waitFor();await page.getByRole('button',{name:'查看经营发现',exact:true}).click();await page.getByRole('heading',{name:'经营发现',exact:true}).waitFor();await page.getByTestId('mean-difference').waitFor();result.legacy_entry_migrated=true;
 await page.evaluate(()=>window.scrollTo(0,0));result.page_errors=errors;return result;
}
