import { FormEvent, useEffect, useMemo, useState } from "react";
import { Banknote, CheckCircle2, Clock3, FileText, Landmark, RefreshCw, ShieldCheck, UploadCloud } from "lucide-react";

type Locale = "ar" | "en";
const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? "http://localhost:8000" : window.location.origin);

type Invoice = {
  id: string;
  number: string;
  status: string;
  subtotal: number;
  tax_amount: number;
  total: number;
  currency: string;
  description?: string | null;
  due_at?: string | null;
  paid_at?: string | null;
  created_at: string;
};

type BankAccount = {
  id: string;
  label: string;
  bank_name: string;
  account_name: string;
  account_number?: string | null;
  iban?: string | null;
  swift_code?: string | null;
  branch_name?: string | null;
  currency: string;
  instructions?: string | null;
  is_active: boolean;
  is_default: boolean;
};

type Transfer = {
  id: string;
  invoice_id: string;
  bank_account_id: string;
  status: string;
  amount: number;
  currency: string;
  sender_name: string;
  sender_bank?: string | null;
  transfer_reference: string;
  transferred_at: string;
  receipt_url?: string | null;
  receipt_note?: string | null;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  rejection_reason?: string | null;
  created_at: string;
};

async function api<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Authorization", `Bearer ${token}`);
  if (init?.body) headers.set("Content-Type", "application/json");
  const response = await fetch(`${API_URL}${path}`, { ...init, headers });
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new Error(body?.detail || `HTTP ${response.status}`);
  return body as T;
}

function localDateTimeValue() {
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  return now.toISOString().slice(0, 16);
}

export default function TenantBilling({ token, locale }: { token: string; locale: Locale }) {
  const ar = locale === "ar";
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState("");
  const [selectedBankId, setSelectedBankId] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    setBusy(true);
    setError("");
    try {
      const [invoiceData, bankData, transferData] = await Promise.all([
        api<Invoice[]>("/api/v1/billing/invoices", token),
        api<BankAccount[]>("/api/v1/billing/bank-accounts", token),
        api<Transfer[]>("/api/v1/billing/bank-transfers", token),
      ]);
      setInvoices(invoiceData);
      setAccounts(bankData);
      setTransfers(transferData);
      const payable = invoiceData.find((item) => ["open", "overdue"].includes(item.status));
      setSelectedInvoiceId((current) => current || payable?.id || "");
      const defaultBank = bankData.find((item) => item.is_default) || bankData[0];
      setSelectedBankId((current) => current || defaultBank?.id || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => { void load(); }, [token]);

  const selectedInvoice = useMemo(
    () => invoices.find((item) => item.id === selectedInvoiceId) || null,
    [invoices, selectedInvoiceId],
  );
  const eligibleAccounts = useMemo(
    () => accounts.filter((item) => !selectedInvoice || item.currency === selectedInvoice.currency),
    [accounts, selectedInvoice],
  );

  useEffect(() => {
    if (selectedInvoice && !eligibleAccounts.some((item) => item.id === selectedBankId)) {
      setSelectedBankId(eligibleAccounts.find((item) => item.is_default)?.id || eligibleAccounts[0]?.id || "");
    }
  }, [selectedInvoiceId, eligibleAccounts.length]);

  async function submitTransfer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedInvoice) return;
    const data = new FormData(event.currentTarget);
    setError("");
    setNotice("");
    setBusy(true);
    try {
      await api(`/api/v1/billing/invoices/${selectedInvoice.id}/bank-transfer`, token, {
        method: "POST",
        body: JSON.stringify({
          bank_account_id: String(data.get("bank_account_id") || ""),
          amount: Number(selectedInvoice.total),
          currency: selectedInvoice.currency,
          sender_name: String(data.get("sender_name") || "").trim(),
          sender_bank: String(data.get("sender_bank") || "").trim() || null,
          transfer_reference: String(data.get("transfer_reference") || "").trim(),
          transferred_at: new Date(String(data.get("transferred_at") || "")).toISOString(),
          receipt_url: String(data.get("receipt_url") || "").trim() || null,
          receipt_note: String(data.get("receipt_note") || "").trim() || null,
        }),
      });
      setNotice(ar
        ? "تم إرسال بيانات التحويل للمراجعة. لن تُعتبر الفاتورة مدفوعة إلا بعد اعتماد التحويل."
        : "Transfer submitted for verification. The invoice remains unpaid until the transfer is approved.");
      (event.currentTarget as HTMLFormElement).reset();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Transfer submission failed");
    } finally {
      setBusy(false);
    }
  }

  return <div className="opsPage billingWorkspace">
    <div className="opsHeading">
      <div>
        <span className="eyebrow">BANK TRANSFER BILLING</span>
        <h2>{ar ? "الاشتراك والدفع بالتحويل البنكي" : "Subscription & bank-transfer billing"}</h2>
      </div>
      <button className="iconButton" onClick={() => void load()} disabled={busy}><RefreshCw size={17} className={busy ? "spin" : ""}/></button>
    </div>

    <div className="bankPolicy panel">
      <ShieldCheck size={18}/>
      <div>
        <strong>{ar ? "لا توجد بوابة دفع إلكترونية" : "No online payment gateway"}</strong>
        <span>{ar
          ? "الدفع يتم بتحويل بنكي فقط. بعد التحويل أرسل رقم العملية هنا، ويعتمد مسؤول المنصة الدفع بعد مراجعته."
          : "Payment is by bank transfer only. Submit the transaction reference here; a platform administrator verifies it before marking the invoice paid."}</span>
      </div>
    </div>

    {error && <div className="systemError">{error}</div>}
    {notice && <div className="successNotice">{notice}</div>}

    <div className="billingGrid">
      <section className="panel">
        <div className="panelHead"><h3>{ar ? "الفواتير" : "Invoices"}</h3><span>{invoices.length}</span></div>
        <div className="billingInvoiceList">
          {invoices.map((invoice) => <button
            key={invoice.id}
            className={selectedInvoiceId === invoice.id ? "billingInvoice active" : "billingInvoice"}
            onClick={() => setSelectedInvoiceId(invoice.id)}
          >
            <FileText size={17}/>
            <div>
              <strong>{invoice.number}</strong>
              <span>{invoice.description || "—"}</span>
            </div>
            <b>{Number(invoice.total).toLocaleString()} {invoice.currency}</b>
            <span className={`statusBadge status-${invoice.status}`}>{invoice.status}</span>
          </button>)}
          {!invoices.length && <div className="seoEmpty"><FileText size={24}/><p>{ar ? "لا توجد فواتير." : "No invoices."}</p></div>}
        </div>
      </section>

      <section className="panel">
        <div className="panelHead"><h3>{ar ? "الحسابات البنكية" : "Bank accounts"}</h3><span>{accounts.length}</span></div>
        <div className="bankAccountList">
          {accounts.map((account) => <article key={account.id} className={account.is_default ? "bankAccountCard default" : "bankAccountCard"}>
            <Landmark size={18}/>
            <div>
              <strong>{account.label}</strong>
              <span>{account.bank_name} · {account.account_name}</span>
              {account.account_number && <small>{ar ? "رقم الحساب" : "Account"}: {account.account_number}</small>}
              {account.iban && <small>IBAN: {account.iban}</small>}
              {account.swift_code && <small>SWIFT: {account.swift_code}</small>}
              {account.instructions && <p>{account.instructions}</p>}
            </div>
            <b>{account.currency}</b>
          </article>)}
        </div>
      </section>
    </div>

    {selectedInvoice && ["open", "overdue"].includes(selectedInvoice.status) && <form className="panel transferForm" onSubmit={submitTransfer}>
      <div className="opsTitle"><Banknote size={19}/><strong>{ar ? "تسجيل تحويل بنكي" : "Submit bank transfer"}</strong></div>
      <div className="transferInvoiceSummary">
        <span>{selectedInvoice.number}</span>
        <strong>{Number(selectedInvoice.total).toLocaleString()} {selectedInvoice.currency}</strong>
      </div>
      <div className="formGrid">
        <label>{ar ? "الحساب المستلم" : "Receiving account"}
          <select name="bank_account_id" value={selectedBankId} onChange={(e) => setSelectedBankId(e.target.value)} required>
            <option value="">{ar ? "اختر الحساب" : "Select account"}</option>
            {eligibleAccounts.map((account) => <option key={account.id} value={account.id}>{account.label} · {account.bank_name}</option>)}
          </select>
        </label>
        <label>{ar ? "اسم المحول" : "Sender name"}<input name="sender_name" required/></label>
        <label>{ar ? "بنك المحول" : "Sender bank"}<input name="sender_bank"/></label>
        <label>{ar ? "رقم العملية/مرجع التحويل" : "Transfer reference"}<input name="transfer_reference" required/></label>
        <label>{ar ? "تاريخ ووقت التحويل" : "Transfer date/time"}<input name="transferred_at" type="datetime-local" defaultValue={localDateTimeValue()} required/></label>
        <label>{ar ? "رابط صورة الإيصال اختياري" : "Receipt image URL (optional)"}<input name="receipt_url" type="url"/></label>
      </div>
      <label>{ar ? "ملاحظة على التحويل" : "Transfer note"}<textarea name="receipt_note" rows={3}/></label>
      <button className="primaryButton" disabled={busy || !selectedBankId}><UploadCloud size={16}/>{ar ? "إرسال للتحقق" : "Submit for verification"}</button>
    </form>}

    {selectedInvoice?.status === "pending_verification" && <div className="pendingVerification panel">
      <Clock3 size={20}/>
      <div><strong>{ar ? "التحويل قيد المراجعة" : "Transfer awaiting verification"}</strong><span>{ar ? "لن يتغير الاشتراك إلى مدفوع قبل اعتماد مسؤول المنصة للتحويل." : "The subscription will not be marked paid until a platform administrator approves the transfer."}</span></div>
    </div>}

    <section className="panel">
      <div className="panelHead"><h3>{ar ? "سجل التحويلات" : "Transfer history"}</h3><span>{transfers.length}</span></div>
      <div className="transferHistory">
        {transfers.map((transfer) => <article key={transfer.id}>
          <div className="transferStateIcon">{transfer.status === "approved" ? <CheckCircle2 size={18}/> : <Clock3 size={18}/>}</div>
          <div><strong>{transfer.transfer_reference}</strong><span>{transfer.sender_name} · {new Date(transfer.transferred_at).toLocaleString(ar ? "ar-EG" : "en-US")}</span>{transfer.rejection_reason && <small>{transfer.rejection_reason}</small>}</div>
          <b>{Number(transfer.amount).toLocaleString()} {transfer.currency}</b>
          <span className={`statusBadge status-${transfer.status}`}>{transfer.status}</span>
        </article>)}
      </div>
    </section>
  </div>;
}
