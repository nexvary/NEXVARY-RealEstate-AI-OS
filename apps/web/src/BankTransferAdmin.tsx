import { FormEvent, useEffect, useMemo, useState } from "react";
import { CheckCircle2, Landmark, RefreshCw, ShieldCheck, XCircle } from "lucide-react";

type Locale = "ar" | "en";
const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? "http://localhost:8000" : window.location.origin);

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
  tenant_id: string;
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

type Tenant = {
  id: string;
  name: string;
  brand_name?: string | null;
  slug: string;
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

export default function BankTransferAdmin({ token, locale }: { token: string; locale: Locale }) {
  const ar = locale === "ar";
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState("");

  async function load() {
    setError("");
    try {
      const [bankData, transferData, tenantData] = await Promise.all([
        api<BankAccount[]>("/api/v1/platform/bank-accounts", token),
        api<Transfer[]>("/api/v1/platform/bank-transfers", token),
        api<Tenant[]>("/api/v1/platform/tenants", token),
      ]);
      setAccounts(bankData);
      setTransfers(transferData);
      setTenants(tenantData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    }
  }

  useEffect(() => { void load(); }, [token]);

  const tenantNames = useMemo(
    () => new Map(tenants.map((tenant) => [tenant.id, tenant.brand_name || tenant.name || tenant.slug])),
    [tenants],
  );
  const pending = transfers.filter((item) => item.status === "pending");

  async function createAccount(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setBusy("bank");
    setError("");
    setNotice("");
    try {
      await api("/api/v1/platform/bank-accounts", token, {
        method: "POST",
        body: JSON.stringify({
          label: String(data.get("label") || "").trim(),
          bank_name: String(data.get("bank_name") || "").trim(),
          account_name: String(data.get("account_name") || "").trim(),
          account_number: String(data.get("account_number") || "").trim() || null,
          iban: String(data.get("iban") || "").trim() || null,
          swift_code: String(data.get("swift_code") || "").trim() || null,
          branch_name: String(data.get("branch_name") || "").trim() || null,
          currency: String(data.get("currency") || "EGP").trim().toUpperCase(),
          instructions: String(data.get("instructions") || "").trim() || null,
          is_active: true,
          is_default: data.get("is_default") === "on",
        }),
      });
      form.reset();
      setNotice(ar ? "تم حفظ الحساب البنكي." : "Bank account saved.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setBusy("");
    }
  }

  async function approve(transfer: Transfer) {
    setBusy(transfer.id);
    setError("");
    setNotice("");
    try {
      await api(`/api/v1/platform/bank-transfers/${transfer.id}/approve`, token, { method: "POST" });
      setNotice(ar ? "تم اعتماد التحويل وتسجيل الفاتورة مدفوعة." : "Transfer approved and invoice marked paid.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approval failed");
    } finally {
      setBusy("");
    }
  }

  async function reject(transfer: Transfer) {
    const reason = window.prompt(ar ? "سبب رفض التحويل" : "Reason for rejection", ar ? "تعذر مطابقة مرجع التحويل مع كشف البنك." : "Transfer reference could not be matched to the bank statement.");
    if (reason === null) return;
    setBusy(transfer.id);
    setError("");
    setNotice("");
    try {
      await api(`/api/v1/platform/bank-transfers/${transfer.id}/reject`, token, {
        method: "POST",
        body: JSON.stringify({ rejection_reason: reason }),
      });
      setNotice(ar ? "تم رفض التحويل وإعادة الفاتورة إلى حالة انتظار الدفع." : "Transfer rejected and invoice reopened for payment.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rejection failed");
    } finally {
      setBusy("");
    }
  }

  return <section className="bankAdmin">
    <div className="commercialHeading">
      <div><span className="eyebrow">BANK TRANSFER OPERATIONS</span><h2>{ar ? "الحسابات البنكية ومراجعة التحويلات" : "Bank accounts & transfer verification"}</h2></div>
      <button className="iconButton" onClick={() => void load()}><RefreshCw size={17}/></button>
    </div>

    <div className="bankPolicy panel">
      <ShieldCheck size={18}/>
      <div><strong>{ar ? "الدفع البنكي فقط" : "Bank-transfer only"}</strong><span>{ar ? "لا يتم اعتماد أي فاتورة تلقائيًا. يجب مطابقة التحويل ثم اعتماده من إدارة المنصة." : "Invoices are never auto-paid. A platform administrator must match and approve each transfer."}</span></div>
    </div>

    {error && <div className="systemError">{error}</div>}
    {notice && <div className="successNotice">{notice}</div>}

    <div className="commercialGrid">
      <form className="panel commercialForm" onSubmit={createAccount}>
        <div className="opsTitle"><Landmark size={19}/><strong>{ar ? "إضافة حساب بنكي" : "Add bank account"}</strong></div>
        <div className="formGrid">
          <label>{ar ? "اسم مختصر" : "Label"}<input name="label" required placeholder="NEXVARY EGP"/></label>
          <label>{ar ? "اسم البنك" : "Bank name"}<input name="bank_name" required/></label>
          <label>{ar ? "اسم صاحب الحساب" : "Account name"}<input name="account_name" required/></label>
          <label>{ar ? "رقم الحساب" : "Account number"}<input name="account_number"/></label>
          <label>IBAN<input name="iban"/></label>
          <label>SWIFT<input name="swift_code"/></label>
          <label>{ar ? "الفرع" : "Branch"}<input name="branch_name"/></label>
          <label>{ar ? "العملة" : "Currency"}<input name="currency" defaultValue="EGP" required/></label>
        </div>
        <label>{ar ? "تعليمات التحويل" : "Transfer instructions"}<textarea name="instructions" rows={3} placeholder={ar ? "اكتب رقم الفاتورة في وصف التحويل." : "Write the invoice number in the transfer description."}/></label>
        <label className="checkLabel"><input name="is_default" type="checkbox"/><span>{ar ? "الحساب الافتراضي" : "Default account"}</span></label>
        <button className="primaryButton" disabled={busy==="bank"}><Landmark size={16}/>{ar ? "حفظ الحساب" : "Save account"}</button>
      </form>

      <section className="panel bankAccountAdminList">
        <div className="panelHead"><h3>{ar ? "الحسابات المتاحة للعملاء" : "Customer-facing bank accounts"}</h3><span>{accounts.length}</span></div>
        {accounts.map((account) => <article key={account.id}>
          <Landmark size={18}/>
          <div><strong>{account.label}</strong><span>{account.bank_name} · {account.account_name}</span>{account.account_number && <small>{account.account_number}</small>}{account.iban && <small>IBAN {account.iban}</small>}</div>
          <b>{account.currency}</b>
          <span className={`statusBadge ${account.is_active ? "status-active" : "status-disabled"}`}>{account.is_active ? (ar?"نشط":"active") : (ar?"متوقف":"disabled")}</span>
        </article>)}
      </section>
    </div>

    <section className="panel transferReviewPanel">
      <div className="panelHead"><div><h3>{ar ? "تحويلات تنتظر المراجعة" : "Transfers awaiting verification"}</h3><span>{pending.length}</span></div></div>
      <div className="transferReviewRows">
        {pending.map((transfer) => <article key={transfer.id}>
          <div><strong>{tenantNames.get(transfer.tenant_id) || transfer.tenant_id}</strong><span>{transfer.transfer_reference} · {transfer.sender_name}{transfer.sender_bank ? ` · ${transfer.sender_bank}` : ""}</span><small>{new Date(transfer.transferred_at).toLocaleString(ar ? "ar-EG" : "en-US")}{transfer.receipt_note ? ` · ${transfer.receipt_note}` : ""}</small></div>
          <b>{Number(transfer.amount).toLocaleString()} {transfer.currency}</b>
          {transfer.receipt_url ? <a href={transfer.receipt_url} target="_blank" rel="noreferrer">{ar ? "الإيصال" : "Receipt"}</a> : <span className="mutedReceipt">{ar ? "لا يوجد رابط إيصال" : "No receipt link"}</span>}
          <button className="secondaryButton approveTransfer" disabled={busy===transfer.id} onClick={() => void approve(transfer)}><CheckCircle2 size={15}/>{ar ? "اعتماد" : "Approve"}</button>
          <button className="secondaryButton rejectTransfer" disabled={busy===transfer.id} onClick={() => void reject(transfer)}><XCircle size={15}/>{ar ? "رفض" : "Reject"}</button>
        </article>)}
        {!pending.length && <div className="seoEmpty"><CheckCircle2 size={26}/><p>{ar ? "لا توجد تحويلات تنتظر المراجعة." : "No bank transfers awaiting verification."}</p></div>}
      </div>
    </section>
  </section>;
}
