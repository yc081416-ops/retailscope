import type {EvidenceFinding} from './evidence'

export const findingCopy: Record<string,{title:string;meaning:string}> = {
 F01:{title:'月度经营变化',meaning:'结合商品金额与订单量，观察经营规模的变化。'},
 F02:{title:'异常月份回顾',meaning:'标记月份值得结合促销、供给与样本变化进一步核查。'},
 F03:{title:'品类贡献集中度',meaning:'重点品类可作为商品结构复盘的起点。'},
 F04:{title:'地区销售与配送',meaning:'结合地区规模和履约表现安排后续复盘重点。'},
 F05:{title:'逾期与评价差异',meaning:'逾期组评价较低，可进一步按地区与品类核查体验差异。'},
 F06:{title:'用户复购结构',meaning:'一次购买用户占多数，用户结构需结合购买机会理解。'},
 F07:{title:'同期群回购留存',meaning:'在完整观察窗口内比较回购活跃，避免误读空白月份。'},
}

/** Shorten presentation only; the complete accepted result remains in the evidence details. */
export function findingHeadline(f:EvidenceFinding){
 if(f.id==='F07'&&typeof f.statistics.m1_weighted_retention==='number')return `完整次月观察的加权回购留存为 ${(f.statistics.m1_weighted_retention*100).toFixed(4)}%。`;
 if(f.id==='F05'){
  const groups=f.statistics.groups as {group:string;mean_score:number}[] | undefined
  if(groups?.length)return groups.map(g=>`${g.group}组均分 ${g.mean_score.toFixed(4)}`).join('；')+'。'
 }
 return f.result.split('；')[0].split('。')[0]+'。'
}
