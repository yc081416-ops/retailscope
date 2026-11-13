/** Ordered rules copied from sql/30_customer.sql; presentation only. */
export const rfmRules:Record<string,string>={
 '核心价值':'R≥4、F≥4、M≥4',
 '活跃复购':'R≥4、F≥4（排除核心价值）',
 '近期用户':'R≥4（排除前两类）',
 '高价值待唤回':'R≤2、M≥4',
 '沉睡用户':'R≤2（排除高价值待唤回）',
 '其他用户':'不满足以上规则的其余用户',
 '数据待核对':'累计商品金额缺失',
}
