import { useMemo, useState } from "react";
import {
  Bot,
  Building2,
  CalendarDays,
  ChevronLeft,
  CircleDollarSign,
  Home,
  Languages,
  LayoutDashboard,
  Plus,
  Search,
  Sparkles,
  Users,
} from "lucide-react";

type Locale = "ar" | "en";
type View = "dashboard" | "leads" | "inventory" | "appointments" | "ai";

type Lead = {
  name: string;
  phone: string;
  budget: string;
  source: string;
  score: number;
};

const copy = {
  ar: {
    brand: "NEXVARY العقاري",
    subtitle: "نظام التشغيل العقاري بالذكاء الاصطناعي",
    dashboard: "لوحة التحكم",
    leads: "العملاء المحتملون",
    inventory: "الوحدات والمخزون",
    appointments: "المعاينات",
    ai: "مساعد الذكاء الاصطناعي",
    search: "ابحث عن عميل، وحدة أو مشروع...",
    addLead: "إضافة عميل",
    welcome: "مساء الخير",
    overview: "نظرة فورية على حركة المبيعات اليوم",
    totalLeads: "إجمالي العملاء",
    hotLeads: "عملاء جاهزون",
    available: "وحدات متاحة",
    meetings: "معاينات اليوم",
    funnel: "مسار المبيعات",
    live: "مباشر",
    newLead: "عميل جديد",
    name: "الاسم",
    phone: "الهاتف",
    budget: "الميزانية",
    save: "حفظ العميل",
    cancel: "إلغاء",
    aiTitle: "AI Sales Copilot",
    aiText: "يعتمد على قاعدة البيانات للأسعار والتوافر، وعلى RAG للمستندات والبروشورات.",
  },
  en: {
    brand: "NEXVARY RealEstate",
    subtitle: "AI-powered real estate operating system",
    dashboard: "Dashboard",
    leads: "Leads",
    inventory: "Inventory",
    appointments: "Viewings",
    ai: "AI Assistant",
    search: "Search customer, unit or project...",
    addLead: "Add lead",
    welcome: "Good evening",
    overview: "Live sales activity overview",
    totalLeads: "Total leads",
    hotLeads: "Hot leads",
    available: "Available units",
    meetings: "Today's viewings",
    funnel: "Sales funnel",
    live: "Live",
    newLead: "New lead",
    name: "Name",
    phone: "Phone",
    budget: "Budget",
    save: "Save lead",
    cancel: "Cancel",
    aiTitle: "AI Sales Copilot",
    aiText: "Uses structured data for price and availability, and RAG for documents and brochures.",
  },
};

const navItems = [
  { id: "dashboard" as View, icon: LayoutDashboard, key: "dashboard" as const },
  { id: "leads" as View, icon: Users, key: "leads" as const },
  { id: "inventory" as View, icon: Building2, key: "inventory" as const },
  { id: "appointments" as View, icon: CalendarDays, key: "appointments" as const },
  { id: "ai" as View, icon: Bot, key: "ai" as const },
];

export default function App() {
  const [locale, setLocale] = useState<Locale>("ar");
  const [view, setView] = useState<View>("dashboard");
  const [modalOpen, setModalOpen] = useState(false);
  const [leads, setLeads] = useState<Lead[]>([
    { name: "أحمد محمود", phone: "0100••••421", budget: "5.0M", source: "WhatsApp", score: 88 },
    { name: "سارة علي", phone: "0112••••903", budget: "3.4M", source: "Website", score: 76 },
  ]);
  const t = copy[locale];
  const dir = locale === "ar" ? "rtl" : "ltr";
  const currentKey = navItems.find((item) => item.id === view)?.key ?? "dashboard";
  const title = useMemo(() => t[currentKey], [currentKey, t]);

  function addLead(form: FormData) {
    const name = String(form.get("name") || "").trim();
    const phone = String(form.get("phone") || "").trim();
    const budget = String(form.get("budget") || "").trim();
    if (!name || !phone) return;
    setLeads((current) => [{ name, phone, budget: budget || "—", source: "Manual", score: 35 }, ...current]);
    setModalOpen(false);
    setView("leads");
  }

  return (
    <div className="app" dir={dir}>
      <aside className="sidebar">
        <div className="logoMark">N</div>
        <div className="brandBlock">
          <strong>{t.brand}</strong>
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
        <div className="sidebarFoot">
          <span className="statusDot" />
          <div>
            <strong>AI Gateway</strong>
            <small>Operational</small>
          </div>
        </div>
      </aside>

      <main className="main">
        <header>
          <div className="mobileBrand">N</div>
          <div className="searchBox">
            <Search size={18} />
            <input aria-label={t.search} placeholder={t.search} />
          </div>
          <button className="iconButton" onClick={() => setLocale(locale === "ar" ? "en" : "ar")} title="Language">
            <Languages size={19} />
            <span>{locale.toUpperCase()}</span>
          </button>
          <button className="primaryButton" onClick={() => setModalOpen(true)}>
            <Plus size={18} />
            {t.addLead}
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

          {view === "dashboard" && (
            <>
              <div className="statsGrid">
                <Stat icon={<Users />} label={t.totalLeads} value={String(248 + leads.length)} delta="+18%" />
                <Stat icon={<Sparkles />} label={t.hotLeads} value="37" delta="+9%" />
                <Stat icon={<Home />} label={t.available} value="416" delta="-3%" />
                <Stat icon={<CalendarDays />} label={t.meetings} value="12" delta="+4" />
              </div>

              <div className="dashboardGrid">
                <section className="panel largePanel">
                  <div className="panelHead"><div><span>{t.funnel}</span><h2>Q3 Pipeline</h2></div><CircleDollarSign /></div>
                  <div className="funnel">
                    <Funnel label={locale === "ar" ? "عملاء جدد" : "New leads"} value="250" width="100%" />
                    <Funnel label={locale === "ar" ? "مؤهلون" : "Qualified"} value="142" width="77%" />
                    <Funnel label={locale === "ar" ? "معاينات" : "Viewings"} value="68" width="52%" />
                    <Funnel label={locale === "ar" ? "تفاوض" : "Negotiation"} value="31" width="34%" />
                    <Funnel label={locale === "ar" ? "تم البيع" : "Won"} value="14" width="21%" />
                  </div>
                </section>

                <section className="panel aiPanel">
                  <div className="aiIcon"><Bot /></div>
                  <span className="eyebrow">NEXVARY AI</span>
                  <h2>{t.aiTitle}</h2>
                  <p>{t.aiText}</p>
                  <button onClick={() => setView("ai")}>{t.ai}<ChevronLeft size={16}/></button>
                </section>
              </div>
            </>
          )}

          {view === "leads" && (
            <section className="panel tablePanel">
              <div className="panelHead"><h2>{t.leads}</h2><span>{leads.length} records</span></div>
              <div className="leadTable">
                {leads.map((lead, index) => (
                  <div className="leadRow" key={lead.phone + index}>
                    <div className="avatar">{lead.name.slice(0, 1)}</div>
                    <div className="leadName"><strong>{lead.name}</strong><span>{lead.phone}</span></div>
                    <span>{lead.source}</span>
                    <span>{lead.budget}</span>
                    <span className={lead.score >= 70 ? "score hot" : "score"}>{lead.score}</span>
                  </div>
                ))}
              </div>
            </section>
          )}

          {view === "inventory" && <EmptyState icon={<Building2 />} title={t.inventory} text={locale === "ar" ? "ستظهر هنا الوحدات الحقيقية بعد مزامنة قاعدة البيانات." : "Live units will appear here after database sync."} />}
          {view === "appointments" && <EmptyState icon={<CalendarDays />} title={t.appointments} text={locale === "ar" ? "جدول المعاينات مربوط بالعملاء والمشروعات." : "Viewings are linked to leads and projects."} />}
          {view === "ai" && <EmptyState icon={<Bot />} title={t.aiTitle} text={t.aiText} />}
        </section>
      </main>

      {modalOpen && (
        <div className="modalBackdrop" onMouseDown={() => setModalOpen(false)}>
          <form className="modal" onSubmit={(event) => { event.preventDefault(); addLead(new FormData(event.currentTarget)); }} onMouseDown={(e) => e.stopPropagation()}>
            <div className="modalHead"><div><span className="eyebrow">CRM</span><h2>{t.newLead}</h2></div><button type="button" className="closeButton" onClick={() => setModalOpen(false)}>×</button></div>
            <label>{t.name}<input name="name" required autoFocus /></label>
            <label>{t.phone}<input name="phone" required /></label>
            <label>{t.budget}<input name="budget" placeholder="5,000,000 EGP" /></label>
            <div className="modalActions">
              <button type="button" className="secondaryButton" onClick={() => setModalOpen(false)}>{t.cancel}</button>
              <button type="submit" className="primaryButton">{t.save}</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

function Stat({ icon, label, value, delta }: { icon: React.ReactNode; label: string; value: string; delta: string }) {
  return <div className="statCard"><div className="statTop"><div className="statIcon">{icon}</div><span>{delta}</span></div><strong>{value}</strong><p>{label}</p></div>;
}

function Funnel({ label, value, width }: { label: string; value: string; width: string }) {
  return <div className="funnelRow"><div className="funnelMeta"><span>{label}</span><strong>{value}</strong></div><div className="funnelTrack"><div className="funnelFill" style={{ width }} /></div></div>;
}

function EmptyState({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return <section className="panel emptyState"><div className="aiIcon">{icon}</div><h2>{title}</h2><p>{text}</p></section>;
}
