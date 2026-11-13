export function beijingTime(value:unknown){
 if(!value)return '未记录'
 const raw=String(value)
 if(!/(Z|[+-]\d{2}:\d{2})$/i.test(raw))return /^\d{4}-\d{2}-\d{2}/.test(raw)?raw.replace('T',' ').split('.')[0]+'（时区未记录）':'时间不可用'
 const date=new Date(raw)
 return Number.isNaN(date.getTime())?'时间不可用':new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(date).replaceAll('/','-')+'（北京时间）'
}
