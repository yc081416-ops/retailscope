async(page)=>{
  const result={pages:[]};const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const assets=[];const api=[];
  page.on('request',r=>{if(r.url().includes('/assets/')&&r.url().split('?')[0].endsWith('.js'))assets.push(r.url());if(r.url().includes('/api/'))api.push(r.url())});
  await page.setViewportSize({width:1440,height:1000});
  await page.goto('http://127.0.0.1:5174/');await page.getByTestId('kpi-0').waitFor();
  await page.getByRole('img',{name:'月度商品成交额与订单趋势',exact:true}).locator('svg').waitFor();
  result.home_loaded_assets=[...assets];
  if(assets.some(url=>/\/(Users|Products|Delivery)-/.test(url)))throw new Error('Other page chunks eagerly loaded on overview');
  if(api.some(url=>url.includes('/api/analysis/')))throw new Error('Hidden analytical pages queried on home');
  await page.getByLabel('开始日期',{exact:true}).fill('2017-05-10');await page.getByLabel('结束日期',{exact:true}).fill('2017-06-20');
  if(!await page.getByText('更改待应用',{exact:true}).isVisible())throw new Error('Draft lost pending state');
  const scoped=page.waitForResponse(r=>r.url().includes('/api/overview?')&&r.url().includes('state=SP')&&r.status()===200);
  await page.getByRole('button',{name:'筛选客户州 SP',exact:true}).click();
  const scope=(await (await scoped).json()).scope;await page.getByTestId('kpi-0').waitFor();
  if(scope.start!=='2017-05-10'||scope.end!=='2017-06-20')throw new Error('Region click overwrote draft dates');
  result.overview_draft_preserved=scope;
  await page.getByRole('button',{name:'当前范围完整月',exact:true}).click();
  if(!await page.getByTestId('month-count').innerText().then(t=>t.includes('显示 0 / 2')))throw new Error('Partial dates should have no complete months');
  await page.getByText('当前视图没有可展示的月份，请查看全部月份或调整筛选',{exact:true}).waitFor();
  result.overview_local_complete_months=0;
  await page.getByRole('button',{name:'重置',exact:true}).click();await page.waitForFunction(()=>document.querySelector('[data-testid="kpi-0"]')?.textContent==='BRL 13,221,498.11');
  await page.getByRole('button',{name:'当前范围全部月',exact:true}).click();
  const cases=[['/users','用户价值分析','users',['93,358','2,801','3.0003%','96.9997%'],4],
    ['/products','商品与品类','products',['BRL 13,221,498.11','110,197','96,478','BRL 2,198,275.64'],4],
    ['/delivery','履约与评价','delivery',['12.56 天','6.7731%','4.16','96,478'],4]];
  for(const [path,title,key,expected,charts] of cases){
    await page.getByRole('link',{name:title,exact:true}).click();await page.getByTestId('analysis-kpi-0').waitFor();
    await page.waitForFunction(n=>document.querySelectorAll('[role="img"] svg').length===n,charts);
    const metrics=await Promise.all([0,1,2,3].map(i=>page.getByTestId(`analysis-kpi-${i}`).innerText()));
    if(JSON.stringify(metrics)!==JSON.stringify(expected))throw new Error(`${key} KPI mismatch ${metrics}`);
    if(key==='users'){
      if(await page.getByLabel('开始日期',{exact:true}).count())throw new Error('Fixed users must not show fake local filters');
      await page.getByTestId('cohort-null-count').waitFor();if(!(await page.getByTestId('cohort-null-count').innerText()).includes('298'))throw new Error('Cohort NULL lost');
      const heatmap=page.getByRole('img',{name:'Cohort回购活跃留存热力图',exact:true});await heatmap.scrollIntoViewIfNeeded();
      await page.screenshot({path:'docs/screenshots/v2-02/users-cohort.png'});
      await page.getByLabel('导出内容',{exact:true}).selectOption('cohort');await page.getByRole('button',{name:'导出 CSV',exact:true}).scrollIntoViewIfNeeded();await page.waitForTimeout(200);const event=page.waitForEvent('download');await page.getByRole('button',{name:'导出 CSV',exact:true}).click();await (await event).saveAs('reports/v2-02/users-cohort.csv');
    }
    for(const [width,height] of [[1440,1000],[1280,900]]){
      await page.setViewportSize({width,height});await page.evaluate(()=>window.scrollTo(0,0));await page.waitForTimeout(300);
      const layout=await page.evaluate(()=>({horizontalOverflow:document.documentElement.scrollWidth>innerWidth,
        clippedKpis:Array.from(document.querySelectorAll('.kpi-value,.kpi-label')).some(e=>e.scrollWidth>e.clientWidth),
        activeNav:document.querySelector('nav a[aria-current="page"]')?.textContent,
        chartCount:document.querySelectorAll('[role="img"] svg').length}));
      if(layout.horizontalOverflow||layout.clippedKpis)throw new Error(`${key} ${width} layout overflow ${JSON.stringify(layout)}`);
      await page.screenshot({path:`docs/screenshots/v2-02/${key}-${width}.png`});
      await page.screenshot({path:`docs/screenshots/v2-02/${key}-${width}-full.png`,fullPage:true});
      result.pages.push({key,width,height,metrics,...layout});
    }
    await page.setViewportSize({width:1440,height:1000});
    if(key!=='users'){
      await page.getByLabel('开始日期',{exact:true}).fill('2017-05-10');await page.getByLabel('结束日期',{exact:true}).fill('2017-06-20');await page.getByLabel('客户州',{exact:true}).selectOption('SP');await page.getByLabel('商品类目',{exact:true}).selectOption('beleza_saude');
      const event=page.waitForResponse(r=>r.url().includes(`/api/analysis/${key}?`)&&r.url().includes('start=2017-05-10')&&r.status()===200);
      if(key==='products')await page.getByRole('button',{name:'筛选类目 beleza_saude',exact:true}).click();else await page.getByRole('button',{name:'应用筛选',exact:true}).click();const filtered=await (await event).json();await page.getByTestId('analysis-kpi-0').waitFor();
      result[`${key}_filtered`]={scope:filtered.scope,kpis:await Promise.all([0,1,2,3].map(i=>page.getByTestId(`analysis-kpi-${i}`).innerText()))};
      if(key==='products'){
        result.products_selected_orders=filtered.kpis[0].orders;
        await page.getByRole('img',{name:'品类帕累托累计贡献',exact:true}).scrollIntoViewIfNeeded();await page.screenshot({path:'docs/screenshots/v2-02/products-pareto.png'});
      }else{
        await page.getByRole('img',{name:'逾期与订单评价关联',exact:true}).scrollIntoViewIfNeeded();await page.screenshot({path:'docs/screenshots/v2-02/delivery-association.png'});
      }
      await page.getByRole('button',{name:'导出 CSV',exact:true}).scrollIntoViewIfNeeded();await page.waitForTimeout(200);
      const download=page.waitForEvent('download');await page.getByRole('button',{name:'导出 CSV',exact:true}).click();await (await download).saveAs(`reports/v2-02/${key}-filtered.csv`);
      await page.getByLabel('结束日期',{exact:true}).fill('2020-01-02');await page.getByLabel('开始日期',{exact:true}).fill('2020-01-01');await page.getByRole('button',{name:'应用筛选',exact:true}).click();
      await page.getByText(key==='products'?'当前日期、地区与类目组合没有有效商品明细，请调整或重置筛选。':'当前筛选没有有效订单，请调整日期、地区或类目。',{exact:true}).waitFor();
      result[`${key}_empty_verified`]=true;await page.screenshot({path:`output/playwright/v2-02/${key}-empty.png`});
      await page.getByRole('button',{name:'重置',exact:true}).click();await page.waitForFunction(({key})=>document.querySelector('[data-testid="analysis-kpi-0"]')?.textContent===(key==='products'?'BRL 13,221,498.11':'12.56 天'),{key});
    }
    if(key==='users'){
      const fixed=await (await page.request.get('http://127.0.0.1:5174/api/analysis/users')).json();
      await page.route('**/api/analysis/users?*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({...fixed,summary:[]})}));
      await page.getByRole('button',{name:'刷新数据',exact:true}).click();await page.getByText('用户分析暂无可用汇总，请核对P1数据仓库。不会用模拟分层或留存填充。',{exact:true}).waitFor();
      result.users_empty_verified=true;await page.screenshot({path:'output/playwright/v2-02/users-empty.png'});await page.unroute('**/api/analysis/users?*');
      await page.getByRole('button',{name:'刷新数据',exact:true}).click();await page.getByTestId('analysis-kpi-0').waitFor();
    }
    await page.route(`**/api/analysis/${key}?*`,route=>route.fulfill({status:503,contentType:'application/json',body:'{"detail":"unavailable"}'}));
    await page.getByRole('button',{name:'刷新数据',exact:true}).click();await page.getByRole('button',{name:'重新连接',exact:true}).waitFor();
    if(await page.getByTestId('analysis-kpi-0').count())throw new Error(`${key} showed stale KPI on failure`);
    result[`${key}_error_verified`]=true;await page.screenshot({path:`output/playwright/v2-02/${key}-error.png`});await page.unroute(`**/api/analysis/${key}?*`);
    await page.getByRole('button',{name:'重新连接',exact:true}).click();await page.getByTestId('analysis-kpi-0').waitFor();
  }
  await page.getByRole('link',{name:'用户价值分析',exact:true}).click();await page.getByTestId('analysis-kpi-0').waitFor();
  if(await page.getByTestId('analysis-kpi-0').innerText()!=='93,358')throw new Error('Local filters leaked into fixed users');
  await page.goBack();await page.getByRole('heading',{name:'履约与评价分析',exact:true}).waitFor();result.history_navigation_verified=true;
  result.page_errors=errors;return result;
}
