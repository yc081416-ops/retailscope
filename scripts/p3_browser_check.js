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
  for(const [title,filename,plots,metrics,ending] of definitions){
    await page.getByRole('link',{name:title,exact:true}).click();
    await page.getByRole('heading',{name:title,exact:true,level:1}).waitFor();
    await page.getByText(ending,{exact:true}).waitFor();
    if(['经营总览','商品与品类分析','履约与评价分析'].includes(title)){
      await page.getByRole('button',{name:'清空筛选',exact:true}).click();
      await page.waitForTimeout(800);
    }
    if(metrics){
      await page.waitForFunction(({metrics,plots})=>{
        const actual=Array.from(document.querySelectorAll('[data-testid="stMetricValue"]')).map(el=>el.textContent);
        return JSON.stringify(actual)===JSON.stringify(metrics)&&document.querySelectorAll('.js-plotly-plot').length===plots;
      },{metrics,plots});
    }else{
      await page.getByText('F07 · 留存分析必须保留不可观察月份',{exact:true}).waitFor();
    }
    await page.waitForTimeout(1000); // Let widget paint settle after a no-op reset with unchanged KPI values.
    await page.locator('[data-testid="stMain"]').evaluate(el=>el.scrollTop=0);
    await page.screenshot({path:`output/playwright/p3/${filename}.png`});
    const state=await page.evaluate(()=>({
      metrics:Array.from(document.querySelectorAll('[data-testid="stMetricValue"]')).map(el=>el.textContent),
      charts:document.querySelectorAll('.js-plotly-plot').length,
      exceptions:document.querySelectorAll('[data-testid="stException"]').length,
      horizontalOverflow:document.documentElement.scrollWidth>innerWidth,
      placeholder:document.querySelector('input[role="combobox"]')?.placeholder,
    }));
    if(state.exceptions||state.horizontalOverflow)throw new Error(`Page failed: ${title}`);
    result.pages.push({title,...state});
    if(title==='经营总览'){
      result.axes=await page.locator('.js-plotly-plot').first().evaluate(el=>({amount:el.layout.yaxis.range,orders:el.layout.yaxis2.range}));
      if(result.axes.amount[0]!==0||result.axes.orders[0]!==0)throw new Error('Axes must start at zero');
      if(state.placeholder!=='请选择（留空为全部）')throw new Error('Filter placeholder is not Chinese');
    }
    if(title==='经营发现'){
      const event=page.waitForEvent('download');
      await page.getByRole('button',{name:'下载 P3 经营诊断报告（Markdown）',exact:true}).click();
      const download=await event;
      await download.saveAs('output/playwright/p3/downloaded_P3_BUSINESS_REPORT.md');
      result.download=download.suggestedFilename();
      await page.getByText('F05 · 逾期与评价存在描述性差异',{exact:true}).click();
      await page.getByText('F05 · 逾期与评价存在描述性差异',{exact:true}).scrollIntoViewIfNeeded();
      await page.screenshot({path:'output/playwright/p3/07-association-finding.png'});
      await page.getByText('查看配送与评价差异及95%区间',{exact:true}).click();
      await page.getByText('查看配送与评价差异及95%区间',{exact:true}).scrollIntoViewIfNeeded();
      await page.screenshot({path:'output/playwright/p3/08-statistical-details.png'});
      await page.getByText('查看完整月趋势与稳健异常筛查',{exact:true}).click();
      await page.getByText('查看完整月趋势与稳健异常筛查',{exact:true}).scrollIntoViewIfNeeded();
      await page.screenshot({path:'output/playwright/p3/09-trend-diagnostics.png'});
    }
  }
  await page.getByRole('link',{name:'经营总览',exact:true}).click();
  await page.getByText('指标说明与历史观察范围',{exact:true}).waitFor();
  await page.setViewportSize({width:1280,height:900});
  await page.locator('[data-testid="stMain"]').evaluate(el=>el.scrollTop=0);
  await page.screenshot({path:'output/playwright/p3/10-desktop-1280.png'});
  await page.setViewportSize({width:1440,height:1000});
  return result;
}
