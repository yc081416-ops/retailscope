async(page)=>{
 const result={pages:[],direct_urls:[],filters:[]};const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const base='http://127.0.0.1:5174';
 const cases=[['/','经营总览','overview','kpi-0','BRL 13,221,498.11',2],['/users','用户价值分析','users','analysis-kpi-0','93,358',4],['/products','商品与品类分析','products','analysis-kpi-0','BRL 13,221,498.11',4],['/delivery','履约与评价分析','delivery','analysis-kpi-0','12.56 天',4],['/findings','经营发现','findings','mean-difference','-2.0188 分',1],['/quality','数据质量中心','quality','latest-test-record',null,0]];
 const assets=[];page.on('request',r=>{if(r.url().includes('/assets/')&&r.url().endsWith('.js'))assets.push(r.url())});
 for(const [path,title,key,test,value,charts] of cases){
   await page.goto(base+path);await page.getByRole('heading',{name:title,exact:true}).waitFor();await page.getByTestId(test).waitFor();
   await page.waitForFunction(n=>document.querySelectorAll('[role="img"] svg').length===n,charts);
   const actual=await page.getByTestId(test).innerText();if(value&&actual!==value)throw new Error(`${key} baseline changed`);
   result.direct_urls.push({path,title,loaded:true,first_value:actual});
   if(key==='overview')result.home_assets=[...assets];
   for(const [width,height] of [[1440,1000],[1280,900]]){
     await page.setViewportSize({width,height});await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));await page.waitForTimeout(300);
     const layout=await page.evaluate(()=>({horizontalOverflow:document.documentElement.scrollWidth>innerWidth,
       clippedKpis:Array.from(document.querySelectorAll('.kpi-value,.kpi-label')).some(e=>e.scrollWidth>e.clientWidth),titleFont:parseFloat(getComputedStyle(document.querySelector('h1')).fontSize),chartCount:document.querySelectorAll('[role="img"] svg').length}));
     if(layout.horizontalOverflow||layout.clippedKpis||layout.titleFont!==29)throw new Error(`${key} ${width} layout issue ${JSON.stringify(layout)}`);
     await page.screenshot({path:`docs/screenshots/v2-04/${key}-${width}.png`});await page.screenshot({path:`docs/screenshots/v2-04/${key}-${width}-full.png`,fullPage:true});result.pages.push({key,width,height,...layout});
   }
   await page.setViewportSize({width:1440,height:1000});
   if(charts){
     const chart=page.locator('[role="img"]').first();await chart.scrollIntoViewIfNeeded();const box=await chart.boundingBox();await page.mouse.move(box.x+box.width*.56,box.y+box.height*.37);await page.waitForTimeout(200);await page.mouse.move(10,10);
   }
   if(key==='findings'){
     const response=await (await page.request.get(base+'/api/evidence/findings')).json();
     for(const f of response.findings)if(await page.getByTestId(`finding-${f.id}`).locator('.finding-result').innerText()!==f.result)throw new Error('F01-F07 text changed');
     const table=page.getByRole('table',{name:'P3逾期评价样本与评分',exact:true});if(!(await table.innerText()).includes('订单评价均分（订单等权）')||(await table.innerText()).includes('最新评分均值'))throw new Error('F05 terminology remains ambiguous');
     if(await page.getByTestId('mean-ci').innerText()!=='[-2.0575, -1.9800]')throw new Error('CI changed');
     await page.locator('.association-proof').screenshot({path:'docs/screenshots/v2-04/findings-association.png'});
     await page.getByLabel('分析专题',{exact:true}).selectOption('履约体验');await page.waitForFunction(()=>document.querySelectorAll('.finding-card').length===1);await page.getByLabel('分析专题',{exact:true}).selectOption('全部专题');
     await page.getByRole('button',{name:'下载 Markdown 报告',exact:true}).scrollIntoViewIfNeeded();await page.waitForTimeout(200);const event=page.waitForEvent('download');await page.getByRole('button',{name:'下载 Markdown 报告',exact:true}).click();await (await event).saveAs('reports/v2-04/downloaded_report.md');result.f05_semantics_verified=true;result.seven_findings_verified=true;
   }
   if(key==='users'){
     if(!(await page.getByTestId('cohort-null-count').innerText()).includes('298'))throw new Error('Cohort NULL changed');
     const chart=page.getByRole('img',{name:'Cohort回购活跃留存热力图',exact:true});await chart.scrollIntoViewIfNeeded();await page.screenshot({path:'docs/screenshots/v2-04/users-cohort.png'});
     await page.getByLabel('导出内容',{exact:true}).selectOption('cohort');await page.getByRole('button',{name:'导出 CSV',exact:true}).scrollIntoViewIfNeeded();await page.waitForTimeout(200);const event=page.waitForEvent('download');await page.getByRole('button',{name:'导出 CSV',exact:true}).click();await (await event).saveAs('reports/v2-04/users-cohort.csv');result.rfm_cohort_verified=true;
   }
   if(key==='quality'){
     if(await page.getByRole('table',{name:'九张原始表当前与历史记录数',exact:true}).locator('tbody tr').count()!==9)throw new Error('Raw table count mismatch');
     if(!await page.getByText('记录执行时间：执行时间未记录；文件保存时间不是执行时间',{exact:true}).first().count())throw new Error('History timestamp misrepresented');
     await page.getByRole('button',{name:'下载质量证据',exact:true}).scrollIntoViewIfNeeded();await page.waitForTimeout(200);const event=page.waitForEvent('download');await page.getByRole('button',{name:'下载质量证据',exact:true}).click();await (await event).saveAs('reports/v2-04/downloaded_quality.json');result.quality_provenance_verified=true;
   }
 }
 for(const [nav,title] of [['经营总览','经营总览'],['用户价值分析','用户价值分析'],['商品与品类','商品与品类分析'],['履约与评价','履约与评价分析'],['经营发现','经营发现'],['数据质量中心','数据质量中心']]){
   await page.getByRole('link',{name:nav,exact:true}).click();await page.getByRole('heading',{name:title,exact:true}).waitFor();
 }
 await page.goBack();await page.getByRole('heading',{name:'经营发现',exact:true}).waitFor();await page.goForward();await page.getByRole('heading',{name:'数据质量中心',exact:true}).waitFor();result.navigation_history_verified=true;
 for(const [path,pageKey,test,expected] of [['/products','products','analysis-kpi-0','BRL 15,182.76'],['/delivery','delivery','analysis-kpi-3','135']]){
   await page.goto(base+path);await page.getByTestId('analysis-kpi-0').waitFor();await page.getByLabel('开始日期',{exact:true}).fill('2017-05-10');await page.getByLabel('结束日期',{exact:true}).fill('2017-06-20');await page.getByLabel('客户州',{exact:true}).selectOption('SP');await page.getByLabel('商品类目',{exact:true}).selectOption('beleza_saude');
   if(!await page.getByText('更改待应用',{exact:true}).isVisible())throw new Error('Pending filters missing');
   await page.getByRole('button',{name:'应用筛选',exact:true}).click();await page.waitForFunction(({test,expected})=>document.querySelector(`[data-testid="${test}"]`)?.textContent===expected,{test,expected});
   result.filters.push({page:pageKey,start:'2017-05-10',end:'2017-06-20',state:'SP',category:'beleza_saude',value:await page.getByTestId(test).innerText()});
   await page.getByRole('button',{name:'导出 CSV',exact:true}).scrollIntoViewIfNeeded();await page.waitForTimeout(200);const event=page.waitForEvent('download');await page.getByRole('button',{name:'导出 CSV',exact:true}).click();await (await event).saveAs(`reports/v2-04/${pageKey}-filtered.csv`);
   await page.getByLabel('结束日期',{exact:true}).fill('2020-01-02');await page.getByLabel('开始日期',{exact:true}).fill('2020-01-01');await page.getByRole('button',{name:'应用筛选',exact:true}).click();await page.getByText(pageKey==='products'?'当前日期、地区与类目组合没有有效商品明细，请调整或重置筛选。':'当前筛选没有有效订单，请调整日期、地区或类目。',{exact:true}).waitFor();
   result[`${pageKey}_empty`]=true;await page.getByRole('button',{name:'重置',exact:true}).click();await page.getByTestId('analysis-kpi-0').waitFor();
 }
 await page.goto(base+'/');await page.getByTestId('kpi-0').waitFor();await page.getByLabel('开始日期',{exact:true}).fill('2017-05-10');await page.getByLabel('结束日期',{exact:true}).fill('2017-06-20');await page.getByRole('button',{name:'筛选客户州 SP',exact:true}).click();await page.waitForFunction(()=>document.querySelector('[data-testid="kpi-0"]')?.textContent==='BRL 250,817.27');
 result.overview_draft_preserved=await page.getByLabel('开始日期',{exact:true}).inputValue()==='2017-05-10';await page.getByRole('button',{name:'重置',exact:true}).click();await page.waitForFunction(()=>document.querySelector('[data-testid="kpi-0"]')?.textContent==='BRL 13,221,498.11');result.overview_reset=true;
 for(const [path,endpoint,test] of [['/','**/api/overview?*','kpi-0'],['/users','**/api/analysis/users?*','analysis-kpi-0'],['/products','**/api/analysis/products?*','analysis-kpi-0'],['/delivery','**/api/analysis/delivery?*','analysis-kpi-0'],['/findings','**/api/evidence/findings','mean-difference'],['/quality','**/api/evidence/quality','latest-test-record']]){
   await page.goto(base+path);await page.getByTestId(test).waitFor();await page.route(endpoint,route=>route.fulfill({status:503,contentType:'application/json',body:'{"detail":"unavailable"}'}));await page.getByRole('button',{name:'刷新数据',exact:true}).click();await page.getByRole('button',{name:'重新连接',exact:true}).waitFor();if(await page.getByTestId(test).count())throw new Error('Stale results after API failure');await page.unroute(endpoint);
   await page.route(endpoint,async route=>{await new Promise(r=>setTimeout(r,900));await route.continue()});await page.getByRole('button',{name:'重新连接',exact:true}).click();await page.getByLabel(path==='/'?'正在加载经营数据':'正在加载分析数据',{exact:true}).waitFor();await page.getByTestId(test).waitFor();await page.unroute(endpoint);
 }
 result.all_api_error_loading_recovery_verified=true;result.page_errors=errors;await page.goto(base+'/');await page.getByTestId('kpi-0').waitFor();return result;
}
