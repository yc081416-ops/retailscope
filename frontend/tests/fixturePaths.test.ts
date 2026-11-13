import {it,expect} from 'vitest'
import {resolve} from 'node:path'
import {containedEvidence} from './p3Evidence'
it('allows current-version test fixtures but rejects paths outside reports',()=>{
 const root=resolve('.')
 expect(containedEvidence(root,'reports/runtime/runs/current/p3/analysis.json')).toContain('analysis.json')
 expect(()=>containedEvidence(root,'../private.json')).toThrow('under reports')
})
