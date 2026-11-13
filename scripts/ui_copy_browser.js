async(page)=>{
 const base='http://127.0.0.1:5174',errors=[];page.on('pageerror',e=>errors.push(e.message));
 const result={pages:[],filters:[],downloads:[],evidence_preserved:[],navigation:false};
 const cases=[['/','经营总览','overview','kpi-0','BRL 13,221,498.11'],['/users','用户价值分析','users','analysis-kpi-0','93,358'],['/products','商品与品类分析','products','analysis-kpi-0','BRL 13,221,498.11'],['/delivery','履约与评价分析','delivery','analysis-kpi-0','12.56 天'],['/findings','经营发现','findings',null,null],['/quality','数据质量中心','quality',null,null]];
 const ready=async(path,test)=>{await page.goto(base+path);if(test)await page.getByTestId(test).waitFor();else if(path==='/findings')await page.locator('.finding-card').first().waitFor();else await page.locator('.trust-status').waitFor();await page.waitForTimeout(250)};
 const download=async(button,file)=>{await button.scrollIntoViewIfNeeded();await page.waitForTimeout(200);const event=page.waitForEvent('download');await button.click();await (await event).saveAs('reports/ui-copy/'+file);result.downloads.push(file)};
 for(const [path,title,key,test,value] of cases){
  await ready(path,test);if(test&&await page.getByTestId(test).innerText()!==value)throw Error(key+' KPI changed');
  for(const [width,height] of [[1440,1000],[1280,900]]){
   await page.setViewportSize({width,height});await page.evaluate(()=>window.scrollTo(0,0));await page.waitForTimeout(250);
   const layout=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth,clippedKpis:[...document.querySelectorAll('.kpi-value,.kpi-label')].some(e=>e.scrollWidth>e.clientWidth),visibleChars:document.querySelector('main').innerText.length,h1:parseFloat(getComputedStyle(document.querySelector('h1')).fontSize)}));
   if(layout.overflow||layout.clippedKpis)throw Error(key+' layout overflow');
   const mainText=await page.locator('main').innerText();if(/\bP[0-4]\b|\bV2\b|SHA-256|\d+ passed/.test(mainText))throw Error(key+' shows developer text by default');
   await page.screenshot({path:`docs/screenshots/ui-copy/${key}-${width}.png`});await page.screenshot({path:`docs/screenshots/ui-copy/${key}-${width}-full.png`,fullPage:true});result.pages.push({path,title,width,height,...layout});
  }
  await page.setViewportSize({width:1440,height:1000});
  if(path==='/users'){
   const notes=page.locator('.metric-notes');if(await notes.locator(':scope[open]').count())throw Error('Method notes default open');
   await page.getByTestId('cohort-null-count').locator('xpath=ancestor::details').locator('summary').click();if(!(await page.getByTestId('cohort-null-count').innerText()).includes('298'))throw Error('NULL changed');
   result.evidence_preserved.push('RFM/Cohort方法与298个NULL');
   await page.getByLabel('导出内容',{exact:true}).selectOption('cohort');await download(page.getByRole('button',{name:'导出 CSV',exact:true}),'users-cohort.csv');
  }
  if(path==='/findings'){
   if(await page.locator('.finding-card').count()!==7||await page.locator('.finding-card > details[open]').count())throw Error('Findings structure');
   const api=await(await page.request.get(base+'/api/evidence/findings')).json();
   for(const f of api.findings){const detail=page.getByTestId('evidence-'+f.id);await detail.locator(':scope > summary').click();const full=await detail.locator(':scope > .finding-result').innerText();if(full!==f.result)throw Error('Evidence result changed '+f.id);if(!await detail.getByText(f.method,{exact:true}).count()||!await detail.getByText(f.limitations,{exact:true}).count()||!await detail.getByText(f.suggestion,{exact:true}).count())throw Error('Evidence omitted '+f.id);result.evidence_preserved.push(f.id);await detail.locator(':scope > summary').click()}
   const proof=page.getByTestId('evidence-F05');await proof.locator(':scope > summary').click();await page.getByTestId('mean-ci').waitFor();if(await page.getByTestId('mean-ci').innerText()!=='[-2.0575, -1.9800]')throw Error('CI changed');
   const svg=page.getByRole('img',{name:'全样本逾期与评价均分',exact:true});await svg.scrollIntoViewIfNeeded();await page.waitForTimeout(300);if((await svg.boundingBox()).width<400)throw Error('Expanded chart not resized');await proof.screenshot({path:'docs/screenshots/ui-copy/findings-evidence.png'});
   await page.getByLabel('分析专题',{exact:true}).selectOption('履约体验');if(await page.locator('.finding-card').count()!==1)throw Error('Topic filter');await page.getByLabel('分析专题',{exact:true}).selectOption('全部专题');await download(page.getByRole('button',{name:'下载 Markdown 报告',exact:true}),'report.md');
  }
  if(path==='/quality'){
   if(await page.getByRole('table',{name:'九张原始表当前与历史记录数',exact:true}).locator('tbody tr').count()!==9)throw Error('Raw counts');
   const audit=page.locator('main > details').filter({has:page.locator(':scope > summary').filter({hasText:'缺失与重复 · 历史审计'})});
   await page.getByText('缺失与重复 · 历史审计',{exact:true}).first().click();
   if(!await page.getByText('执行时间：未记录',{exact:true}).count())throw Error('Unrecorded audit time lost');
   await page.getByLabel('字段缺失范围',{exact:true}).selectOption('order_items');if(!(await page.getByRole('table',{name:'P0历史字段缺失',exact:true}).innerText()).includes('当前范围没有可展示的结果。'))throw Error('Missing field empty state');
   await download(page.getByRole('button',{name:'下载 JSON',exact:true}),'quality.json');result.evidence_preserved.push('当前/历史区分及未知审计时间');
  }
 }
 for(const [path,title] of cases){const navTitle=path==='/products'?'商品与品类':path==='/delivery'?'履约与评价':title;await page.getByRole('link',{name:navTitle,exact:true}).click();await page.getByRole('heading',{name:title,exact:true}).waitFor()}
 await page.goBack();await page.getByRole('heading',{name:'经营发现',exact:true}).waitFor();await page.goForward();await page.getByRole('heading',{name:'数据质量中心',exact:true}).waitFor();result.navigation=true;
 for(const key of ['products','delivery']){
  await ready('/'+key,'analysis-kpi-0');await page.getByLabel('开始日期',{exact:true}).fill('2017-05-10');await page.getByLabel('结束日期',{exact:true}).fill('2017-06-20');await page.getByLabel('客户州',{exact:true}).selectOption('SP');await page.getByLabel('商品类目',{exact:true}).selectOption('beleza_saude');await page.getByRole('button',{name:'应用筛选',exact:true}).click();
  await page.waitForFunction(({key})=>document.querySelector(`[data-testid="analysis-kpi-${key==='products'?0:3}"]`)?.textContent===(key==='products'?'BRL 15,182.76':'135'),{key});
  await download(page.getByRole('button',{name:'导出 CSV',exact:true}),key+'-filtered.csv');
  await page.getByLabel('结束日期',{exact:true}).fill('2020-01-02');await page.getByLabel('开始日期',{exact:true}).fill('2020-01-01');await page.getByRole('button',{name:'应用筛选',exact:true}).click();await page.locator('.empty-notice').waitFor();await page.getByRole('button',{name:'重置',exact:true}).click();await page.getByTestId('analysis-kpi-0').waitFor();result.filters.push({page:key,filtered:true,empty:true,reset:true});
 }
 await ready('/','kpi-0');await page.getByLabel('开始日期',{exact:true}).fill('2017-05-10');await page.getByLabel('结束日期',{exact:true}).fill('2017-06-20');await page.getByRole('button',{name:'筛选客户州 SP',exact:true}).click();await page.waitForFunction(()=>document.querySelector('[data-testid="kpi-0"]')?.textContent==='BRL 250,817.27');await download(page.getByRole('button',{name:'导出 CSV',exact:true}),'overview-filtered.csv');await page.getByRole('button',{name:'重置',exact:true}).click();await page.waitForFunction(()=>document.querySelector('[data-testid="kpi-0"]')?.textContent==='BRL 13,221,498.11');
 result.overview_draft_and_reset=true;
 for(const [path,,key,test] of cases){
  await ready(path,test);const endpoint=path==='/'?'**/api/overview?*':key==='findings'?'**/api/evidence/findings':key==='quality'?'**/api/evidence/quality':`**/api/analysis/${key}?*`;
  await page.route(endpoint,r=>r.fulfill({status:503,contentType:'application/json',body:'{"detail":"unavailable"}'}));await page.getByRole('button',{name:'刷新数据',exact:true}).click();await page.getByRole('button',{name:'重新连接',exact:true}).waitFor();await page.unroute(endpoint);
  await page.route(endpoint,async r=>{await new Promise(resolve=>setTimeout(resolve,800));await r.continue()});await page.getByRole('button',{name:'重新连接',exact:true}).click();await page.getByLabel(path==='/'?'正在加载经营数据':'正在加载分析数据',{exact:true}).waitFor();if(test)await page.getByTestId(test).waitFor();else if(key==='findings')await page.locator('.finding-card').first().waitFor();else await page.locator('.trust-status').waitFor();await page.unroute(endpoint);
 }
 result.loading_error_recovery=true;result.page_errors=errors;await ready('/','kpi-0');return result;
}
