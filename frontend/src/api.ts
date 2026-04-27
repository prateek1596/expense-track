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

  listTransactions: (token: string) =>
    request('/transactions', { headers: { Authorization: `Bearer ${token}` } }),

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
};

export { API_BASE };
