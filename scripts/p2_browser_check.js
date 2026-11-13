async (page) => {
  const evidence = {pages: [], interactions: []};
  const definitions = [
    ['经营总览', '01-overview', 3], ['用户价值分析', '02-users', 5],
    ['商品与品类分析', '03-products', 5], ['履约与评价分析', '04-delivery', 4],
    ['经营发现', '05-findings', 0], ['数据质量中心', '06-quality', 0],
  ];
  const expectedMetrics = {
    '经营总览':['BRL 13,221,498.11','96,478','93,358','BRL 137.04'],
    '用户价值分析':['93,358','2,801','3.0003%','96.9997%'],
    '商品与品类分析':['BRL 13,221,498.11','110,197','96,478','BRL 2,198,275.64'],
    '履约与评价分析':['12.56 天','6.7731%','4.16','96,478'],
    '经营发现':[], '数据质量中心':['9','1,550,922','通过'],
  };
  for (const [title, filename, expectedPlots] of definitions) {
    await page.getByRole('link', {name: title, exact: true}).click();
    await page.getByRole('heading', {name: title, exact: true, level: 1}).waitFor();
    if (expectedPlots) {
      await page.locator('.js-plotly-plot').nth(expectedPlots - 1).waitFor();
    } else {
      await page.getByText(title === '经营发现' ? 'P3 才进一步开发系统化经营诊断' : '核心指标计算说明', {exact:false}).waitFor();
    }
    const endings={
      '经营总览':'指标说明与历史观察范围','用户价值分析':'每月观测新增购买用户',
      '商品与品类分析':'TOP 10 品类 · 件数与订单数','履约与评价分析':'逾期与评价 · 描述性关联',
    };
    if(endings[title]) await page.getByText(endings[title],{exact:true}).waitFor();
    if(['经营总览','商品与品类分析','履约与评价分析'].includes(title)) {
      await page.getByRole('button',{name:'清空筛选',exact:true}).click();
      await page.waitForTimeout(1000);
    }
    await page.waitForFunction(({metrics,plots}) => {
      const actual=Array.from(document.querySelectorAll('[data-testid="stMetricValue"]')).map(el=>el.textContent);
      return JSON.stringify(actual)===JSON.stringify(metrics) && document.querySelectorAll('.js-plotly-plot').length===plots;
    }, {metrics:expectedMetrics[title],plots:expectedPlots});
    await page.locator('[data-testid="stMain"]').evaluate(el => el.scrollTop = 0);
    await page.screenshot({path: `output/playwright/${filename}.png`});
    const state = await page.evaluate(() => ({
      plots: document.querySelectorAll('.js-plotly-plot').length,
      metrics: Array.from(document.querySelectorAll('[data-testid="stMetricValue"]')).map(el => el.textContent),
      horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth,
      exceptions: document.querySelectorAll('[data-testid="stException"]').length,
    }));
    if (state.exceptions || state.plots < expectedPlots) throw new Error(`Incomplete page: ${title}`);
    evidence.pages.push({title, ...state});
    if (title === '用户价值分析') {
      const nulls = await page.locator('.js-plotly-plot').evaluateAll(plots => {
        const heatmap = plots.map(p => p.data?.[0]).find(t => t?.type === 'heatmap');
        return heatmap.z.flat().filter(v => v === null || Number.isNaN(v)).length;
      });
      if (nulls !== 298) throw new Error(`Cohort NULL mismatch: ${nulls}`);
      evidence.interactions.push({cohort_unobserved_cells: nulls});
      await page.getByRole('heading', {name:'Cohort 月度回购活跃留存', exact:true}).scrollIntoViewIfNeeded();
      await page.screenshot({path:'output/playwright/02-cohort.png'});
    }
  }
  // Actual category/state interaction; the table download uses this same query result.
  await page.getByRole('link', {name:'商品与品类分析', exact:true}).click();
  await page.getByRole('button', {name:'清空筛选', exact:true}).click();
  await page.waitForTimeout(1000); // Allow the reset callback to commit before editing a new widget.
  await page.getByRole('combobox', {name:'客户州 · 留空为全部'}).fill('SP');
  await page.waitForTimeout(500);
  await page.getByRole('option', {name:'SP', exact:true}).click();
  await page.keyboard.press('Escape');
  await page.getByText('州：SP · 类目：全部', {exact:false}).waitFor();
  await page.waitForTimeout(800);
  await page.getByRole('combobox', {name:'商品类目 · 留空为全部'}).fill('beleza_saude');
  await page.waitForTimeout(500);
  await page.getByRole('option', {name:'beleza_saude', exact:true}).click();
  await page.keyboard.press('Escape');
  await page.getByText('州：SP · 类目：beleza_saude', {exact:false}).waitFor();
  await page.waitForFunction(() => document.querySelector('[data-testid="stMetricValue"]')?.textContent==='BRL 453,916.48');
  await page.waitForTimeout(250);
  await page.getByRole('heading', {name:'帕累托累计贡献', exact:true}).waitFor();
  const filteredMetrics = await page.locator('[data-testid="stMetricValue"]').allTextContents();
  await page.getByText('全部类目排行与当前范围导出', {exact:true}).click();
  const downloadEvent = page.waitForEvent('download');
  await page.getByRole('button', {name:'下载 CSV · category_ranking', exact:true}).click();
  const download = await downloadEvent;
  await download.saveAs('output/playwright/filtered-category.csv');
  evidence.interactions.push({filter:'SP / beleza_saude', metrics:filteredMetrics, download:download.suggestedFilename()});
  await page.locator('[data-testid="stMain"]').evaluate(el => el.scrollTop = 0);
  await page.screenshot({path:'output/playwright/07-filtered-products.png'});
  await page.getByRole('button', {name:'清空筛选', exact:true}).click();
  await page.getByText('BRL 13,221,498.11', {exact:true}).first().waitFor();
  evidence.interactions.push({reset_restored_full_sample: true});
  await page.getByRole('link', {name:'经营总览', exact:true}).click();
  await page.getByRole('heading', {name:'月度商品金额与有效订单', exact:true}).waitFor();
  await page.waitForFunction(() => document.querySelectorAll('.js-plotly-plot').length===3 && document.querySelector('[data-testid="stMetricValue"]')?.textContent==='BRL 13,221,498.11');
  await page.setViewportSize({width:1280,height:900});
  await page.locator('[data-testid="stMain"]').evaluate(el => el.scrollTop = 0);
  await page.screenshot({path:'output/playwright/08-desktop-1280.png'});
  await page.setViewportSize({width:1440,height:1000});
  return evidence;
}
