export type Scope = { start: string; end: string; state: string | null };
export type Kpis = {
  orders: number;
  users: number;
  merchandise: string;
  freight: string;
  payment: string;
  average_order_value: string | null;
};
export type Month = {
  month_start: string;
  orders: number;
  users: number;
  merchandise: string;
  is_complete: boolean;
};
export type Region = {
  state: string;
  orders: number;
  merchandise: string;
  contribution: string;
};
export type Overview = {
  scope: Scope;
  metadata: {
    source: string;
    license: string;
    bounds: { start: string; end: string };
    context: {
      first_purchase: string;
      last_purchase: string;
      first_complete_month?: string;
      observation_end_exclusive?: string;
    };
    states: string[];
    query_source: string;
    read_only: boolean;
  };
  kpis: Kpis;
  monthly: Month[];
  statuses: { status: string; orders: number }[];
  regions: Region[];
};
export type Finding = {
  id: string;
  title: string;
  result: string;
  scope: string;
  source_sql: string[];
  method: string;
  limitations: string;
  suggestion: string;
};
