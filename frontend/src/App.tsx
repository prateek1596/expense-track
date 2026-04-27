import { useEffect, useMemo, useState } from 'react';
import { api, API_BASE } from './api';
import type { BankAccount, Budget, BudgetAlert, MonthlyReport, Transaction } from './types';

function App() {
  const now = new Date();
  const [email, setEmail] = useState('prateek@example.com');
  const [fullName, setFullName] = useState('Prateek');
  const [password, setPassword] = useState('password123');
  const [token, setToken] = useState<string>('');
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [alerts, setAlerts] = useState<BudgetAlert[]>([]);
  const [report, setReport] = useState<MonthlyReport | null>(null);
  const [bankName, setBankName] = useState('HDFC');
  const [masked, setMasked] = useState('XXXX4321');
  const [selectedAccount, setSelectedAccount] = useState<number | null>(null);
  const [amount, setAmount] = useState<number>(250);
  const [merchant, setMerchant] = useState('Swiggy');
  const [description, setDescription] = useState('Dinner order');
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [budgetCategory, setBudgetCategory] = useState('Food');
  const [budgetLimit, setBudgetLimit] = useState<number>(5000);
  const [error, setError] = useState('');
  const [userId, setUserId] = useState<number | null>(null);

  const wsUrl = useMemo(() => {
    const base = API_BASE.replace('http://', 'ws://').replace('https://', 'wss://');
    return `${base}/ws/0`;
  }, []);

  async function refreshAll(activeToken: string) {
    const [accountRes, txRes, reportRes, budgetRes] = await Promise.all([
      api.listAccounts(activeToken) as Promise<BankAccount[]>,
      api.listTransactions(activeToken) as Promise<Transaction[]>,
      api.monthlyReport(activeToken, month, year) as Promise<MonthlyReport>,
      api.listBudgets(activeToken) as Promise<Budget[]>,
    ]);
    setAccounts(accountRes);
    setTransactions(txRes);
    setReport(reportRes);
    setBudgets(budgetRes);
    if (!selectedAccount && accountRes.length) {
      setSelectedAccount(accountRes[0].id);
    }
  }

  async function handleRegister() {
    setError('');
    try {
      await api.register({ email, full_name: fullName, password });
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function handleLogin() {
    setError('');
    try {
      const res = await api.login({ email, password });
      setToken(res.access_token);
      const me = (await api.me(res.access_token)) as { id: number };
      setUserId(me.id);
      await refreshAll(res.access_token);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function handleLinkAccount() {
    if (!token) return;
    await api.linkAccount(token, { bank_name: bankName, masked_account: masked });
    await refreshAll(token);
  }

  async function handleAddTransaction() {
    if (!token || !selectedAccount) return;
    await api.addTransaction(token, {
      account_id: selectedAccount,
      amount,
      tx_type: 'debit',
      merchant,
      description,
      timestamp: new Date().toISOString(),
      raw_data: { source: 'manual' },
    });
    await refreshAll(token);
  }

  async function handleRefreshReport() {
    if (!token) return;
    const reportRes = (await api.monthlyReport(token, month, year)) as MonthlyReport;
    setReport(reportRes);
  }

  async function handleExportPdf() {
    if (!token) return;
    const blob = await api.monthlyReportPdf(token, month, year);
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `monthly-report-${year}-${String(month).padStart(2, '0')}.pdf`;
    anchor.click();
    window.URL.revokeObjectURL(url);
  }

  async function handleSaveBudget() {
    if (!token) return;
    await api.upsertBudget(token, {
      category: budgetCategory,
      monthly_limit: budgetLimit,
      month,
      year,
    });
    await refreshAll(token);
  }

  useEffect(() => {
    if (!token || !userId) return;

    const socket = new WebSocket(`${wsUrl.replace('/ws/0', `/ws/${userId}`)}?token=${encodeURIComponent(token)}`);
    socket.onmessage = async (event) => {
      try {
        const payload = JSON.parse(event.data) as { type?: string; data?: BudgetAlert };
        if (payload.type === 'budget.alert' && payload.data) {
          setAlerts((prev) => [payload.data, ...prev].slice(0, 5));
        }
      } catch {
        // Ignore non-JSON ping frames.
      }
      await refreshAll(token);
    };

    return () => socket.close();
  }, [token, wsUrl, userId]);

  const debitTotal = transactions
    .filter((tx) => tx.tx_type === 'debit')
    .reduce((sum, tx) => sum + Number(tx.amount), 0);

  return (
    <div className="page">
      <header className="hero">
        <h1>Spend</h1>
        <p>Real-time monthly expense tracking for Indian bank users.</p>
      </header>

      <section className="card auth-card">
        <h2>Auth</h2>
        <div className="grid two">
          <input value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Full name" />
          <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
          <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="Password" />
        </div>
        <div className="row">
          <button onClick={handleRegister}>Register</button>
          <button onClick={handleLogin}>Login</button>
          {token && <span className="ok">Authenticated</span>}
        </div>
        {error && <p className="error">{error}</p>}
      </section>

      {!!alerts.length && (
        <section className="card alert-card">
          <h3>Budget Alerts</h3>
          <div className="alerts">
            {alerts.map((alert, idx) => (
              <p key={`${alert.category}-${alert.month}-${alert.year}-${idx}`}>
                {alert.category}: spent INR {alert.spent.toFixed(2)} vs limit INR {alert.limit.toFixed(2)} ({alert.percent.toFixed(1)}%)
              </p>
            ))}
          </div>
        </section>
      )}

      <section className="grid three">
        <article className="card">
          <h3>Quick Stats</h3>
          <p>Accounts linked: {accounts.length}</p>
          <p>Transactions: {transactions.length}</p>
          <p>This month spend: INR {debitTotal.toFixed(2)}</p>
        </article>

        <article className="card">
          <h3>Link Bank Account</h3>
          <input value={bankName} onChange={(e) => setBankName(e.target.value)} placeholder="Bank name" />
          <input value={masked} onChange={(e) => setMasked(e.target.value)} placeholder="Masked account" />
          <button disabled={!token} onClick={handleLinkAccount}>Link Account</button>
        </article>

        <article className="card">
          <h3>Add Transaction</h3>
          <select
            title="Select account"
            value={selectedAccount ?? ''}
            onChange={(e) => setSelectedAccount(Number(e.target.value))}
          >
            <option value="">Select account</option>
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.bank_name} {account.masked_account}
              </option>
            ))}
          </select>
          <input
            type="number"
            title="Amount"
            placeholder="Amount"
            value={amount}
            onChange={(e) => setAmount(Number(e.target.value))}
          />
          <input value={merchant} onChange={(e) => setMerchant(e.target.value)} placeholder="Merchant" />
          <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description" />
          <button disabled={!token || !selectedAccount} onClick={handleAddTransaction}>Add Debit</button>
        </article>
      </section>

      <section className="grid two">
        <article className="card">
          <h3>Live Transaction Feed</h3>
          <div className="feed">
            {transactions.map((tx) => (
              <div className="tx" key={tx.id}>
                <div>
                  <strong>{tx.merchant}</strong>
                  <p>{tx.description}</p>
                </div>
                <div>
                  <span className="tag">{tx.category}</span>
                  <p>INR {Number(tx.amount).toFixed(2)}</p>
                </div>
              </div>
            ))}
            {!transactions.length && <p>No transactions yet.</p>}
          </div>
        </article>

        <article className="card">
          <h3>Monthly Report</h3>
          <div className="row">
            <input
              type="number"
              title="Month"
              placeholder="Month"
              min={1}
              max={12}
              value={month}
              onChange={(e) => setMonth(Number(e.target.value))}
            />
            <input
              type="number"
              title="Year"
              placeholder="Year"
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
            />
            <button disabled={!token} onClick={handleRefreshReport}>Refresh</button>
            <button disabled={!token} onClick={handleExportPdf}>Export PDF</button>
          </div>
          <p>Total spend: INR {report?.total_spend.toFixed(2) ?? '0.00'}</p>
          <div className="bars">
            {report?.by_category.map((item) => (
              <div key={item.category} className="bar-row">
                <span>{item.category}</span>
                <progress
                  className="bar-progress"
                  max={100}
                  value={Math.min(100, report.total_spend ? (item.total / report.total_spend) * 100 : 0)}
                />
                <span>INR {item.total.toFixed(0)}</span>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="card">
        <h3>Budgets</h3>
        <div className="grid three">
          <input
            title="Budget category"
            placeholder="Category"
            value={budgetCategory}
            onChange={(e) => setBudgetCategory(e.target.value)}
          />
          <input
            type="number"
            title="Monthly limit"
            placeholder="Monthly limit"
            value={budgetLimit}
            onChange={(e) => setBudgetLimit(Number(e.target.value))}
          />
          <button disabled={!token} onClick={handleSaveBudget}>Save Budget</button>
        </div>
        <div className="budget-list">
          {budgets
            .filter((item) => item.month === month && item.year === year)
            .map((item) => (
              <p key={item.id}>{item.category}: INR {item.monthly_limit.toFixed(2)} for {item.month}/{item.year}</p>
            ))}
        </div>
      </section>
    </div>
  );
}

export default App;
