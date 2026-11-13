async(page)=>{
 await page.setViewportSize({width:1440,height:1000});await page.goto('http://127.0.0.1:5174/');await page.getByTestId('kpi-0').waitFor();await page.keyboard.press('Control+0');const before=await page.evaluate(()=>({dpr:devicePixelRatio,width:innerWidth}));await page.keyboard.press('Control+Equal');await page.keyboard.press('Control+Equal');await page.waitForTimeout(400);const after=await page.evaluate(()=>({dpr:devicePixelRatio,width:innerWidth}));await page.keyboard.press('Control+0');return {before,after};
}
