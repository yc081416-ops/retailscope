async(page)=>{
 await page.goto('http://127.0.0.1:5174/products');const chart=page.getByRole('img',{name:'品类月度金额趋势',exact:true});await chart.locator('svg').waitFor();await chart.scrollIntoViewIfNeeded();
 const legend=chart.locator('svg text').filter({hasText:/^beleza_saude$/});await legend.waitFor();await page.waitForTimeout(600);const before=await legend.getAttribute('fill');
 const click=async()=>{const b=await legend.boundingBox();await page.mouse.move(b.x+b.width/2,b.y+b.height/2);await page.waitForTimeout(150);await page.mouse.down();await page.waitForTimeout(100);await page.mouse.up();await page.mouse.move(10,10);await page.waitForTimeout(600)};
 await click();const after=await legend.getAttribute('fill');
 if(before===after)throw Error('Legend toggle did not change selection');await click();if(await legend.getAttribute('fill')!==before)throw Error('Legend did not restore');
 await page.screenshot({path:'output/playwright/v2-04/products-legend.png'});await page.goto('http://127.0.0.1:5174/');await page.getByTestId('kpi-0').waitFor();
 return {legend_visible:true,legend_click_toggles:true,restored:true,before,after,userAgent:await page.evaluate(()=>navigator.userAgent)};
}
