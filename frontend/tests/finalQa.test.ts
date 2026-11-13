import {it,expect} from 'vitest'
import {readFileSync} from 'node:fs'
import {categoryLabels,categoryName,categoryMatches,categoryRows,wrapCategoryLabel} from '../src/categories'
import {beijingTime} from '../src/dateTime'
import {cohortOption,retentionLabel} from '../src/usersCharts'
import {horizontal} from '../src/analysisCharts'
import type {Row} from '../src/analysis'

it('covers every raw product category and keeps the official English translation intact',()=>{
 const products=readFileSync(new URL('../../data/raw/olist_products_dataset.csv',import.meta.url),'utf8').trim().split(/\r?\n/).slice(1)
 const codes=new Set(products.map(line=>line.split(',')[1]||'__unknown__'))
 expect([...codes].sort()).toEqual(Object.keys(categoryLabels).sort())
 const official=readFileSync(new URL('../../data/raw/product_category_name_translation.csv',import.meta.url),'utf8').trim().split(/\r?\n/).slice(1)
 for(const line of official){const [code,en]=line.split(',');expect(categoryLabels[code].en).toBe(en)}
 expect(categoryName('__unknown__')).toBe('未分类');expect(categoryName('new_unrecognized')).toBe('未翻译')
 expect(categoryLabels.cool_stuff.status).toBe('preserved_name')
 expect(categoryMatches('beleza_saude','美容')).toBe(true);expect(categoryMatches('beleza_saude','BELEZA')).toBe(true)
 const long=categoryName('moveis_cozinha_area_de_servico_jantar_e_jardim'),lines=wrapCategoryLabel(long).split('\n')
 expect(lines.join('')).toBe(long);expect(lines.every(line=>line.length>1&&line.length<=12)).toBe(true)
 expect(wrapCategoryLabel('美容与健康')).toBe('美容与健康')
})
it('limits and sorts only the visible ranking without mutating contribution denominators',()=>{
 const rows:Row[]=JSON.parse(readFileSync(new URL('../../reports/p1/category_ranking.json',import.meta.url),'utf8'))
 const before=JSON.stringify(rows)
 expect(categoryRows(rows,'','merchandise',false)).toHaveLength(10)
 expect(categoryRows(rows,'','merchandise',true)).toHaveLength(rows.length)
 expect(categoryRows(rows,'美容','merchandise',false)[0].category).toBe('beleza_saude')
 expect(categoryRows(rows,'does_not_exist','items',true)).toHaveLength(0)
 expect(categoryRows(rows,'','name',true).map(r=>categoryName(r.category))).toEqual([...rows].map(r=>categoryName(r.category)).sort((a,b)=>a.localeCompare(b,'zh-CN')))
 expect(JSON.stringify(rows)).toBe(before)
 expect((horizontal(rows.slice(0,10),'category','merchandise') as any).yAxis.axisLabel.overflow).toBe('break')
})
it('converts recorded offsets to Beijing without replacing missing audit times with mtime',()=>{
 expect(beijingTime('2026-11-13T09:38:43.228609+00:00')).toBe('2026-11-13 17:38（北京时间）')
 expect(beijingTime('2026-11-13T17:38:43+08:00')).toBe('2026-11-13 17:38（北京时间）')
 expect(beijingTime(null)).toBe('未记录');expect(beijingTime('2026-11-13T17:38:43')).toContain('时区未记录')
 expect(beijingTime('invalid')).toBe('时间不可用')
})
it('focuses M1–M6 without changing full Cohort values and keeps M0 outside the retention scale',()=>{
 const rows:Row[]=JSON.parse(readFileSync(new URL('../../reports/p1/cohort_retention.json',import.meta.url),'utf8')),before=JSON.stringify(rows)
 const focus=cohortOption(rows,'focus') as any,all=cohortOption(rows) as any
 expect(focus.xAxis.data).toEqual(['M1','M2','M3','M4','M5','M6'])
 expect(all.series[0].data).toHaveLength(552)
 expect(all.series[0].data.filter((r:any)=>r.value[2]==='-')).toHaveLength(298)
 expect(all.series[0].data.filter((r:any)=>Number(r.row.month_age)===0).every((r:any)=>r.value[3]===-1)).toBe(true)
 expect(all.series[0].data.filter((r:any)=>Number(r.row.month_age)===0).every((r:any)=>r.visualMap===false&&r.itemStyle.color==='#dce6e4')).toBe(true)
 expect(retentionLabel(.00018733608092918696)).toBe('0.02%')
 expect(retentionLabel(.000001)).toBe('<0.01%');expect(retentionLabel(0)).toBe('0%');expect(retentionLabel(null)).toBe('NA')
 const observed=all.series[0].data.find((r:any)=>Number(r.row.month_age)===1&&r.row.retention!==null)
 const tooltip=all.tooltip.formatter({data:observed})
 for(const text of ['观察月份','活跃人数','首购人数',String(observed.row.target_month).slice(0,7)])expect(tooltip).toContain(text)
 expect(JSON.stringify(rows)).toBe(before)
})

it('uses the three approved display names consistently while preserving raw codes and search',()=>{
 for(const [code,name] of Object.entries({cool_stuff:'Cool Stuff',la_cuisine:'La Cuisine',seguros_e_servicos:'Seguros e Serviços'})){
  expect(categoryName(code)).toBe(name)
  expect(categoryMatches(code,name)).toBe(true)
  expect(categoryMatches(code,code)).toBe(true)
  const rows:Row[]=[{category:code,merchandise:'1.00'}]
  expect(categoryRows(rows,name,'merchandise',true)[0].category).toBe(code)
  const option=horizontal(rows,'category','merchandise') as any
  expect(option.yAxis.data).toEqual([name])
  expect(option.tooltip.formatter([{dataIndex:0}])).toContain(name)
  expect(option.tooltip.formatter([{dataIndex:0}])).toContain(code)
 }
})
