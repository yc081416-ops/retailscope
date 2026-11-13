import {useEffect,useId,useRef,useState} from 'react'
import {categoryMatches,categoryName} from './categories'

export function CategorySelect({codes,value,onChange}:{codes:string[];value:string|null;onChange:(code:string|null)=>void}){
 const [open,setOpen]=useState(false),[search,setSearch]=useState(''),[active,setActive]=useState(0)
 const input=useRef<HTMLInputElement>(null),trigger=useRef<HTMLButtonElement>(null),id=useId()
 const options=['',...codes].filter(code=>code?categoryMatches(code,search):!search||'全部类目'.includes(search))
 useEffect(()=>{if(open)input.current?.focus()},[open])
 useEffect(()=>{if(open)document.getElementById(`${id}-${active}`)?.scrollIntoView({block:'nearest'})},[active,open,id])
 const choose=(code:string)=>{onChange(code||null);setOpen(false);setSearch('');trigger.current?.focus()}
 return <div className="category-picker" onBlur={e=>{if(!e.currentTarget.contains(e.relatedTarget))setOpen(false)}}>
  <button type="button" ref={trigger} role="combobox" aria-label="商品类目" aria-expanded={open} aria-controls={id} title={value??'全部类目'} onClick={()=>{setOpen(!open);setSearch('');setActive(0)}} onKeyDown={e=>{if(e.key==='ArrowDown'){e.preventDefault();setOpen(true)}}}>{value?categoryName(value):'全部类目'}<span aria-hidden="true">⌄</span></button>
  {open&&<div className="category-menu">
   <input ref={input} role="searchbox" aria-label="搜索商品类目" aria-controls={id} aria-activedescendant={options.length?`${id}-${active}`:undefined} value={search} placeholder="搜索中文名称或原编码" onChange={e=>{setSearch(e.target.value);setActive(0)}} onKeyDown={e=>{
    if(e.key==='Escape'){e.preventDefault();setOpen(false);trigger.current?.focus()}
    if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();setActive(i=>Math.max(0,Math.min(options.length-1,i+(e.key==='ArrowDown'?1:-1))))}
    if(e.key==='Enter'){e.preventDefault();if(options[active]!==undefined)choose(options[active])}
   }}/>
   <div role="listbox" aria-label="商品类目选项" id={id}>{options.map((code,i)=><button type="button" role="option" aria-selected={code===(value??'')} id={`${id}-${i}`} key={code} tabIndex={-1} className={i===active?'active-option':''} title={code||'全部类目'} onMouseDown={e=>e.preventDefault()} onClick={()=>choose(code)}>{code?categoryName(code):'全部类目'}</button>)}{!options.length&&<p role="status">没有匹配类目</p>}</div>
  </div>}
 </div>
}
