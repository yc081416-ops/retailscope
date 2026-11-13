async(page)=>{
  const result={pages:[]};
  const definitions=[
    ['经营总览','01-overview',3,['BRL 13,221,498.11','96,478','93,358','BRL 137.04'],'指标说明与历史观察范围'],
    ['用户价值分析','02-users',5,['93,358','2,801','3.0003%','96.9997%'],'每月观测新增购买用户'],
    ['商品与品类分析','03-products',5,['BRL 13,221,498.11','110,197','96,478','BRL 2,198,275.64'],'TOP 10 品类 · 件数与订单数'],
    ['履约与评价分析','04-delivery',4,['12.56 天','6.7731%','4.16','96,478'],'逾期与评价 · 描述性关联'],
    ['经营发现','05-findings',null,null,'P1 已验收描述性事实'],
    ['数据质量中心','06-quality',0,['9','1,550,922','通过'],'核心指标计算说明'],
  ];
  await page.setViewportSize({width:1440,height:1000});
  for(const [title,file,plots,metrics,last] of definitions){
    await page.getByRole('link',{name:title,exact:true}).click();
    await page.getByRole('heading',{name:title,exact:true,level:1}).waitFor();
    await page.getByText(last,{exact:true}).waitFor();
    if(['经营总览','商品与品类分析','履约与评价分析'].includes(title)){
      await page.getByRole('button',{name:'清空筛选',exact:true}).click();
      await page.waitForTimeout(1000);
    }
    if(metrics) await page.waitForFunction(({metrics,plots})=>JSON.stringify(Array.from(document.querySelectorAll('[data-testid="stMetricValue"]')).map(el=>el.textContent))===JSON.stringify(metrics)&&document.querySelectorAll('.js-plotly-plot').length===plots,{metrics,plots});
    else await page.getByText('F07 · 留存分析必须保留不可观察月份',{exact:true}).waitFor();
    await page.waitForTimeout(1000);
    await page.locator('[data-testid="stMain"]').evaluate(el=>el.scrollTop=0);
    await page.screenshot({path:`docs/screenshots/${file}.png`});
    result.pages.push(await page.evaluate(title=>({title,charts:document.querySelectorAll('.js-plotly-plot').length,
      metrics:Array.from(document.querySelectorAll('[data-testid="stMetricValue"]')).map(el=>el.textContent),
      exceptions:document.querySelectorAll('[data-testid="stException"]').length,horizontalOverflow:document.documentElement.scrollWidth>innerWidth}),title));
    if(title==='经营总览'){
      const height=await page.locator('[data-testid="stMain"]').evaluate(el=>el.scrollHeight);
      await page.setViewportSize({width:1440,height:Math.min(12000,height+100)});
      await page.locator('[data-testid="stMain"]').evaluate(el=>el.scrollTop=0);
      await page.screenshot({path:'docs/screenshots/01-overview-full.png',fullPage:true});
      result.overview_full_capture_height=height+100;
      await page.setViewportSize({width:1440,height:1000});
    }
    if(title==='用户价值分析'){
      await page.locator('[data-testid="stPlotlyChart"]').nth(3).screenshot({path:'docs/screenshots/02-cohort.png'});
      result.cohort_nulls=await page.locator('.js-plotly-plot').nth(3).evaluate(el=>el.data[0].z.flat().filter(v=>v===null||Number.isNaN(v)).length);
    }
    if(title==='商品与品类分析') await page.locator('[data-testid="stPlotlyChart"]').nth(2).screenshot({path:'docs/screenshots/03-pareto.png'});
    if(title==='履约与评价分析') await page.locator('[data-testid="stPlotlyChart"]').nth(3).screenshot({path:'docs/screenshots/04-association.png'});
    if(title==='经营发现'){
      const event=page.waitForEvent('download');
      await page.getByRole('button',{name:'下载 P3 经营诊断报告（Markdown）',exact:true}).click();
      const report=await event; await report.saveAs('reports/p4/downloaded_report.md');
      await page.getByText('查看配送与评价差异及95%区间',{exact:true}).click();
      await page.getByText('查看配送与评价差异及95%区间',{exact:true}).scrollIntoViewIfNeeded();
      await page.waitForTimeout(800);
      await page.screenshot({path:'docs/screenshots/05-confidence.png'});
      result.report_download=report.suggestedFilename();
    }
  }
  await page.getByRole('link',{name:'商品与品类分析',exact:true}).click();
  await page.getByText('TOP 10 品类 · 件数与订单数',{exact:true}).waitFor();
  await page.getByRole('combobox',{name:'客户州 · 留空为全部'}).fill('SP');
  await page.getByRole('option',{name:'SP',exact:true}).click(); await page.keyboard.press('Escape');
  await page.getByText('州：SP · 类目：全部',{exact:false}).waitFor(); await page.waitForTimeout(800);
  await page.getByRole('combobox',{name:'商品类目 · 留空为全部'}).fill('beleza_saude');
  await page.getByRole('option',{name:'beleza_saude',exact:true}).click(); await page.keyboard.press('Escape');
  await page.waitForFunction(()=>document.querySelector('[data-testid="stMetricValue"]')?.textContent==='BRL 453,916.48');
  await page.getByText('全部类目排行与当前范围导出',{exact:true}).click();
  const event=page.waitForEvent('download');
  await page.getByRole('button',{name:'下载 CSV · category_ranking',exact:true}).click();
  const csv=await event; await csv.saveAs('reports/p4/filtered-category.csv');
  result.filtered_metrics=await page.locator('[data-testid="stMetricValue"]').allTextContents();
  await page.getByRole('button',{name:'清空筛选',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('[data-testid="stMetricValue"]')?.textContent==='BRL 13,221,498.11');
  result.reset_restored_full_sample=true;
  await page.getByRole('link',{name:'经营总览',exact:true}).click();
  await page.getByText('指标说明与历史观察范围',{exact:true}).waitFor();
  return result;
}
