const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers ?? {}),
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'Request failed');
  }

  return (await response.json()) as T;
}

export const api = {
  register: (payload: { email: string; full_name: string; password: string }) =>
    request('/auth/register', { method: 'POST', body: JSON.stringify(payload) }),

  login: (payload: { email: string; password: string }) =>
    request<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  me: (token: string) =>
    request('/auth/me', { headers: { Authorization: `Bearer ${token}` } }),

  listAccounts: (token: string) =>
    request('/accounts', { headers: { Authorization: `Bearer ${token}` } }),

  linkAccount: (token: string, payload: { bank_name: string; masked_account: string }) =>
    request('/accounts/link', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify(payload),
    }),

  listTransactions: (
    token: string,
    filters?: { month?: number; year?: number; category?: string; search?: string; account_id?: number },
  ) => {
    const params = new URLSearchParams();
    if (filters?.month !== undefined) params.set('month', String(filters.month));
    if (filters?.year !== undefined) params.set('year', String(filters.year));
    if (filters?.category) params.set('category', filters.category);
    if (filters?.search) params.set('search', filters.search);
    if (filters?.account_id !== undefined) params.set('account_id', String(filters.account_id));

    const query = params.toString();
    return request(`/transactions${query ? `?${query}` : ''}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  },
  listTransactionsPage: (
    token: string,
    filters?: { month?: number; year?: number; category?: string; search?: string; account_id?: number; page?: number; per_page?: number },
  ) => {
    const params = new URLSearchParams();
    if (filters?.month !== undefined) params.set('month', String(filters.month));
    if (filters?.year !== undefined) params.set('year', String(filters.year));
    if (filters?.category) params.set('category', filters.category);
    if (filters?.search) params.set('search', filters.search);
    if (filters?.account_id !== undefined) params.set('account_id', String(filters.account_id));
    if (filters?.page !== undefined) params.set('page', String(filters.page));
    if (filters?.per_page !== undefined) params.set('per_page', String(filters.per_page));

    const query = params.toString();
    return request(`/transactions/page${query ? `?${query}` : ''}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  },
  transactionsCsv: async (
    token: string,
    filters?: { month?: number; year?: number; category?: string; search?: string; account_id?: number; page?: number; per_page?: number },
  ) => {
    const params = new URLSearchParams();
    if (filters?.month !== undefined) params.set('month', String(filters.month));
    if (filters?.year !== undefined) params.set('year', String(filters.year));
    if (filters?.category) params.set('category', filters.category);
    if (filters?.search) params.set('search', filters.search);
    if (filters?.account_id !== undefined) params.set('account_id', String(filters.account_id));
    if (filters?.page !== undefined) params.set('page', String(filters.page));
    if (filters?.per_page !== undefined) params.set('per_page', String(filters.per_page));

    const query = params.toString();
    const response = await fetch(`${API_BASE}/transactions/csv${query ? `?${query}` : ''}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || 'Failed to export transactions CSV');
    }
    return response.blob();
  },

  addTransaction: (
    token: string,
    payload: {
      account_id: number;
      amount: number;
      tx_type: string;
      merchant: string;
      description: string;
      timestamp: string;
      raw_data: Record<string, unknown>;
    },
  ) =>
    request('/transactions', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify(payload),
    }),

  monthlyReport: (token: string, month: number, year: number) =>
    request(`/reports/monthly?month=${month}&year=${year}`, {
      headers: { Authorization: `Bearer ${token}` },
    }),

  recurringSpending: (token: string, month: number, year: number, lookbackMonths = 6) =>
    request(`/reports/recurring?month=${month}&year=${year}&lookback_months=${lookbackMonths}`, {
      headers: { Authorization: `Bearer ${token}` },
    }),

  monthlyReportPdf: async (token: string, month: number, year: number) => {
    const response = await fetch(`${API_BASE}/reports/monthly/pdf?month=${month}&year=${year}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || 'Failed to export PDF');
    }
    return response.blob();
  },
  monthlyReportCsv: async (token: string, month: number, year: number) => {
    const response = await fetch(`${API_BASE}/reports/monthly/csv?month=${month}&year=${year}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || 'Failed to export CSV');
    }
    return response.blob();
  },

  listBudgets: (token: string) =>
    request('/budgets', { headers: { Authorization: `Bearer ${token}` } }),

  upsertBudget: (
    token: string,
    payload: { category: string; monthly_limit: number; month: number; year: number },
  ) =>
    request('/budgets', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify(payload),
    }),
};

export { API_BASE };
