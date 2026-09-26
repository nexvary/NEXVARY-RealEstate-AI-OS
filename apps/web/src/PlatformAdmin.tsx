import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowLeft,
  ArrowRight,
  Building2,
  CheckCircle2,
  CircleDollarSign,
  Globe2,
  KeyRound,
  Languages,
  LogOut,
  Plus,
  RefreshCw,
  Save,
  Settings2,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";

type Locale = "ar" | "en";

const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? "http://localhost:8000" : window.location.origin);
const PLATFORM_SESSION_KEY = "nexvary-platform-admin-session";

type PlatformAdmin = {
  id: string;
  email: string;
  display_name: string;
};

type PlatformSession = {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
  admin: PlatformAdmin;
};

type PlatformStatus = {
  configured: boolean;
  admin_count: number;
};

type Overview = {
  tenants_total: number;
  tenants_active: number;
  tenants_trial: number;
  tenants_suspended: number;
  users_total: number;
  projects_total: number;
  units_total: number;
  ai_requests_current_month: number;
};

type TenantPlan = "starter" | "professional" | "enterprise";
type TenantLifecycle = "active" | "trial" | "suspended";

type Tenant = {
  id: string;
  name: string;
  slug: string;
  brand_name?: string | null;
  primary_color: string;
  created_at: string;
  plan: TenantPlan;
  lifecycle: TenantLifecycle;
  custom_domain?: string | null;
  powered_by_nexvary: boolean;
  logo_data_url?: string | null;
  contact_email?: string | null;
  website_url?: string | null;
  facebook_url?: string | null;
  linkedin_url?: string | null;
  youtube_url?: string | null;
  x_url?: string | null;
  tiktok_url?: string | null;
  max_users: number;
  max_projects: number;
  max_units: number;
  max_monthly_ai_requests: number;
  users_count: number;
  projects_count: number;
  units_count: number;
  leads_count: number;
  ai_requests_current_month: number;
};

type Integration = {
  id: string;
  tenant_id: string;
  provider: string;
  display_name: string;
  is_enabled: boolean;
  public_config: Record<string, unknown>;
  secret_keys: string[];
  updated_at: string;
};

function readPlatformSession(): PlatformSession | null {
  try {
    const raw = sessionStorage.getItem(PLATFORM_SESSION_KEY);
    return raw ? JSON.parse(raw) as PlatformSession : null;
  } catch {
    return null;
  }
}

async function platformApi<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Authorization", `Bearer ${token}`);
  if (init?.body) headers.set("Content-Type", "application/json");
  const response = await fetch(`${API_URL}${path}`, { ...init, headers });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const error = new Error(body?.detail || `HTTP ${response.status}`) as Error & { status?: number };
    error.status = response.status;
    throw error;
  }
  return body as T;
}

export default function PlatformAdminCenter({
  locale,
  setLocale,
  onBack,
}: {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  onBack: () => void;
}) {
  const [session, setSession] = useState<PlatformSession | null>(() => readPlatformSession());

  if (!session) {
    return (
      <PlatformLogin
        locale={locale}
        setLocale={setLocale}
        onBack={onBack}
        onAuthenticated={(next) => {
          sessionStorage.setItem(PLATFORM_SESSION_KEY, JSON.stringify(next));
          setSession(next);
        }}
      />
    );
  }

  return (
    <PlatformConsole
      locale={locale}
      setLocale={setLocale}
      session={session}
      onBack={onBack}
      onSignOut={() => {
        sessionStorage.removeItem(PLATFORM_SESSION_KEY);
        setSession(null);
      }}
    />
  );
}

function PlatformLogin({
  locale,
  setLocale,
  onBack,
  onAuthenticated,
}: {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  onBack: () => void;
  onAuthenticated: (session: PlatformSession) => void;
}) {
  const ar = locale === "ar";
  const [status, setStatus] = useState<PlatformStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_URL}/api/v1/platform/status`)
      .then((response) => response.json())
      .then((data: PlatformStatus) => setStatus(data))
      .catch(() => setStatus({ configured: true, admin_count: 1 }));
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const data = new FormData(event.currentTarget);
    const configured = status?.configured !== false;
    const path = configured ? "/api/v1/platform/auth/login" : "/api/v1/platform/auth/claim";
    const payload = configured
      ? {
          email: String(data.get("email") || "").trim(),
          password: String(data.get("password") || ""),
        }
      : {
          tenant_slug: String(data.get("tenant_slug") || "").trim().toLowerCase(),
          email: String(data.get("email") || "").trim(),
          password: String(data.get("password") || ""),
        };

    try {
      const response = await fetch(`${API_URL}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const body = await response.json().catch(() => null);
      if (!response.ok) throw new Error(body?.detail || "Platform login failed");
      onAuthenticated(body as PlatformSession);
    } catch (err) {
      setError(err instanceof Error ? err.message : (ar ? "تعذر تسجيل الدخول." : "Sign-in failed."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="loginPage platformLoginPage" dir={ar ? "rtl" : "ltr"}>
      <div className="platformLoginActions">
        <button className="iconButton" onClick={onBack}>
          {ar ? <ArrowRight size={18}/> : <ArrowLeft size={18}/>}
          {ar ? "العودة لدخول الشركة" : "Company login"}
        </button>
        <button className="iconButton" onClick={() => setLocale(ar ? "en" : "ar")}>
          <Languages size={18}/>{ar ? "EN" : "AR"}
        </button>
      </div>
      <div className="loginGlow" />
      <section className="loginCard platformLoginCard">
        <div className="loginBrand">
          <div className="logoMark">N</div>
          <div><strong>NEXVARY Platform Admin</strong><span>RealEstate AI SaaS Control Plane</span></div>
        </div>
        <div className="loginHeroIcon"><ShieldCheck size={29}/></div>
        <span className="eyebrow">NEXVARY CONTROL PLANE</span>
        <h1>{ar ? "إدارة جميع شركات العقارات" : "Manage every real-estate company"}</h1>
        <p>
          {status?.configured === false
            ? (ar ? "هذه نسخة مطورة من إصدار سابق. أدخل بيانات مالك الشركة الأولى لتفعيل لوحة إدارة المنصة بدون أوامر." : "This is an upgraded installation. Use the first company owner's credentials to activate the platform console.")
            : (ar ? "هذه اللوحة مخصصة لإدارة الشركات والخطط والحدود والهوية والتكاملات على مستوى المنصة." : "This console manages companies, plans, limits, branding and integrations across the platform.")}
        </p>
        <form onSubmit={submit}>
          {status?.configured === false && (
            <label>{ar ? "معرّف الشركة الأولى" : "First company identifier"}<input name="tenant_slug" required placeholder="company-name" /></label>
          )}
          <label>{ar ? "البريد الإلكتروني" : "Email"}<input name="email" type="email" required autoComplete="username"/></label>
          <label>{ar ? "كلمة المرور" : "Password"}<input name="password" type="password" minLength={10} required autoComplete="current-password"/></label>
          {error && <div className="formError">{error}</div>}
          <button className="primaryButton loginSubmit" type="submit" disabled={busy}>
            {busy ? <RefreshCw size={18} className="spin"/> : <ShieldCheck size={18}/>}
            {status?.configured === false
              ? (ar ? "تفعيل لوحة المنصة" : "Activate platform console")
              : (ar ? "دخول إدارة المنصة" : "Enter platform admin")}
          </button>
        </form>
        <div className="secureNote"><span className="statusDot"/>{ar ? "جلسة Platform Admin مستقلة عن حسابات الشركات" : "Platform Admin session is isolated from tenant accounts"}</div>
      </section>
    </div>
  );
}

function PlatformConsole({
  locale,
  setLocale,
  session,
  onBack,
  onSignOut,
}: {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  session: PlatformSession;
  onBack: () => void;
  onSignOut: () => void;
}) {
  const ar = locale === "ar";
  const [overview, setOverview] = useState<Overview | null>(null);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [createOpen, setCreateOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [tenantLogoData, setTenantLogoData] = useState<string | null>(null);

  const selected = useMemo(() => tenants.find((item) => item.id === selectedId) || null, [tenants, selectedId]);

  async function load() {
    setBusy(true);
    setError("");
    try {
      const [o, t] = await Promise.all([
        platformApi<Overview>("/api/v1/platform/overview", session.access_token),
        platformApi<Tenant[]>("/api/v1/platform/tenants", session.access_token),
      ]);
      setOverview(o);
      setTenants(t);
      setSelectedId((current) => current || t[0]?.id || "");
    } catch (err) {
      const typed = err as Error & { status?: number };
      if (typed.status === 401) onSignOut();
      else setError(typed.message);
    } finally {
      setBusy(false);
    }
  }

  async function loadIntegrations(tenantId: string) {
    if (!tenantId) {
      setIntegrations([]);
      return;
    }
    try {
      setIntegrations(await platformApi<Integration[]>(`/api/v1/platform/tenants/${tenantId}/integrations`, session.access_token));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Integration load failed");
    }
  }

  useEffect(() => { void load(); }, [session.access_token]);
  useEffect(() => { void loadIntegrations(selectedId); }, [selectedId]);
  useEffect(() => { setTenantLogoData(selected?.logo_data_url || null); }, [selectedId, selected?.logo_data_url]);

  async function createTenant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setError("");
    setNotice("");
    try {
      const created = await platformApi<Tenant>("/api/v1/platform/tenants", session.access_token, {
        method: "POST",
        body: JSON.stringify({
          company_name: String(data.get("company_name") || "").trim(),
          company_slug: String(data.get("company_slug") || "").trim().toLowerCase(),
          brand_name: String(data.get("brand_name") || "").trim() || null,
          primary_color: String(data.get("primary_color") || "#0B1F33"),
          owner_name: String(data.get("owner_name") || "").trim(),
          owner_email: String(data.get("owner_email") || "").trim(),
          owner_password: String(data.get("owner_password") || ""),
          plan: String(data.get("plan") || "professional"),
          lifecycle: String(data.get("lifecycle") || "active"),
          custom_domain: String(data.get("custom_domain") || "").trim() || null,
          powered_by_nexvary: data.get("powered_by_nexvary") === "on",
        }),
      });
      form.reset();
      setCreateOpen(false);
      setNotice(ar ? "تم إنشاء الشركة ومساحة العمل وحساب المالك." : "Company workspace and owner account created.");
      await load();
      setSelectedId(created.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    }
  }

  async function updateTenant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const data = new FormData(event.currentTarget);
    setError("");
    setNotice("");
    try {
      await platformApi<Tenant>(`/api/v1/platform/tenants/${selected.id}`, session.access_token, {
        method: "PATCH",
        body: JSON.stringify({
          brand_name: String(data.get("brand_name") || "").trim(),
          primary_color: String(data.get("primary_color") || "#0B1F33"),
          plan: String(data.get("plan") || selected.plan),
          lifecycle: String(data.get("lifecycle") || selected.lifecycle),
          custom_domain: String(data.get("custom_domain") || "").trim() || null,
          powered_by_nexvary: data.get("powered_by_nexvary") === "on",
          logo_data_url: tenantLogoData,
          contact_email: String(data.get("contact_email") || "").trim() || null,
          website_url: String(data.get("website_url") || "").trim() || null,
          facebook_url: String(data.get("facebook_url") || "").trim() || null,
          linkedin_url: String(data.get("linkedin_url") || "").trim() || null,
          youtube_url: String(data.get("youtube_url") || "").trim() || null,
          x_url: String(data.get("x_url") || "").trim() || null,
          tiktok_url: String(data.get("tiktok_url") || "").trim() || null,
          max_users: Number(data.get("max_users") || selected.max_users),
          max_projects: Number(data.get("max_projects") || selected.max_projects),
          max_units: Number(data.get("max_units") || selected.max_units),
          max_monthly_ai_requests: Number(data.get("max_monthly_ai_requests") || selected.max_monthly_ai_requests),
          apply_plan_defaults: data.get("apply_plan_defaults") === "on",
        }),
      });
      setNotice(ar ? "تم تحديث إعدادات الشركة." : "Company settings updated.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    }
  }

  async function saveIntegration(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    const provider = String(data.get("provider") || "").trim().toLowerCase();
    setError("");
    setNotice("");
    try {
      const publicRaw = String(data.get("public_config") || "{}").trim() || "{}";
      const secretsRaw = String(data.get("secrets") || "").trim();
      await platformApi<Integration>(`/api/v1/platform/tenants/${selected.id}/integrations/${encodeURIComponent(provider)}`, session.access_token, {
        method: "PUT",
        body: JSON.stringify({
          display_name: String(data.get("display_name") || provider).trim(),
          is_enabled: data.get("is_enabled") === "on",
          public_config: JSON.parse(publicRaw),
          secrets: secretsRaw ? JSON.parse(secretsRaw) : null,
        }),
      });
      form.reset();
      setNotice(ar ? "تم حفظ التكامل. القيم السرية مشفرة ولا يعاد عرضها." : "Integration saved. Secret values are encrypted and never echoed back.");
      await loadIntegrations(selected.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Integration save failed");
    }
  }

  return (
    <div className="platformShell" dir={ar ? "rtl" : "ltr"}>
      <aside className="platformSidebar">
        <div className="logoMark">N</div>
        <div className="brandBlock"><strong>NEXVARY Platform</strong><span>RealEstate AI SaaS Control Plane</span></div>
        <div className="platformAdminIdentity">
          <div className="avatar">{session.admin.display_name.slice(0,1).toUpperCase()}</div>
          <div><strong>{session.admin.display_name}</strong><span>{session.admin.email}</span></div>
        </div>
        <button className="navItem" onClick={onBack}><Building2 size={18}/><span>{ar ? "دخول الشركات" : "Company login"}</span></button>
        <button className="navItem signOutButton" onClick={onSignOut}><LogOut size={18}/><span>{ar ? "تسجيل الخروج" : "Sign out"}</span></button>
        <div className="sidebarFoot"><span className="statusDot"/><div><strong>Control Plane</strong><small>Platform Admin</small></div></div>
      </aside>

      <main className="platformMain">
        <header className="platformHeader">
          <div>
            <span className="eyebrow">NEXVARY PLATFORM ADMIN</span>
            <h1>{ar ? "إدارة شركات العقارات" : "Real-estate company management"}</h1>
          </div>
          <div className="platformHeaderActions">
            <button className="iconButton" onClick={() => void load()} disabled={busy}><RefreshCw size={18} className={busy ? "spin" : ""}/></button>
            <button className="iconButton" onClick={() => setLocale(ar ? "en" : "ar")}><Languages size={18}/>{ar ? "EN" : "AR"}</button>
            <button className="primaryButton" onClick={() => setCreateOpen(true)}><Plus size={18}/>{ar ? "شركة جديدة" : "New company"}</button>
          </div>
        </header>

        <section className="platformContent">
          {error && <div className="systemError">{error}</div>}
          {notice && <div className="successNotice">{notice}</div>}

          {overview && (
            <div className="platformStats">
              <PlatformStat icon={<Building2/>} label={ar ? "الشركات" : "Companies"} value={overview.tenants_total}/>
              <PlatformStat icon={<CheckCircle2/>} label={ar ? "نشطة" : "Active"} value={overview.tenants_active}/>
              <PlatformStat icon={<Activity/>} label={ar ? "تجريبية" : "Trials"} value={overview.tenants_trial}/>
              <PlatformStat icon={<Users/>} label={ar ? "المستخدمون" : "Users"} value={overview.users_total}/>
              <PlatformStat icon={<CircleDollarSign/>} label={ar ? "الوحدات" : "Units"} value={overview.units_total}/>
              <PlatformStat icon={<Sparkles/>} label={ar ? "طلبات AI" : "AI requests"} value={overview.ai_requests_current_month}/>
            </div>
          )}

          <div className="platformGrid">
            <section className="panel tenantDirectory">
              <div className="panelHead"><div><span>Tenants</span><h2>{ar ? "الشركات المسجلة" : "Registered companies"}</h2></div><span>{tenants.length}</span></div>
              <div className="tenantSearchList">
                {tenants.map((tenant) => (
                  <button key={tenant.id} className={selectedId === tenant.id ? "tenantSelect active" : "tenantSelect"} onClick={() => setSelectedId(tenant.id)}>
                    <div className="tenantBrandDot" style={{ background: tenant.primary_color }}/>
                    <div><strong>{tenant.brand_name || tenant.name}</strong><span>{tenant.slug} · {tenant.plan}</span></div>
                    <span className={`statusBadge status-${tenant.lifecycle}`}>{tenant.lifecycle}</span>
                  </button>
                ))}
              </div>
            </section>

            {selected && (
              <section className="panel tenantInspector">
                <div className="panelHead">
                  <div><span>{selected.slug}</span><h2>{selected.brand_name || selected.name}</h2></div>
                  <span className={`statusBadge status-${selected.lifecycle}`}>{selected.lifecycle}</span>
                </div>

                <div className="tenantMetricGrid">
                  <MiniMetric label={ar ? "المستخدمون" : "Users"} value={`${selected.users_count} / ${selected.max_users}`}/>
                  <MiniMetric label={ar ? "المشروعات" : "Projects"} value={`${selected.projects_count} / ${selected.max_projects}`}/>
                  <MiniMetric label={ar ? "الوحدات" : "Units"} value={`${selected.units_count} / ${selected.max_units}`}/>
                  <MiniMetric label={ar ? "العملاء" : "Leads"} value={String(selected.leads_count)}/>
                  <MiniMetric label={ar ? "AI هذا الشهر" : "AI this month"} value={`${selected.ai_requests_current_month} / ${selected.max_monthly_ai_requests}`}/>
                </div>

                <form className="platformTenantForm" onSubmit={updateTenant} key={selected.id}>
                  <div className="formGrid">
                    <label>{ar ? "الاسم التجاري" : "Brand name"}<input name="brand_name" defaultValue={selected.brand_name || selected.name}/></label>
                    <label>{ar ? "لون الهوية" : "Brand color"}<input name="primary_color" type="color" defaultValue={selected.primary_color}/></label>
                    <label>{ar ? "الخطة" : "Plan"}<select name="plan" defaultValue={selected.plan}><option value="starter">Starter</option><option value="professional">Professional</option><option value="enterprise">Enterprise</option></select></label>
                    <label>{ar ? "الحالة" : "Lifecycle"}<select name="lifecycle" defaultValue={selected.lifecycle}><option value="active">Active</option><option value="trial">Trial</option><option value="suspended">Suspended</option></select></label>
                    <label>{ar ? "النطاق المخصص" : "Custom domain"}<input name="custom_domain" defaultValue={selected.custom_domain || ""} placeholder="crm.company.com"/></label>
                    <label className="checkLabel"><input name="powered_by_nexvary" type="checkbox" defaultChecked={selected.powered_by_nexvary}/><span>{ar ? "إظهار Powered by NEXVARY" : "Show Powered by NEXVARY"}</span></label>
                    <label>{ar ? "بريد التواصل" : "Contact email"}<input name="contact_email" type="email" defaultValue={selected.contact_email || ""}/></label>
                    <label>{ar ? "الموقع الإلكتروني" : "Website"}<input name="website_url" defaultValue={selected.website_url || ""}/></label>
                    <label>Facebook<input name="facebook_url" defaultValue={selected.facebook_url || ""}/></label>
                    <label>LinkedIn<input name="linkedin_url" defaultValue={selected.linkedin_url || ""}/></label>
                    <label>YouTube<input name="youtube_url" defaultValue={selected.youtube_url || ""}/></label>
                    <label>X<input name="x_url" defaultValue={selected.x_url || ""}/></label>
                    <label>TikTok<input name="tiktok_url" defaultValue={selected.tiktok_url || ""}/></label>
                    <label>{ar ? "حد المستخدمين" : "User limit"}<input name="max_users" type="number" min="1" defaultValue={selected.max_users}/></label>
                    <label>{ar ? "حد المشروعات" : "Project limit"}<input name="max_projects" type="number" min="1" defaultValue={selected.max_projects}/></label>
                    <label>{ar ? "حد الوحدات" : "Unit limit"}<input name="max_units" type="number" min="1" defaultValue={selected.max_units}/></label>
                    <label>{ar ? "طلبات AI شهريًا" : "Monthly AI requests"}<input name="max_monthly_ai_requests" type="number" min="0" defaultValue={selected.max_monthly_ai_requests}/></label>
                  </div>
                  <div className="platformBrandAsset">
                    <div className="brandLogoPreview">
                      {tenantLogoData ? <img src={tenantLogoData} alt={selected.brand_name || selected.name}/> : <Building2 size={28}/>}
                    </div>
                    <label>{ar ? "شعار الشركة PNG/JPG/WEBP" : "Company logo PNG/JPG/WEBP"}
                      <input type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => {
                        const file = event.target.files?.[0];
                        if (!file) return;
                        if (file.size > 1_000_000) {
                          setError(ar ? "حجم الشعار يجب ألا يتجاوز 1 ميجابايت." : "Logo must be 1 MB or smaller.");
                          event.target.value = "";
                          return;
                        }
                        const reader = new FileReader();
                        reader.onload = () => setTenantLogoData(typeof reader.result === "string" ? reader.result : null);
                        reader.readAsDataURL(file);
                      }}/>
                    </label>
                    {tenantLogoData && <button type="button" className="secondaryButton" onClick={() => setTenantLogoData(null)}>{ar ? "إزالة الشعار" : "Remove logo"}</button>}
                  </div>
                  <label className="checkLabel planDefaults"><input name="apply_plan_defaults" type="checkbox"/><span>{ar ? "تطبيق الحدود الافتراضية للخطة المختارة" : "Apply selected plan defaults"}</span></label>
                  <button className="primaryButton" type="submit"><Save size={17}/>{ar ? "حفظ إعدادات الشركة" : "Save company settings"}</button>
                </form>
              </section>
            )}
          </div>

          {selected && (
            <div className="platformGrid integrationsGrid">
              <form className="panel integrationEditor" onSubmit={saveIntegration}>
                <div className="opsTitle"><KeyRound size={19}/><strong>{ar ? "تكاملات الشركة" : "Tenant integrations"}</strong></div>
                <p className="platformHint">{ar ? "يمكن حفظ مفاتيح WhatsApp أو OpenAI أو Telegram وغيرها. الأسرار تشفر في قاعدة البيانات ولا تعاد للواجهة." : "Store WhatsApp, OpenAI, Telegram or other credentials. Secrets are encrypted at rest and are never returned to the UI."}</p>
                <div className="formGrid">
                  <label>Provider<select name="provider" defaultValue="whatsapp"><option value="whatsapp">WhatsApp</option><option value="openai">OpenAI</option><option value="telegram">Telegram</option><option value="instagram">Instagram</option><option value="messenger">Messenger</option><option value="custom">Custom</option></select></label>
                  <label>{ar ? "الاسم الظاهر" : "Display name"}<input name="display_name" defaultValue="WhatsApp Business" required/></label>
                </div>
                <label>{ar ? "إعدادات عامة JSON" : "Public config JSON"}<textarea name="public_config" rows={5} defaultValue={'{"phone_number_id":""}'}/></label>
                <label>{ar ? "بيانات سرية JSON — لا يعاد عرضها بعد الحفظ" : "Secret JSON — never echoed after save"}<textarea name="secrets" rows={5} placeholder={'{"access_token":"...","app_secret":"..."}'}/></label>
                <label className="checkLabel"><input name="is_enabled" type="checkbox"/><span>{ar ? "تفعيل التكامل" : "Enable integration"}</span></label>
                <button className="primaryButton" type="submit"><KeyRound size={17}/>{ar ? "حفظ التكامل المشفر" : "Save encrypted integration"}</button>
              </form>

              <section className="panel integrationList">
                <div className="panelHead"><div><span>Integrations</span><h2>{ar ? "التكاملات المحفوظة" : "Configured integrations"}</h2></div><span>{integrations.length}</span></div>
                {integrations.map((item) => (
                  <article key={item.id} className="integrationRow">
                    <div className="integrationIcon"><Globe2 size={18}/></div>
                    <div><strong>{item.display_name}</strong><span>{item.provider} · {item.secret_keys.length ? `${item.secret_keys.length} secret keys` : "no secrets"}</span></div>
                    <span className={`statusBadge ${item.is_enabled ? "status-active" : "status-blocked"}`}>{item.is_enabled ? "enabled" : "disabled"}</span>
                  </article>
                ))}
                {!integrations.length && <div className="emptyRow">{ar ? "لا توجد تكاملات لهذه الشركة بعد." : "No integrations configured for this company."}</div>}
              </section>
            </div>
          )}
        </section>
      </main>

      {createOpen && (
        <div className="modalBackdrop" onMouseDown={() => setCreateOpen(false)}>
          <form className="modal platformCreateModal" onSubmit={createTenant} onMouseDown={(event) => event.stopPropagation()}>
            <div className="modalHead"><div><span className="eyebrow">CREATE TENANT</span><h2>{ar ? "إنشاء شركة جديدة" : "Create new company"}</h2></div><button className="closeButton" type="button" onClick={() => setCreateOpen(false)}>×</button></div>
            <div className="formGrid">
              <label>{ar ? "اسم الشركة" : "Company name"}<input name="company_name" required autoFocus/></label>
              <label>{ar ? "معرّف الشركة" : "Company identifier"}<input name="company_slug" required pattern="[a-z0-9][a-z0-9-]{1,98}[a-z0-9]" placeholder="atlas-realty"/></label>
              <label>{ar ? "الاسم التجاري" : "Brand name"}<input name="brand_name"/></label>
              <label>{ar ? "لون الهوية" : "Brand color"}<input name="primary_color" type="color" defaultValue="#0B1F33"/></label>
              <label>{ar ? "اسم المالك" : "Owner name"}<input name="owner_name" required/></label>
              <label>{ar ? "بريد المالك" : "Owner email"}<input name="owner_email" type="email" required/></label>
              <label>{ar ? "كلمة مرور المالك" : "Owner password"}<input name="owner_password" type="password" minLength={10} required/></label>
              <label>{ar ? "الخطة" : "Plan"}<select name="plan" defaultValue="professional"><option value="starter">Starter</option><option value="professional">Professional</option><option value="enterprise">Enterprise</option></select></label>
              <label>{ar ? "الحالة" : "Lifecycle"}<select name="lifecycle" defaultValue="active"><option value="active">Active</option><option value="trial">Trial</option><option value="suspended">Suspended</option></select></label>
              <label>{ar ? "نطاق مخصص" : "Custom domain"}<input name="custom_domain" placeholder="crm.company.com"/></label>
            </div>
            <label className="checkLabel"><input name="powered_by_nexvary" type="checkbox" defaultChecked/><span>{ar ? "إظهار Powered by NEXVARY" : "Show Powered by NEXVARY"}</span></label>
            <div className="modalActions"><button className="secondaryButton" type="button" onClick={() => setCreateOpen(false)}>{ar ? "إلغاء" : "Cancel"}</button><button className="primaryButton" type="submit"><Plus size={17}/>{ar ? "إنشاء الشركة" : "Create company"}</button></div>
          </form>
        </div>
      )}
    </div>
  );
}

function PlatformStat({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return <div className="platformStat"><div>{icon}</div><strong>{value.toLocaleString()}</strong><span>{label}</span></div>;
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return <div className="miniMetric"><span>{label}</span><strong>{value}</strong></div>;
}
