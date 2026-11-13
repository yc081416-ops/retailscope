import labels from './categoryLabels.json'
import type {Row} from './analysis'
export const categoryLabels:Record<string,{zh:string;en:string|null;status:string}>=labels
export const categoryName=(code:unknown)=>categoryLabels[String(code)]?.zh ?? '未翻译'
export const categoryMatches=(code:string,search:string)=>[categoryName(code),code,categoryLabels[code]?.en ?? ''].some(v=>v.toLocaleLowerCase().includes(search.trim().toLocaleLowerCase()))
export function wrapCategoryLabel(name:string){
 if(name.length<=12)return name
 const middle=Math.ceil(name.length/2),separator=name.lastIndexOf('、',middle)
 const cut=separator>=3?separator+1:middle
 return name.slice(0,cut)+'\n'+name.slice(cut)
}
export function categoryRows(rows:Row[],search:string,sort:string,all:boolean){
 const filtered=rows.filter(r=>categoryMatches(String(r.category),search))
 const sorted=[...filtered].sort((a,b)=>sort==='name'?categoryName(a.category).localeCompare(categoryName(b.category),'zh-CN'):Number(b[sort])-Number(a[sort])||String(a.category).localeCompare(String(b.category)))
 return all||search?sorted:sorted.slice(0,10)
}
