import BankTransferAdmin from "./BankTransferAdmin";
import { FormEvent, useEffect, useState } from "react";
import { Building2, CheckCircle2, CircleDollarSign, FileText, Layers3, Plus, RefreshCw, Sparkles } from "lucide-react";

type Locale = "ar" | "en";

const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? "http://localhost:8000" : window.location.origin);

async function api<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Authorization", `Bearer ${token}`);
  if (init?.body) headers.set("Content-Type", "application/json");
  const response = await fetch(`${API_URL}${path}`, { ...init, headers });
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new Error(body?.detail || `HTTP ${response.status}`);
  return body as T;
}

type Subscription = {
  id: string;
  tenant_id: string;
  plan: string;
  status: string;
  billing_cycle: string;
  amount: number;
  currency: string;
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
};

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

type Template = {
  id: string;
  name: string;
  description?: string | null;
  plan: string;
  primary_color: string;
  powered_by_nexvary: boolean;
  max_users: number;
  max_projects: number;
  max_units: number;
  max_monthly_ai_requests: number;
  feature_flags: Record<string, boolean>;
  integration_providers: string[];
  subscription_amount: number;
  subscription_currency: string;
  billing_cycle: string;
};

export default function CommercialAdmin({
  token,
  locale,
  tenantId,
  tenantName,
  onProvisioned,
}: {
  token: string;
  locale: Locale;
  tenantId?: string;
  tenantName?: string;
  onProvisioned?: () => void;
}) {
  const ar = locale === "ar";
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState("");

  async function load() {
    setError("");
    try {
      const templateData = await api<Template[]>("/api/v1/platform/templates", token);
      setTemplates(templateData);
      if (tenantId) {
        const [sub, inv] = await Promise.all([
          api<Subscription | null>(`/api/v1/platform/tenants/${tenantId}/subscription`, token),
          api<Invoice[]>(`/api/v1/platform/tenants/${tenantId}/invoices`, token),
        ]);
        setSubscription(sub);
        setInvoices(inv);
      } else {
        setSubscription(null);
        setInvoices([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    }
  }

  useEffect(() => { void load(); }, [token, tenantId]);

  async function saveSubscription(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tenantId) return;
    const data = new FormData(event.currentTarget);
    setBusy("subscription"); setError(""); setNotice("");
    try {
      await api(`/api/v1/platform/tenants/${tenantId}/subscription`, token, {
        method: "PUT",
        body: JSON.stringify({
          plan: String(data.get("plan") || "professional"),
          status: String(data.get("status") || "active"),
          billing_cycle: String(data.get("billing_cycle") || "monthly"),
          amount: Number(data.get("amount") || 0),
          currency: String(data.get("currency") || "USD"),
          provider: "bank_transfer",
          cancel_at_period_end: data.get("cancel_at_period_end") === "on",
          apply_plan_limits: data.get("apply_plan_limits") === "on",
        }),
      });
      setNotice(ar ? "تم تحديث الاشتراك وحدود الخطة." : "Subscription and plan limits updated.");
      await load();
      onProvisioned?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Subscription update failed");
    } finally { setBusy(""); }
  }

  async function createInvoice(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tenantId) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    setBusy("invoice"); setError(""); setNotice("");
    try {
      await api(`/api/v1/platform/tenants/${tenantId}/invoices`, token, {
        method: "POST",
        body: JSON.stringify({
          subtotal: Number(data.get("subtotal") || 0),
          tax_amount: Number(data.get("tax_amount") || 0),
          currency: String(data.get("currency") || "USD"),
          due_at: data.get("due_at") ? new Date(String(data.get("due_at"))).toISOString() : null,
          description: String(data.get("description") || "").trim() || null,
          status: "open",
        }),
      });
      form.reset();
      setNotice(ar ? "تم إنشاء الفاتورة." : "Invoice created.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invoice failed");
    } finally { setBusy(""); }
  }

  async function invoiceAction(id: string, action: "pay" | "void") {
    setError("");
    try {
      await api(`/api/v1/platform/invoices/${id}/${action}`, token, { method: "POST" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invoice update failed");
    }
  }

  async function seedDefaults() {
    setBusy("seed"); setError(""); setNotice("");
    try {
      const seeded = await api<Template[]>("/api/v1/platform/templates/seed-defaults", token, { method: "POST" });
      setTemplates(seeded);
      setNotice(ar ? "تم تجهيز قوالب Starter وProfessional وEnterprise." : "Starter, Professional and Enterprise templates are ready.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Template seeding failed");
    } finally { setBusy(""); }
  }

  async function createTemplate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setBusy("template"); setError(""); setNotice("");
    try {
      const providers = String(data.get("integration_providers") || "")
        .split(",").map((item) => item.trim()).filter(Boolean);
      await api("/api/v1/platform/templates", token, {
        method: "POST",
        body: JSON.stringify({
          name: String(data.get("name") || ""),
          description: String(data.get("description") || "") || null,
          plan: String(data.get("plan") || "professional"),
          primary_color: String(data.get("primary_color") || "#0B1F33"),
          powered_by_nexvary: data.get("powered_by_nexvary") === "on",
          feature_flags: {
            seo: data.get("feature_seo") === "on",
            whatsapp: data.get("feature_whatsapp") === "on",
            ai_sales: data.get("feature_ai") === "on",
          },
          integration_providers: providers,
          subscription_amount: Number(data.get("subscription_amount") || 0),
          subscription_currency: String(data.get("subscription_currency") || "USD"),
          billing_cycle: String(data.get("billing_cycle") || "monthly"),
        }),
      });
      form.reset();
      setNotice(ar ? "تم حفظ قالب الشركة." : "Tenant template saved.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Template creation failed");
    } finally { setBusy(""); }
  }

  async function provision(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const templateId = String(data.get("template_id") || "");
    if (!templateId) return;
    setBusy("provision"); setError(""); setNotice("");
    try {
      const result = await api<{ company_slug: string; integrations_created: string[] }>(`/api/v1/platform/templates/${templateId}/provision`, token, {
        method: "POST",
        body: JSON.stringify({
          company_name: String(data.get("company_name") || ""),
          company_slug: String(data.get("company_slug") || "").toLowerCase(),
          brand_name: String(data.get("brand_name") || "") || null,
          owner_name: String(data.get("owner_name") || ""),
          owner_email: String(data.get("owner_email") || ""),
          owner_password: String(data.get("owner_password") || ""),
          custom_domain: String(data.get("custom_domain") || "") || null,
          contact_email: String(data.get("contact_email") || "") || null,
          website_url: String(data.get("website_url") || "") || null,
        }),
      });
      form.reset();
      setNotice(ar
        ? `تم إنشاء الشركة ${result.company_slug} بالكامل بضغطة واحدة مع ${result.integrations_created.length} تكاملات مبدئية.`
        : `Provisioned ${result.company_slug} with ${result.integrations_created.length} integration placeholders.`);
      onProvisioned?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Provisioning failed");
    } finally { setBusy(""); }
  }

  return <section className="commercialAdmin">
    <div className="commercialHeading">
      <div><span className="eyebrow">COMMERCIAL CONTROL PLANE</span><h2>{ar ? "الاشتراكات والفواتير وقوالب الشركات" : "Subscriptions, billing & tenant templates"}</h2></div>
      <button className="iconButton" onClick={() => void load()}><RefreshCw size={17}/></button>
    </div>
    {error && <div className="systemError">{error}</div>}
    {notice && <div className="successNotice">{notice}</div>}

    {tenantId && <div className="commercialGrid">
      <form className="panel commercialForm" onSubmit={saveSubscription}>
        <div className="opsTitle"><CircleDollarSign size={19}/><strong>{ar ? `اشتراك ${tenantName || ""}` : `${tenantName || "Company"} subscription`}</strong></div>
        <div className="formGrid">
          <label>{ar ? "الخطة" : "Plan"}<select name="plan" defaultValue={subscription?.plan || "professional"} key={subscription?.id || tenantId}><option value="starter">Starter</option><option value="professional">Professional</option><option value="enterprise">Enterprise</option></select></label>
          <label>{ar ? "الحالة" : "Status"}<select name="status" defaultValue={subscription?.status || "active"} key={(subscription?.id || tenantId)+"status"}><option value="trial">Trial</option><option value="active">Active</option><option value="past_due">Past Due</option><option value="cancelled">Cancelled</option></select></label>
          <label>{ar ? "الدورة" : "Cycle"}<select name="billing_cycle" defaultValue={subscription?.billing_cycle || "monthly"}><option value="monthly">Monthly</option><option value="yearly">Yearly</option><option value="custom">Custom</option></select></label>
          <label>{ar ? "القيمة" : "Amount"}<input name="amount" type="number" min="0" step="0.01" defaultValue={Number(subscription?.amount || 0)}/></label>
          <label>{ar ? "العملة" : "Currency"}<input name="currency" defaultValue={subscription?.currency || "USD"}/></label>
        </div>
        <label className="checkLabel"><input name="apply_plan_limits" type="checkbox" defaultChecked/><span>{ar ? "تطبيق حدود الخطة" : "Apply plan limits"}</span></label>
        <label className="checkLabel"><input name="cancel_at_period_end" type="checkbox" defaultChecked={subscription?.cancel_at_period_end}/><span>{ar ? "إلغاء بنهاية الفترة" : "Cancel at period end"}</span></label>
        <button className="primaryButton" disabled={busy==="subscription"}><CheckCircle2 size={16}/>{ar ? "حفظ الاشتراك" : "Save subscription"}</button>
      </form>

      <form className="panel commercialForm" onSubmit={createInvoice}>
        <div className="opsTitle"><FileText size={19}/><strong>{ar ? "فاتورة جديدة" : "New invoice"}</strong></div>
        <div className="formGrid">
          <label>{ar ? "المبلغ" : "Subtotal"}<input name="subtotal" type="number" min="0.01" step="0.01" required/></label>
          <label>{ar ? "الضريبة" : "Tax"}<input name="tax_amount" type="number" min="0" step="0.01" defaultValue="0"/></label>
          <label>{ar ? "العملة" : "Currency"}<input name="currency" defaultValue={subscription?.currency || "USD"}/></label>
          <label>{ar ? "الاستحقاق" : "Due"}<input name="due_at" type="datetime-local"/></label>
        </div>
        <label>{ar ? "الوصف" : "Description"}<textarea name="description" rows={3}/></label>
        <button className="primaryButton" disabled={busy==="invoice"}><Plus size={16}/>{ar ? "إنشاء الفاتورة" : "Create invoice"}</button>
      </form>
    </div>}

    {tenantId && <section className="panel invoicePanel">
      <div className="panelHead"><h2>{ar ? "الفواتير" : "Invoices"}</h2><span>{invoices.length}</span></div>
      <div className="invoiceRows">{invoices.map((invoice) => <article key={invoice.id}>
        <div><strong>{invoice.number}</strong><span>{invoice.description || "—"} · {new Date(invoice.created_at).toLocaleDateString(ar?"ar-EG":"en-US")}</span></div>
        <b>{Number(invoice.total).toLocaleString()} {invoice.currency}</b>
        <span className={`statusBadge status-${invoice.status}`}>{invoice.status}</span>
        <div className="invoiceActions">{invoice.status !== "paid" && invoice.status !== "void" && <button className="secondaryButton" onClick={() => void invoiceAction(invoice.id,"void")}>{ar?"إلغاء":"Void"}</button>}</div>
      </article>)}</div>
    </section>}

    <div className="commercialGrid">
      <form className="panel commercialForm" onSubmit={createTemplate}>
        <div className="opsTitle"><Layers3 size={19}/><strong>{ar ? "إنشاء قالب شركة" : "Create tenant template"}</strong></div>
        <label>{ar ? "اسم القالب" : "Template name"}<input name="name" required placeholder="Real Estate Pro"/></label>
        <label>{ar ? "الوصف" : "Description"}<textarea name="description" rows={3}/></label>
        <div className="formGrid">
          <label>{ar ? "الخطة" : "Plan"}<select name="plan" defaultValue="professional"><option value="starter">Starter</option><option value="professional">Professional</option><option value="enterprise">Enterprise</option></select></label>
          <label>{ar ? "اللون" : "Color"}<input name="primary_color" type="color" defaultValue="#0B1F33"/></label>
          <label>{ar ? "الاشتراك" : "Subscription"}<input name="subscription_amount" type="number" min="0" step="0.01" defaultValue="0"/></label>
          <label>{ar ? "العملة" : "Currency"}<input name="subscription_currency" defaultValue="USD"/></label>
          <label>{ar ? "الدورة" : "Cycle"}<select name="billing_cycle" defaultValue="monthly"><option value="monthly">Monthly</option><option value="yearly">Yearly</option></select></label>
        </div>
        <label>{ar ? "التكاملات الافتراضية مفصولة بفاصلة" : "Default integrations, comma separated"}<input name="integration_providers" defaultValue="whatsapp,google-search-console,openai"/></label>
        <div className="templateFlags"><label className="checkLabel"><input name="feature_seo" type="checkbox" defaultChecked/><span>SEO</span></label><label className="checkLabel"><input name="feature_whatsapp" type="checkbox" defaultChecked/><span>WhatsApp</span></label><label className="checkLabel"><input name="feature_ai" type="checkbox" defaultChecked/><span>AI Sales</span></label><label className="checkLabel"><input name="powered_by_nexvary" type="checkbox" defaultChecked/><span>Powered by NEXVARY</span></label></div>
        <button className="primaryButton" disabled={busy==="template"}><Plus size={16}/>{ar ? "حفظ القالب" : "Save template"}</button>
      </form>

      <form className="panel commercialForm" onSubmit={provision}>
        <div className="opsTitle"><Sparkles size={19}/><strong>{ar ? "إنشاء شركة بضغطة واحدة" : "One-click tenant provisioning"}</strong></div>
        <label>{ar ? "القالب" : "Template"}<select name="template_id" required><option value="">{ar?"اختر قالبًا":"Select template"}</option>{templates.map(t=><option key={t.id} value={t.id}>{t.name} · {t.plan}</option>)}</select></label>
        <div className="formGrid">
          <label>{ar ? "اسم الشركة" : "Company"}<input name="company_name" required/></label>
          <label>{ar ? "المعرّف" : "Slug"}<input name="company_slug" required pattern="[a-z0-9][a-z0-9-]{1,98}[a-z0-9]"/></label>
          <label>{ar ? "الاسم التجاري" : "Brand"}<input name="brand_name"/></label>
          <label>{ar ? "اسم المالك" : "Owner"}<input name="owner_name" required/></label>
          <label>{ar ? "بريد المالك" : "Owner email"}<input name="owner_email" type="email" required/></label>
          <label>{ar ? "كلمة المرور" : "Owner password"}<input name="owner_password" type="password" minLength={10} required/></label>
          <label>{ar ? "النطاق" : "Custom domain"}<input name="custom_domain" placeholder="crm.company.com"/></label>
          <label>{ar ? "الموقع" : "Website"}<input name="website_url" type="url"/></label>
          <label>{ar ? "بريد التواصل" : "Contact email"}<input name="contact_email" type="email"/></label>
        </div>
        <button className="primaryButton" disabled={busy==="provision"}><Building2 size={16}/>{ar ? "إنشاء الشركة كاملة" : "Provision company"}</button>
      </form>
    </div>

    <section className="panel templateShelf">
      <div className="panelHead"><div><h2>{ar ? "القوالب الجاهزة" : "Tenant templates"}</h2><span>{templates.length}</span></div><button className="secondaryButton" onClick={() => void seedDefaults()} disabled={busy==="seed"}>{busy==="seed" ? <RefreshCw size={15} className="spin"/> : <Sparkles size={15}/>} {ar ? "القوالب الافتراضية" : "Default templates"}</button></div>
      <div className="templateCards">{templates.map(t=><article key={t.id}><span className="templateColor" style={{background:t.primary_color}}/><div><strong>{t.name}</strong><span>{t.plan} · {t.max_users} users · {t.max_units.toLocaleString()} units</span><small>{t.integration_providers.join(" · ") || "No integrations"}</small></div><b>{Number(t.subscription_amount).toLocaleString()} {t.subscription_currency}/{t.billing_cycle}</b></article>)}</div>
    </section>

    <BankTransferAdmin token={token} locale={locale} />
  </section>;
}
