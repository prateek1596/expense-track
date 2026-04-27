export type User = {
  id: number;
  email: string;
  full_name: string;
};

export type BankAccount = {
  id: number;
  bank_name: string;
  masked_account: string;
  aa_consent_id: string;
  linked_at: string;
};

export type Transaction = {
  id: number;
  account_id: number;
  amount: number;
  tx_type: string;
  merchant: string;
  category: string;
  description: string;
  timestamp: string;
};

export type MonthlyReport = {
  month: number;
  year: number;
  total_spend: number;
  by_category: Array<{ category: string; total: number }>;
};

export type Budget = {
  id: number;
  category: string;
  monthly_limit: number;
  month: number;
  year: number;
};

export type BudgetAlert = {
  category: string;
  month: number;
  year: number;
  limit: number;
  spent: number;
  over_by: number;
  percent: number;
};
