async(page)=>{
  const result={};const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.setViewportSize({width:1440,height:1000});
  await page.route('**/api/overview?*',async route=>{await new Promise(r=>setTimeout(r,700));await route.continue()});
  await page.reload();await page.getByLabel('正在加载经营数据').waitFor();result.loading_verified=true;
  await page.getByTestId('kpi-0').waitFor();await page.unroute('**/api/overview?*');
  await page.locator('.reading-result').waitFor();
  const response=await page.request.get('http://127.0.0.1:8000/api/overview');const full=await response.json();
  const facts=await (await page.request.get('http://127.0.0.1:8000/api/findings')).json();
  const metrics=async()=>Promise.all([0,1,2,3].map(i=>page.getByTestId(`kpi-${i}`).innerText()));
  const baseline=['BRL 13,221,498.11','96,478','93,358','BRL 137.04'];
  result.baseline=await metrics();if(JSON.stringify(result.baseline)!==JSON.stringify(baseline))throw new Error('KPI mismatch');
  if(await page.locator('.avatar,.version,.legacy').count())throw new Error('Display-only identity/legacy links remain');
  if(await page.getByText('SQL 实时查询',{exact:true}).count())throw new Error('Misleading real-time claim');
  if(await page.locator('nav[aria-label="分析模块"] button:disabled').count()!==4)throw new Error('Reserved modules must be visibly disabled');
  result.reserved_modules_disabled=4;
  if((await page.locator('.reading-result').innerText())!==facts.findings.find(f=>f.id==='F01').result)throw new Error('P3 reading changed');
  result.fixed_reading_matches_p3=true;
  result.sizes=[];
  for(const [width,height] of [[1440,1000],[1280,900]]){
    await page.setViewportSize({width,height});await page.waitForTimeout(350);await page.evaluate(()=>window.scrollTo(0,0));
    const layout=await page.evaluate(()=>{
      const style=s=>getComputedStyle(document.querySelector(s));
      const lum=rgb=>{const x=rgb.match(/[\d.]+/g).slice(0,3).map(n=>{const c=Number(n)/255;return c<=.04045?c/12.92:((c+.055)/1.055)**2.4});return .2126*x[0]+.7152*x[1]+.0722*x[2]};
      const secondary=style('.page-heading p').color;
      return {horizontalOverflow:document.documentElement.scrollWidth>innerWidth,
        clippedKpis:Array.from(document.querySelectorAll('.kpi-value,.kpi-label,.kpi p')).some(e=>e.scrollWidth>e.clientWidth),
        titleSize:parseFloat(style('h1').fontSize),navSize:parseFloat(style('.nav-link').fontSize),bodySize:parseFloat(style('.page-heading p').fontSize),
        importantNoteSize:parseFloat(style('.metric-footnote').fontSize),auxiliarySize:parseFloat(style('.source-line').fontSize),
        chartLabelSizes:[...new Set(Array.from(document.querySelectorAll('[role="img"] svg text')).map(e=>parseFloat(getComputedStyle(e).fontSize)))],
        secondaryContrastOnWhite:1.05/(lum(secondary)+.05),trendTop:document.querySelector('.trend-panel').getBoundingClientRect().top};
    });
    if(layout.horizontalOverflow||layout.clippedKpis||layout.titleSize<28||layout.navSize<14||layout.bodySize<14||layout.importantNoteSize<13||layout.auxiliarySize<12||layout.chartLabelSizes.some(n=>n<12)||layout.secondaryContrastOnWhite<4.5)throw new Error(`Typography/layout failure ${JSON.stringify(layout)}`);
    result.sizes.push({width,height,...layout});
    await page.screenshot({path:`docs/screenshots/v2-01-1/overview-${width}.png`});
    await page.screenshot({path:`docs/screenshots/v2-01-1/overview-${width}-full.png`,fullPage:true});
  }
  await page.setViewportSize({width:1440,height:1000});
  const complete=full.monthly.filter(r=>r.is_complete).length;
  await page.getByRole('button',{name:'完整月份',exact:true}).click();
  await page.waitForTimeout(150);
  if(!await page.getByTestId('month-count').innerText().then(t=>t.includes(`显示 ${complete} / ${full.monthly.length}`)))throw new Error('Month view count incorrect');
  if(JSON.stringify(await metrics())!==JSON.stringify(baseline))throw new Error('Month view must not alter KPI scope');
  result.complete_months=complete;result.all_months=full.monthly.length;
  await page.getByRole('button',{name:'全部月份',exact:true}).click();
  const chart=page.getByRole('img',{name:'月度商品成交额与订单趋势',exact:true});
  await chart.scrollIntoViewIfNeeded();
  const box=await chart.boundingBox();
  await page.mouse.move(box.x+box.width*.62,box.y+65);await page.waitForTimeout(400);
  const tooltip=await chart.locator('div').filter({hasText:'商品成交额'}).allTextContents();
  result.tooltip_visible=tooltip.some(t=>t.includes('BRL')&&t.includes('有效订单')&&t.includes('观察月'));
  if(!result.tooltip_visible)throw new Error('Real chart tooltip not visible');
  await page.screenshot({path:'docs/screenshots/v2-01-1/trend-tooltip.png'});await page.mouse.move(10,10);
  const regionResponse=page.waitForResponse(r=>r.url().includes('/api/overview?')&&r.url().includes('state=SP')&&r.status()===200);
  await page.getByRole('button',{name:'筛选客户州 SP',exact:true}).click();
  const sp=await (await regionResponse).json();await page.getByTestId('kpi-0').waitFor();
  if(sp.scope.state!=='SP'||await page.getByLabel('客户州',{exact:true}).inputValue()!=='SP')throw new Error('Region click did not apply real filter');
  await page.getByText('当前为局部筛选。以下发现仍为固定全样本，不代表当前日期或地区的趋势；请以当前筛选图表为准。',{exact:true}).waitFor();
  result.region_click_orders=sp.kpis.orders;result.local_reading_explicit=true;
  await page.getByLabel('开始日期',{exact:true}).fill('2017-05-10');await page.getByLabel('结束日期',{exact:true}).fill('2017-06-20');
  if(!await page.getByText('更改待应用',{exact:true}).isVisible())throw new Error('Pending state missing');
  const filteredResponse=page.waitForResponse(r=>r.url().includes('start=2017-05-10')&&r.url().includes('/api/overview?')&&r.status()===200);
  await page.getByRole('button',{name:'应用筛选',exact:true}).click();const filtered=await (await filteredResponse).json();await page.getByTestId('kpi-0').waitFor();
  result.filtered_scope=filtered.scope;result.filtered_kpis=await metrics();
  if(result.filtered_kpis[0]!=='BRL 250,817.27'||result.filtered_kpis[1]!=='1,900')throw new Error('Filtered metrics wrong');
  if((await page.locator('.reading-result').innerText())!==facts.findings.find(f=>f.id==='F01').result)throw new Error('Fixed scope reading changed after local filter');
  await page.screenshot({path:'docs/screenshots/v2-01-1/filtered-overview.png',fullPage:true});
  await page.getByRole('button',{name:'导出 CSV',exact:true}).scrollIntoViewIfNeeded();
  await page.waitForTimeout(200);
  const event=page.waitForEvent('download');await page.getByRole('button',{name:'导出 CSV',exact:true}).click();await (await event).saveAs('reports/v2-01-1/filtered-monthly.csv');
  result.export_downloaded=true;
  await page.getByLabel('结束日期',{exact:true}).fill('2020-01-02');await page.getByLabel('开始日期',{exact:true}).fill('2020-01-01');
  await page.getByRole('button',{name:'应用筛选',exact:true}).click();await page.getByText('当前范围没有有效订单',{exact:true}).waitFor();
  result.empty_kpis=await metrics();
  await page.getByRole('button',{name:'完整月份',exact:true}).click();await page.getByText('当前视图没有可展示的月份，请查看全部月份或调整筛选',{exact:true}).waitFor();
  await page.screenshot({path:'output/playwright/v2-01-1/empty.png',fullPage:true});
  await page.getByRole('button',{name:'全部月份',exact:true}).click();await page.getByRole('button',{name:'重置',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('[data-testid="kpi-0"]')?.textContent==='BRL 13,221,498.11');
  result.reset_restores_baseline=true;
  // Transport-level failure state only; the API/database business logic is unchanged.
  await page.route('**/api/overview?*',route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'unavailable'})}));
  await page.getByRole('button',{name:'刷新数据',exact:true}).click();await page.getByRole('button',{name:'重新连接',exact:true}).waitFor();
  result.failure_message=await page.getByRole('alert').innerText();if(await page.getByTestId('kpi-0').count())throw new Error('Stale KPI after failure');
  await page.screenshot({path:'output/playwright/v2-01-1/error.png'});await page.unroute('**/api/overview?*');
  await page.getByRole('button',{name:'重新连接',exact:true}).click();await page.waitForFunction(()=>document.querySelector('[data-testid="kpi-0"]')?.textContent==='BRL 13,221,498.11');
  await page.getByRole('button',{name:'经营发现',exact:true}).click();await page.locator('.finding').nth(6).waitFor();result.findings=await page.locator('.finding').count();await page.keyboard.press('Escape');
  await page.evaluate(()=>window.scrollTo(0,0));result.page_errors=errors;return result;
}
