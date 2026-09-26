import { CSSProperties, FormEvent, ReactNode, useEffect, useMemo, useState } from "react";
import { AICopilotOps, FinanceOps, InventoryOps, InboxOps, KnowledgeOps, SettingsOps, TasksOps, TeamOps } from "./Operations";
import PlatformAdminCenter from "./PlatformAdmin";

import {
  ArrowLeft,
  ArrowRight,
  BedDouble,
  Bot,
  BookOpen,
  Building2,
  CalendarDays,
  ClipboardCheck,
  ChevronLeft,
  CircleDollarSign,
  Home,
  Info,
  KeyRound,
  Languages,
  LayoutDashboard,
  LogOut,
  MapPin,
  MessageSquare,
  Plus,
  RefreshCw,
  Ruler,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";

type Locale = "ar" | "en";
type View = "dashboard" | "leads" | "inventory" | "manage" | "appointments" | "finance" | "inbox" | "knowledge" | "tasks" | "team" | "settings" | "ai" | "about";

type User = {
  id: string;
  tenant_id: string;
  email: string;
  display_name: string;
  role: string;
  is_active: number;
};

type AuthSession = {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
  user: User;
};

type SetupStatus = {
  needs_setup: boolean;
  tenant_count: number;
  desktop_mode: boolean;
};

type BootstrapResponse = {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
  tenant_id: string;
  tenant_slug: string;
  user_id: string;
  user_email: string;
  user_name: string;
  role: string;
};

type Overview = {
  leads_total: number;
  leads_hot: number;
  units_available: number;
  appointments_total: number;
  active_reservations: number;
};

type Pipeline = Record<"new" | "qualified" | "viewing" | "negotiation" | "won" | "lost", number>;

type Lead = {
  id: string;
  full_name: string;
  phone: string;
  email?: string | null;
  source: string;
  preferred_city?: string | null;
  budget?: number | null;
  bedrooms?: number | null;
  status: keyof Pipeline;
  score: number;
  created_at: string;
};

type Unit = {
  id: string;
  project_id: string;
  building_id?: string | null;
  payment_plan_id?: string | null;
  code: string;
  unit_type: string;
  bedrooms?: number | null;
  area_sqm: number;
  price: number;
  currency: string;
  status: "available" | "reserved" | "sold" | "blocked";
};

type Appointment = {
  id: string;
  lead_id: string;
  project_id?: string | null;
  assigned_user_id?: string | null;
  starts_at: string;
  notes?: string | null;
  status: string;
};

type TenantSettings = {
  id: string;
  name: string;
  slug: string;
  brand_name?: string | null;
  primary_color: string;
  logo_data_url?: string | null;
  contact_email?: string | null;
  website_url?: string | null;
  facebook_url?: string | null;
  linkedin_url?: string | null;
  youtube_url?: string | null;
  x_url?: string | null;
  tiktok_url?: string | null;
  custom_domain?: string | null;
  powered_by_nexvary: boolean;
  plan: string;
  lifecycle: string;
};

const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? "http://localhost:8000" : window.location.origin);
const SESSION_KEY = "nexvary-realestate-session";

const copy = {
  ar: {
    brand: "NEXVARY العقاري",
    subtitle: "نظام التشغيل العقاري بالذكاء الاصطناعي",
    dashboard: "لوحة التحكم",
    leads: "العملاء المحتملون",
    inventory: "الوحدات والمخزون",
    manage: "إدارة المخزون",
    appointments: "المعاينات",
    finance: "العقود والمالية",
    inbox: "المحادثات",
    knowledge: "قاعدة المعرفة",
    tasks: "المهام والمتابعة",
    team: "الفريق والصلاحيات",
    settings: "إعدادات الشركة",
    ai: "مساعد الذكاء الاصطناعي",
    about: "عن المنصة",
    search: "ابحث داخل الصفحة الحالية...",
    addLead: "إضافة عميل",
    welcome: "مركز قيادة المبيعات",
    overview: "بيانات حية من قاعدة الشركة — لا توجد أرقام تجريبية في هذه الشاشة",
    totalLeads: "إجمالي العملاء",
    hotLeads: "عملاء جاهزون",
    available: "وحدات متاحة",
    meetings: "إجمالي المعاينات",
    reservations: "حجوزات نشطة",
    funnel: "مسار المبيعات",
    live: "بيانات حية",
    newLead: "عميل جديد",
    name: "الاسم",
    phone: "الهاتف",
    email: "البريد الإلكتروني",
    budget: "الميزانية",
    city: "المدينة المفضلة",
    bedrooms: "غرف النوم",
    source: "المصدر",
    save: "حفظ العميل",
    cancel: "إلغاء",
    aiTitle: "AI Sales Copilot",
    aiText: "السعر والتوافر والحجز تؤخذ من قاعدة البيانات فقط. يستخدم RAG للمستندات والبروشورات عندما يتم تفعيله.",
    refresh: "تحديث",
    signOut: "تسجيل الخروج",
    back: "رجوع",
    loading: "جارٍ تحميل بيانات الشركة...",
    noLeads: "لا توجد عملاء مطابقون للبحث.",
    noUnits: "لا توجد وحدات مطابقة للبحث.",
    noAppointments: "لا توجد معاينات مسجلة.",
    role: "الصلاحية",
    loginTitle: "الدخول إلى مركز القيادة",
    loginText: "أدخل بيانات شركة العقارات وحسابك للوصول إلى البيانات المعزولة الخاصة بالشركة.",
    companySlug: "معرّف الشركة",
    password: "كلمة المرور",
    login: "تسجيل الدخول",
    loginBusy: "جارٍ التحقق...",
    loginError: "تعذر تسجيل الدخول. راجع معرّف الشركة والبريد وكلمة المرور.",
    systemError: "تعذر تحميل البيانات من الخادم.",
    status: "الحالة",
    area: "المساحة",
    price: "السعر",
    unit: "الوحدة",
    appointmentTime: "موعد المعاينة",
    secure: "جلسة مشفرة ومحمية بصلاحيات المستخدم",
  },
  en: {
    brand: "NEXVARY RealEstate",
    subtitle: "AI-powered real estate operating system",
    dashboard: "Dashboard",
    leads: "Leads",
    inventory: "Inventory",
    manage: "Inventory Management",
    appointments: "Viewings",
    finance: "Contracts & Finance",
    inbox: "Inbox",
    knowledge: "Knowledge Base",
    tasks: "Tasks",
    team: "Team & Roles",
    settings: "Company Settings",
    ai: "AI Assistant",
    about: "About",
    search: "Search the current view...",
    addLead: "Add lead",
    welcome: "Sales Command Center",
    overview: "Live company data — no demo counters are used on this screen",
    totalLeads: "Total leads",
    hotLeads: "Hot leads",
    available: "Available units",
    meetings: "Total viewings",
    reservations: "Active reservations",
    funnel: "Sales funnel",
    live: "Live data",
    newLead: "New lead",
    name: "Name",
    phone: "Phone",
    email: "Email",
    budget: "Budget",
    city: "Preferred city",
    bedrooms: "Bedrooms",
    source: "Source",
    save: "Save lead",
    cancel: "Cancel",
    aiTitle: "AI Sales Copilot",
    aiText: "Price, availability and reservations come only from transactional data. RAG will be used for documents and brochures.",
    refresh: "Refresh",
    signOut: "Sign out",
    back: "Back",
    loading: "Loading company data...",
    noLeads: "No leads match your search.",
    noUnits: "No units match your search.",
    noAppointments: "No viewings recorded.",
    role: "Role",
    loginTitle: "Enter the command center",
    loginText: "Use your company identifier and account to access the tenant-isolated workspace.",
    companySlug: "Company identifier",
    password: "Password",
    login: "Sign in",
    loginBusy: "Verifying...",
    loginError: "Sign-in failed. Check the company identifier, email and password.",
    systemError: "The server data could not be loaded.",
    status: "Status",
    area: "Area",
    price: "Price",
    unit: "Unit",
    appointmentTime: "Viewing time",
    secure: "Encrypted session protected by user permissions",
  },
};

const navItems = [
  { id: "dashboard" as View, icon: LayoutDashboard, key: "dashboard" as const },
  { id: "leads" as View, icon: Users, key: "leads" as const },
  { id: "inventory" as View, icon: Building2, key: "inventory" as const },
  { id: "manage" as View, icon: ClipboardCheck, key: "manage" as const },
  { id: "appointments" as View, icon: CalendarDays, key: "appointments" as const },
  { id: "finance" as View, icon: CircleDollarSign, key: "finance" as const },
  { id: "inbox" as View, icon: MessageSquare, key: "inbox" as const },
  { id: "knowledge" as View, icon: BookOpen, key: "knowledge" as const },
  { id: "tasks" as View, icon: ClipboardCheck, key: "tasks" as const },
  { id: "team" as View, icon: ShieldCheck, key: "team" as const },
  { id: "settings" as View, icon: Settings2, key: "settings" as const },
  { id: "ai" as View, icon: Bot, key: "ai" as const },
  { id: "about" as View, icon: Info, key: "about" as const },
];

function readSession(): AuthSession | null {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    return raw ? (JSON.parse(raw) as AuthSession) : null;
  } catch {
    return null;
  }
}

async function api<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Authorization", `Bearer ${token}`);
  if (init?.body) headers.set("Content-Type", "application/json");

  const response = await fetch(`${API_URL}${path}`, { ...init, headers });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const message = data?.detail || `HTTP ${response.status}`;
    const error = new Error(message) as Error & { status?: number };
    error.status = response.status;
    throw error;
  }
  return data as T;
}

export default function App() {
  const [locale, setLocale] = useState<Locale>("ar");
  const [session, setSession] = useState<AuthSession | null>(() => readSession());
  const [setup, setSetup] = useState<SetupStatus | null>(null);
  const [platformMode, setPlatformMode] = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/api/v1/setup/status`)
      .then((response) => response.json())
      .then((data: SetupStatus) => setSetup(data))
      .catch(() => setSetup({ needs_setup: false, tenant_count: 0, desktop_mode: false }));
  }, []);

  function acceptSession(auth: AuthSession) {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(auth));
    setSession(auth);
    setSetup((current) => current ? { ...current, needs_setup: false, tenant_count: Math.max(1, current.tenant_count) } : current);
  }

  if (platformMode) {
    return <PlatformAdminCenter locale={locale} setLocale={setLocale} onBack={() => setPlatformMode(false)} />;
  }

  if (!session && setup?.needs_setup) {
    return <FirstRunSetup locale={locale} setLocale={setLocale} onAuthenticated={acceptSession} />;
  }

  if (!session) {
    return <Login locale={locale} setLocale={setLocale} onAuthenticated={acceptSession} onPlatformAdmin={() => setPlatformMode(true)} />;
  }

  return <ControlCenter locale={locale} setLocale={setLocale} session={session} onSignOut={() => {
    sessionStorage.removeItem(SESSION_KEY);
    setSession(null);
  }} />;
}

function FirstRunSetup({
  locale,
  setLocale,
  onAuthenticated,
}: {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  onAuthenticated: (session: AuthSession) => void;
}) {
  const t = copy[locale];
  const dir = locale === "ar" ? "rtl" : "ltr";
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const data = new FormData(event.currentTarget);
    try {
      const response = await fetch(`${API_URL}/api/v1/auth/bootstrap`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_name: String(data.get("company_name") || "").trim(),
          company_slug: String(data.get("company_slug") || "").trim().toLowerCase(),
          brand_name: String(data.get("brand_name") || "").trim() || null,
          owner_name: String(data.get("owner_name") || "").trim(),
          owner_email: String(data.get("owner_email") || "").trim(),
          owner_password: String(data.get("owner_password") || ""),
        }),
      });
      const body = await response.json().catch(() => null);
      if (!response.ok) throw new Error(body?.detail || "setup failed");
      const result = body as BootstrapResponse;
      onAuthenticated({
        access_token: result.access_token,
        token_type: result.token_type,
        expires_in_minutes: result.expires_in_minutes,
        user: {
          id: result.user_id,
          tenant_id: result.tenant_id,
          email: result.user_email,
          display_name: result.user_name,
          role: result.role,
          is_active: 1,
        },
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : t.systemError);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="loginPage" dir={dir}>
      <button className="loginLanguage" onClick={() => setLocale(locale === "ar" ? "en" : "ar")}>
        <Languages size={18} /> {locale === "ar" ? "EN" : "AR"}
      </button>
      <div className="loginGlow" />
      <section className="loginCard setupCard">
        <div className="loginBrand">
          <div className="logoMark">N</div>
          <div><strong>{t.brand}</strong><span>{t.subtitle}</span></div>
        </div>
        <span className="eyebrow">FIRST OWNER SETUP</span>
        <h1>{locale === "ar" ? "إعداد الشركة لأول مرة" : "Set up your company"}</h1>
        <p>{locale === "ar" ? "أنشئ مساحة الشركة وحساب المالك الأول. بعد ذلك سيطلب البرنامج تسجيل الدخول بشكل طبيعي." : "Create the company workspace and first owner account. Later launches will use normal sign-in."}</p>
        <form onSubmit={submit}>
          <div className="formGrid">
            <label>{locale === "ar" ? "اسم الشركة" : "Company name"}<input name="company_name" required autoFocus /></label>
            <label>{locale === "ar" ? "معرّف الشركة" : "Company identifier"}<input name="company_slug" required pattern="[a-z0-9][a-z0-9-]{1,98}[a-z0-9]" placeholder="company-name" /></label>
            <label>{locale === "ar" ? "الاسم التجاري" : "Brand name"}<input name="brand_name" /></label>
            <label>{locale === "ar" ? "اسم المالك" : "Owner name"}<input name="owner_name" required /></label>
            <label>{t.email}<input name="owner_email" type="email" required /></label>
            <label>{t.password}<input name="owner_password" type="password" required minLength={10} /></label>
          </div>
          {error && <div className="formError">{error}</div>}
          <button className="primaryButton loginSubmit" type="submit" disabled={busy}>
            {busy ? <RefreshCw size={18} className="spin" /> : <KeyRound size={18} />}
            {locale === "ar" ? "إنشاء الشركة والدخول" : "Create company and enter"}
          </button>
        </form>
      </section>
    </div>
  );
}

function Login({
  locale,
  setLocale,
  onAuthenticated,
  onPlatformAdmin,
}: {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  onAuthenticated: (session: AuthSession) => void;
  onPlatformAdmin: () => void;
}) {
  const t = copy[locale];
  const dir = locale === "ar" ? "rtl" : "ltr";
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const data = new FormData(event.currentTarget);

    try {
      const response = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tenant_slug: String(data.get("tenant_slug") || "").trim().toLowerCase(),
          email: String(data.get("email") || "").trim(),
          password: String(data.get("password") || ""),
        }),
      });
      const body = await response.json().catch(() => null);
      if (!response.ok) throw new Error(body?.detail || "login failed");
      const auth = body as AuthSession;
      sessionStorage.setItem(SESSION_KEY, JSON.stringify(auth));
      onAuthenticated(auth);
    } catch {
      setError(t.loginError);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="loginPage" dir={dir}>
      <button className="loginLanguage" onClick={() => setLocale(locale === "ar" ? "en" : "ar")}>
        <Languages size={18} /> {locale === "ar" ? "EN" : "AR"}
      </button>
      <div className="loginGlow" />
      <section className="loginCard">
        <div className="loginBrand">
          <div className="logoMark">N</div>
          <div>
            <strong>{t.brand}</strong>
            <span>{t.subtitle}</span>
          </div>
        </div>
        <div className="loginHeroIcon"><KeyRound size={28} /></div>
        <span className="eyebrow">SECURE WORKSPACE</span>
        <h1>{t.loginTitle}</h1>
        <p>{t.loginText}</p>
        <form onSubmit={submit}>
          <label>{t.companySlug}<input name="tenant_slug" required autoComplete="organization" placeholder="company-name" /></label>
          <label>{t.email}<input name="email" type="email" required autoComplete="username" /></label>
          <label>{t.password}<input name="password" type="password" required minLength={10} autoComplete="current-password" /></label>
          {error && <div className="formError">{error}</div>}
          <button className="primaryButton loginSubmit" type="submit" disabled={busy}>
            {busy ? <RefreshCw size={18} className="spin" /> : <KeyRound size={18} />}
            {busy ? t.loginBusy : t.login}
          </button>
        </form>
        <button className="platformEntryButton" type="button" onClick={onPlatformAdmin}>
          <ShieldCheck size={17}/>
          {locale === "ar" ? "إدارة منصة NEXVARY والشركات" : "NEXVARY Platform Admin"}
        </button>
        <div className="secureNote"><span className="statusDot" />{t.secure}</div>
      </section>
    </div>
  );
}

function ControlCenter({
  locale,
  setLocale,
  session,
  onSignOut,
}: {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  session: AuthSession;
  onSignOut: () => void;
}) {
  const [view, setView] = useState<View>("dashboard");
  const [modalOpen, setModalOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [overview, setOverview] = useState<Overview | null>(null);
  const [pipeline, setPipeline] = useState<Pipeline | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [tenantSettings, setTenantSettings] = useState<TenantSettings | null>(null);
  const [busy, setBusy] = useState(true);
  const [systemError, setSystemError] = useState("");
  const [saving, setSaving] = useState(false);

  const t = copy[locale];
  const dir = locale === "ar" ? "rtl" : "ltr";
  const currentKey = navItems.find((item) => item.id === view)?.key ?? "dashboard";
  const title = useMemo(() => t[currentKey], [currentKey, t]);

  async function loadData() {
    setBusy(true);
    setSystemError("");
    try {
      const [overviewData, pipelineData, leadData, unitData, appointmentData, settingsData] = await Promise.all([
        api<Overview>("/api/v1/overview", session.access_token),
        api<Pipeline>("/api/v1/pipeline", session.access_token),
        api<Lead[]>("/api/v1/leads", session.access_token),
        api<Unit[]>("/api/v1/units", session.access_token),
        api<Appointment[]>("/api/v1/appointments", session.access_token),
        api<TenantSettings>("/api/v1/tenant/settings", session.access_token),
      ]);
      setOverview(overviewData);
      setPipeline(pipelineData);
      setLeads(leadData);
      setUnits(unitData);
      setAppointments(appointmentData);
      setTenantSettings(settingsData);
    } catch (error) {
      const typed = error as Error & { status?: number };
      if (typed.status === 401) {
        onSignOut();
        return;
      }
      setSystemError(t.systemError);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void loadData();
    // Session token is immutable for the life of this control-center instance.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session.access_token]);

  async function addLead(form: FormData) {
    setSaving(true);
    setSystemError("");
    try {
      await api<Lead>("/api/v1/leads", session.access_token, {
        method: "POST",
        body: JSON.stringify({
          full_name: String(form.get("name") || "").trim(),
          phone: String(form.get("phone") || "").trim(),
          email: String(form.get("email") || "").trim() || null,
          source: String(form.get("source") || "manual").trim(),
          preferred_city: String(form.get("city") || "").trim() || null,
          budget: form.get("budget") ? Number(form.get("budget")) : null,
          bedrooms: form.get("bedrooms") ? Number(form.get("bedrooms")) : null,
        }),
      });
      setModalOpen(false);
      setView("leads");
      await loadData();
    } catch (error) {
      const typed = error as Error & { status?: number };
      if (typed.status === 401) onSignOut();
      else setSystemError(typed.message || t.systemError);
    } finally {
      setSaving(false);
    }
  }

  const normalizedSearch = search.trim().toLowerCase();
  const visibleLeads = leads.filter((lead) =>
    !normalizedSearch ||
    [lead.full_name, lead.phone, lead.email || "", lead.source, lead.preferred_city || "", lead.status]
      .some((value) => value.toLowerCase().includes(normalizedSearch))
  );
  const visibleUnits = units.filter((unit) =>
    !normalizedSearch ||
    [unit.code, unit.unit_type, unit.currency, unit.status]
      .some((value) => value.toLowerCase().includes(normalizedSearch))
  );

  const tenantStyle = tenantSettings
    ? ({ "--tenant-primary": tenantSettings.primary_color } as CSSProperties)
    : undefined;

  return (
    <div className="app" dir={dir} style={tenantStyle}>
      <aside className="sidebar">
        <div className={tenantSettings?.logo_data_url ? "logoMark tenantLogoMark" : "logoMark"}>
          {tenantSettings?.logo_data_url ? <img src={tenantSettings.logo_data_url} alt={tenantSettings.brand_name || tenantSettings.name}/> : "N"}
        </div>
        <div className="brandBlock">
          <strong>{tenantSettings?.brand_name || t.brand}</strong>
          <span>{t.subtitle}</span>
        </div>
        <nav>
          {navItems.map(({ id, icon: Icon, key }) => (
            <button key={id} className={view === id ? "navItem active" : "navItem"} onClick={() => setView(id)}>
              <Icon size={19} />
              <span>{t[key]}</span>
              {view === id && <ChevronLeft size={16} className="navArrow" />}
            </button>
          ))}
        </nav>
        <div className="userCard">
          <div className="avatar">{session.user.display_name.slice(0, 1).toUpperCase()}</div>
          <div><strong>{session.user.display_name}</strong><span>{t.role}: {session.user.role}</span></div>
        </div>
        <button className="navItem signOutButton" onClick={onSignOut}><LogOut size={18}/><span>{t.signOut}</span></button>
        <div className="sidebarFoot">
          <span className="statusDot" />
          <div><strong>API + RBAC</strong><small>Authenticated</small></div>
        </div>
      </aside>

      <main className="main">
        <header>
          <div className={tenantSettings?.logo_data_url ? "mobileBrand tenantLogoMark" : "mobileBrand"}>
            {tenantSettings?.logo_data_url ? <img src={tenantSettings.logo_data_url} alt={tenantSettings.brand_name || tenantSettings.name}/> : "N"}
          </div>
          {view !== "dashboard" && (
            <button className="iconButton backButton" onClick={() => setView("dashboard")} title={t.back}>
              {locale === "ar" ? <ArrowRight size={19}/> : <ArrowLeft size={19}/>}
              <span>{t.back}</span>
            </button>
          )}
          <div className="searchBox">
            <Search size={18} />
            <input aria-label={t.search} placeholder={t.search} value={search} onChange={(event) => setSearch(event.target.value)} />
          </div>
          <button className="iconButton" onClick={() => void loadData()} title={t.refresh} disabled={busy}>
            <RefreshCw size={19} className={busy ? "spin" : ""} />
          </button>
          <button className="iconButton" onClick={() => setLocale(locale === "ar" ? "en" : "ar")} title="Language">
            <Languages size={19} /><span>{locale.toUpperCase()}</span>
          </button>
          <button className="primaryButton" onClick={() => setModalOpen(true)}>
            <Plus size={18} />{t.addLead}
          </button>
        </header>

        <section className="content">
          <div className="pageHeading">
            <div>
              <span className="eyebrow">{title}</span>
              <h1>{view === "dashboard" ? t.welcome : title}</h1>
              <p>{view === "dashboard" ? t.overview : t.subtitle}</p>
            </div>
            <span className="liveBadge"><span />{t.live}</span>
          </div>

          {systemError && <div className="systemError">{systemError}</div>}
          {busy && !overview ? <LoadingState text={t.loading} /> : null}

          {view === "dashboard" && overview && pipeline && (
            <>
              <div className="statsGrid statsFive">
                <Stat icon={<Users />} label={t.totalLeads} value={String(overview.leads_total)} />
                <Stat icon={<Sparkles />} label={t.hotLeads} value={String(overview.leads_hot)} />
                <Stat icon={<Home />} label={t.available} value={String(overview.units_available)} />
                <Stat icon={<CalendarDays />} label={t.meetings} value={String(overview.appointments_total)} />
                <Stat icon={<CircleDollarSign />} label={t.reservations} value={String(overview.active_reservations)} />
              </div>

              <div className="dashboardGrid">
                <section className="panel largePanel">
                  <div className="panelHead"><div><span>{t.funnel}</span><h2>Live Pipeline</h2></div><CircleDollarSign /></div>
                  <div className="funnel">
                    {pipelineRows(pipeline, locale).map((row) => (
                      <Funnel key={row.key} label={row.label} value={String(row.value)} width={row.width} />
                    ))}
                  </div>
                </section>

                <section className="panel aiPanel">
                  <div className="aiIcon"><Bot /></div>
                  <span className="eyebrow">NEXVARY AI</span>
                  <h2>{t.aiTitle}</h2>
                  <p>{t.aiText}</p>
                  <div className="truthRules">
                    <span>DB → Price</span><span>DB → Availability</span><span>RAG → Documents</span>
                  </div>
                  <button onClick={() => setView("ai")}>{t.ai}<ChevronLeft size={16}/></button>
                </section>
              </div>
            </>
          )}

          {view === "leads" && (
            <section className="panel tablePanel">
              <div className="panelHead"><h2>{t.leads}</h2><span>{visibleLeads.length} / {leads.length}</span></div>
              <div className="leadTable">
                {visibleLeads.map((lead) => (
                  <div className="leadRow" key={lead.id}>
                    <div className="avatar">{lead.full_name.slice(0, 1)}</div>
                    <div className="leadName"><strong>{lead.full_name}</strong><span>{lead.phone}{lead.email ? ` · ${lead.email}` : ""}</span></div>
                    <span>{lead.source}</span>
                    <span>{formatMoney(lead.budget, "EGP", locale)}</span>
                    <StatusBadge value={lead.status} />
                    <span className={lead.score >= 70 ? "score hot" : "score"}>{lead.score}</span>
                  </div>
                ))}
                {!visibleLeads.length && <div className="emptyRow">{t.noLeads}</div>}
              </div>
            </section>
          )}

          {view === "inventory" && (
            <div className="inventoryGrid">
              {visibleUnits.map((unit) => (
                <article className="unitCard" key={unit.id}>
                  <div className="unitHead"><div className="unitIcon"><Building2 size={20}/></div><StatusBadge value={unit.status}/></div>
                  <span className="eyebrow">{unit.unit_type}</span>
                  <h2>{unit.code}</h2>
                  <div className="unitFacts">
                    <span><BedDouble size={16}/>{unit.bedrooms ?? "—"}</span>
                    <span><Ruler size={16}/>{Number(unit.area_sqm).toLocaleString(locale === "ar" ? "ar-EG" : "en-US")} m²</span>
                  </div>
                  <div className="unitPrice">{formatMoney(unit.price, unit.currency, locale)}</div>
                </article>
              ))}
              {!visibleUnits.length && <section className="panel emptyState"><div className="aiIcon"><Building2/></div><h2>{t.inventory}</h2><p>{t.noUnits}</p></section>}
            </div>
          )}

          {view === "manage" && <InventoryOps token={session.access_token} locale={locale} />}
          {view === "finance" && <FinanceOps token={session.access_token} locale={locale} />}
          {view === "inbox" && <InboxOps token={session.access_token} locale={locale} />}
          {view === "knowledge" && <KnowledgeOps token={session.access_token} locale={locale} />}
          {view === "tasks" && <TasksOps token={session.access_token} locale={locale} />}
          {view === "team" && <TeamOps token={session.access_token} locale={locale} />}
          {view === "settings" && <SettingsOps token={session.access_token} locale={locale} onSaved={() => void loadData()} />}

          {view === "appointments" && (
            <section className="panel appointmentsPanel">
              <div className="panelHead"><h2>{t.appointments}</h2><span>{appointments.length}</span></div>
              <div className="appointmentList">
                {appointments.map((appointment) => (
                  <div className="appointmentRow" key={appointment.id}>
                    <div className="appointmentIcon"><CalendarDays size={19}/></div>
                    <div><strong>{formatDateTime(appointment.starts_at, locale)}</strong><span>{appointment.notes || appointment.status}</span></div>
                    <StatusBadge value={appointment.status}/>
                  </div>
                ))}
                {!appointments.length && <div className="emptyRow">{t.noAppointments}</div>}
              </div>
            </section>
          )}

          {view === "ai" && <AICopilotOps token={session.access_token} locale={locale} />}

          {view === "about" && (
            <section className="panel aboutPanel">
              <div className={tenantSettings?.logo_data_url ? "logoMark tenantLogoMark" : "logoMark"}>
                {tenantSettings?.logo_data_url ? <img src={tenantSettings.logo_data_url} alt={tenantSettings.brand_name || tenantSettings.name}/> : "N"}
              </div>
              <span className="eyebrow">{tenantSettings?.brand_name || tenantSettings?.name || t.brand}</span>
              <h2>{tenantSettings?.brand_name || tenantSettings?.name || t.brand}</h2>
              <p>{locale === "ar" ? "منصة تشغيل عقاري لإدارة المبيعات والمخزون والعملاء والأتمتة والذكاء الاصطناعي." : "Real-estate operating workspace for sales, inventory, customers, automation and AI."}</p>
              <div className="aboutLinks">
                {tenantSettings?.website_url && <a href={tenantSettings.website_url} target="_blank" rel="noreferrer">Website</a>}
                {tenantSettings?.facebook_url && <a href={tenantSettings.facebook_url} target="_blank" rel="noreferrer">Facebook</a>}
                {tenantSettings?.linkedin_url && <a href={tenantSettings.linkedin_url} target="_blank" rel="noreferrer">LinkedIn</a>}
                {tenantSettings?.youtube_url && <a href={tenantSettings.youtube_url} target="_blank" rel="noreferrer">YouTube</a>}
                {tenantSettings?.x_url && <a href={tenantSettings.x_url} target="_blank" rel="noreferrer">X</a>}
                {tenantSettings?.tiktok_url && <a href={tenantSettings.tiktok_url} target="_blank" rel="noreferrer">TikTok</a>}
                {tenantSettings?.contact_email && <a href={`mailto:${tenantSettings.contact_email}`}>Email</a>}
              </div>
              {tenantSettings?.powered_by_nexvary && (
                <div className="poweredByBlock">
                  <span>Powered by</span><strong>NEXVARY RealEstate AI OS</strong>
                  <div className="aboutLinks">
                    <a href="https://nexvary.com/" target="_blank" rel="noreferrer">NEXVARY</a>
                  </div>
                </div>
              )}
            </section>
          )}
        </section>
      </main>

      <div className="mobileNav">
        {navItems.filter((item) => item.id !== "about").map(({ id, icon: Icon, key }) => (
          <button key={id} className={view === id ? "active" : ""} onClick={() => setView(id)} aria-label={t[key]}>
            <Icon size={20}/>
          </button>
        ))}
      </div>

      {modalOpen && (
        <div className="modalBackdrop" onMouseDown={() => !saving && setModalOpen(false)}>
          <form className="modal" onSubmit={(event) => { event.preventDefault(); void addLead(new FormData(event.currentTarget)); }} onMouseDown={(event) => event.stopPropagation()}>
            <div className="modalHead"><div><span className="eyebrow">CRM</span><h2>{t.newLead}</h2></div><button type="button" className="closeButton" onClick={() => setModalOpen(false)} disabled={saving}>×</button></div>
            <div className="formGrid">
              <label>{t.name}<input name="name" required autoFocus /></label>
              <label>{t.phone}<input name="phone" required /></label>
              <label>{t.email}<input name="email" type="email" /></label>
              <label>{t.source}<input name="source" defaultValue="manual" /></label>
              <label>{t.city}<input name="city" /></label>
              <label>{t.budget}<input name="budget" type="number" min="0" step="1" /></label>
              <label>{t.bedrooms}<input name="bedrooms" type="number" min="0" max="20" /></label>
            </div>
            <div className="modalActions">
              <button type="button" className="secondaryButton" onClick={() => setModalOpen(false)} disabled={saving}>{t.cancel}</button>
              <button type="submit" className="primaryButton" disabled={saving}>{saving && <RefreshCw size={17} className="spin"/>}{t.save}</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

function pipelineRows(pipeline: Pipeline, locale: Locale) {
  const labels = locale === "ar"
    ? { new: "عملاء جدد", qualified: "مؤهلون", viewing: "معاينات", negotiation: "تفاوض", won: "تم البيع", lost: "مفقود" }
    : { new: "New leads", qualified: "Qualified", viewing: "Viewings", negotiation: "Negotiation", won: "Won", lost: "Lost" };
  const max = Math.max(...Object.values(pipeline), 1);
  return (Object.keys(labels) as Array<keyof Pipeline>).map((key) => ({
    key,
    label: labels[key],
    value: pipeline[key] || 0,
    width: `${Math.max(4, Math.round(((pipeline[key] || 0) / max) * 100))}%`,
  }));
}

function formatMoney(value: number | null | undefined, currency: string, locale: Locale) {
  if (value === null || value === undefined) return "—";
  try {
    return new Intl.NumberFormat(locale === "ar" ? "ar-EG" : "en-US", {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    }).format(Number(value));
  } catch {
    return `${Number(value).toLocaleString()} ${currency}`;
  }
}

function formatDateTime(value: string, locale: Locale) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(locale === "ar" ? "ar-EG" : "en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function Stat({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return <div className="statCard"><div className="statTop"><div className="statIcon">{icon}</div><span className="dataTag">LIVE</span></div><strong>{value}</strong><p>{label}</p></div>;
}

function Funnel({ label, value, width }: { label: string; value: string; width: string }) {
  return <div className="funnelRow"><div className="funnelMeta"><span>{label}</span><strong>{value}</strong></div><div className="funnelTrack"><div className="funnelFill" style={{ width }} /></div></div>;
}

function StatusBadge({ value }: { value: string }) {
  const safe = value.toLowerCase().replace(/[^a-z0-9_-]/g, "");
  return <span className={`statusBadge status-${safe}`}>{value}</span>;
}

function LoadingState({ text }: { text: string }) {
  return <section className="panel loadingState"><RefreshCw className="spin"/><span>{text}</span></section>;
}

function ArchitectureCard({ title, text }: { title: string; text: string }) {
  return <article><strong>{title}</strong><p>{text}</p></article>;
}
