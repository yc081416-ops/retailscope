import {expect,it} from 'vitest'
import {readP3Evidence} from './p3Evidence'
import {findingHeadline,findingCopy} from '../src/findingCopy'
import type {EvidenceFinding} from '../src/evidence'

it('shortens finding summaries without changing the accepted evidence or inventing values',()=>{
 const findings:EvidenceFinding[]=readP3Evidence().findings
 const original=JSON.stringify(findings)
 expect(Object.keys(findingCopy)).toHaveLength(7)
 for(const f of findings){
  const summary=findingHeadline(f)
  expect(summary.length).toBeLessThanOrEqual(f.result.length)
  expect(findingCopy[f.id].meaning).toBeTruthy()
  if(f.id==='F05'){
   expect(summary).toContain('2.2718');expect(summary).toContain('4.2906')
   expect(summary).not.toContain('95%');expect(summary).not.toContain('6,381')
  }else if(f.id==='F07')expect(summary).toContain((Number(f.statistics.m1_weighted_retention)*100).toFixed(4))
  else expect(f.result.startsWith(summary.slice(0,-1))).toBe(true)
 }
 expect(JSON.stringify(findings)).toBe(original)
 expect(findingHeadline({...findings[0],id:'F05',statistics:{}})).toBeTruthy()
})
