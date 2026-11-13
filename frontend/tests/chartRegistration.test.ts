import {expect,it} from 'vitest'
import * as echarts from 'echarts/core'
import '../src/Chart'

it('renders and toggles the configured category legend with on-demand registration',()=>{
 const chart=echarts.init(null,undefined,{renderer:'svg',ssr:true,width:800,height:350})
 try{
  chart.setOption({legend:{type:'scroll'},xAxis:{type:'category',data:[]},yAxis:{},
   series:[{name:'beleza_saude',type:'line',data:[]}]})
  expect(chart.renderToSVGString()).toContain('beleza_saude')
  chart.dispatchAction({type:'legendToggleSelect',name:'beleza_saude'})
  const option=chart.getOption() as {legend:{selected:Record<string,boolean>}[]}
  expect(option.legend[0].selected.beleza_saude).toBe(false)
 }finally{chart.dispose()}
})
