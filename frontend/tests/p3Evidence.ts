/** Test fixtures follow the same active-snapshot convention as the running application. */
import {existsSync,readFileSync} from 'node:fs'
import {resolve,relative,isAbsolute} from 'node:path'
import {fileURLToPath} from 'node:url'
export function containedEvidence(root:string,candidate:string){
 const path=resolve(root,candidate),within=relative(resolve(root,'reports'),path)
 if(within.startsWith('..')||isAbsolute(within))throw Error('Test evidence must remain under reports')
 return path
}
export function readP3Evidence(){
 const root=fileURLToPath(new URL('../../',import.meta.url))
 const active=resolve(root,'reports/runtime/active.json')
 const candidate=existsSync(active)?JSON.parse(readFileSync(active,'utf8')).analysis:'reports/p3/analysis.json'
 return JSON.parse(readFileSync(containedEvidence(root,candidate),'utf8'))
}
