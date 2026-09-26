import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  BarChart3,
  Bot,
  CheckCircle2,
  Code2,
  Globe2,
  Gauge,
  Plus,
  Radar,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

type Locale = "ar" | "en";
type Tab = "overview" | "audit" | "crawl" | "search" | "schema" | "performance" | "autopilot";

const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? "http://localhost:8000" : window.location.origin);

type SEOProject = {
  id: string;
  name: string;
  site_url: string;
  is_active: number;
  created_at: string;
};

type Dashboard = {
  project: SEOProject;
  latest_audit?: { score: number; grade: string; created_at: string } | null;
  latest_crawl_at?: string | null;
  search_console_synced_at?: string | null;
  index_coverage?: Record<string, unknown> | null;
  planned_changes: number;
};

type AuditResult = {
  snapshot_id: string;
  score: number;
  grade: string;
  url: string;
  failed_by_severity: Record<string, number>;
  checks: Array<{
    key: string;
    title: string;
    passed: boolean;
    severity: string;
    detail: string;
    recommendation?: string | null;
  }>;
};

type CrawlResult = {
  snapshot_id: string;
  root_url: string;
  pages: Array<{ url: string; status_code: number; title?: string | null; indexable: boolean }>;
  issues: Array<{ key: string; severity: string; url?: string | null; detail: string }>;
  totals: Record<string, number>;
  truncated: boolean;
};

type Opportunity = {
  key: string;
  page?: string | null;
  query?: string | null;
  impact: number;
  confidence: number;
  effort: number;
  priority: number;
  reason: string;
  recommended_action: string;
};

type ChangeDraft = {
  id: string;
  target_url: string;
  action: string;
  risk: string;
  status: string;
  created_at: string;
  payload: Record<string, unknown>;
};

async function seoApi<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Authorization", `Bearer ${token}`);
  if (init?.body) headers.set("Content-Type", "application/json");
  const response = await fetch(`${API_URL}${path}`, { ...init, headers });
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new Error(body?.detail || `HTTP ${response.status}`);
  return body as T;
}

export default function SEOAutopilot({
  token,
  locale,
}: {
  token: string;
  locale: Locale;
}) {
  const ar = locale === "ar";
  const [projects, setProjects] = useState<SEOProject[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [tab, setTab] = useState<Tab>("overview");
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [audit, setAudit] = useState<AuditResult | null>(null);
  const [crawl, setCrawl] = useState<CrawlResult | null>(null);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [plans, setPlans] = useState<ChangeDraft[]>([]);
  const [schemaOutput, setSchemaOutput] = useState<Record<string, unknown> | null>(null);
  const [performanceOutput, setPerformanceOutput] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const selected = useMemo(() => projects.find((item) => item.id === selectedId) || null, [projects, selectedId]);

  async function loadProjects() {
    try {
      const data = await seoApi<SEOProject[]>("/api/v1/seo/projects", token);
      setProjects(data);
      setSelectedId((current) => current || data[0]?.id || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    }
  }

  async function loadProjectState(projectId: string) {
    if (!projectId) {
      setDashboard(null);
      setPlans([]);
      return;
    }
    try {
      const [summary, drafts] = await Promise.all([
        seoApi<Dashboard>(`/api/v1/seo/projects/${projectId}/dashboard`, token),
        seoApi<ChangeDraft[]>(`/api/v1/seo/projects/${projectId}/autopilot/plans`, token),
      ]);
      setDashboard(summary);
      setPlans(drafts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    }
  }

  useEffect(() => { void loadProjects(); }, [token]);
  useEffect(() => {
    setAudit(null);
    setCrawl(null);
    setOpportunities([]);
    void loadProjectState(selectedId);
  }, [selectedId]);

  async function createProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setBusy("project");
    setError("");
    try {
      const created = await seoApi<SEOProject>("/api/v1/seo/projects", token, {
        method: "POST",
        body: JSON.stringify({
          name: String(data.get("name") || "").trim(),
          site_url: String(data.get("site_url") || "").trim(),
        }),
      });
      form.reset();
      await loadProjects();
      setSelectedId(created.id);
      setNotice(ar ? "تمت إضافة الموقع إلى مساحة SEO." : "Website added to the SEO workspace.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    } finally {
      setBusy("");
    }
  }

  async function runAudit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const data = new FormData(event.currentTarget);
    setBusy("audit");
    setError("");
    try {
      const result = await seoApi<AuditResult>(`/api/v1/seo/projects/${selected.id}/audit`, token, {
        method: "POST",
        body: JSON.stringify({ target_url: String(data.get("target_url") || "").trim() || null }),
      });
      setAudit(result);
      await loadProjectState(selected.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Audit failed");
    } finally {
      setBusy("");
    }
  }

  async function runCrawl(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const data = new FormData(event.currentTarget);
    setBusy("crawl");
    setError("");
    try {
      const result = await seoApi<CrawlResult>(`/api/v1/seo/projects/${selected.id}/crawl`, token, {
        method: "POST",
        body: JSON.stringify({
          max_pages: Number(data.get("max_pages") || 60),
          concurrency: Number(data.get("concurrency") || 4),
        }),
      });
      setCrawl(result);
      await loadProjectState(selected.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Crawl failed");
    } finally {
      setBusy("");
    }
  }

  async function syncSearchConsole(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const data = new FormData(event.currentTarget);
    setBusy("search");
    setError("");
    setNotice("");
    try {
      const result = await seoApi<{ rows: number }>(`/api/v1/seo/projects/${selected.id}/search-console/sync`, token, {
        method: "POST",
        body: JSON.stringify({
          start_date: String(data.get("start_date") || ""),
          end_date: String(data.get("end_date") || ""),
          dimensions: ["query", "page"],
          row_limit: Number(data.get("row_limit") || 5000),
        }),
      });
      setNotice(ar ? `تمت مزامنة ${result.rows} صفًا من Search Console.` : `Synced ${result.rows} Search Console rows.`);
      await loadProjectState(selected.id);
      await loadOpportunities();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search Console sync failed");
    } finally {
      setBusy("");
    }
  }

  async function loadOpportunities() {
    if (!selected) return;
    setBusy("opportunities");
    setError("");
    try {
      setOpportunities(await seoApi<Opportunity[]>(`/api/v1/seo/projects/${selected.id}/opportunities?limit=40`, token));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Opportunity load failed");
    } finally {
      setBusy("");
    }
  }

  async function buildSchema(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setBusy("schema");
    setError("");
    try {
      const visible = JSON.parse(String(data.get("visible_data") || "{}"));
      setSchemaOutput(await seoApi<Record<string, unknown>>("/api/v1/seo/schema/build", token, {
        method: "POST",
        body: JSON.stringify({ schema_type: String(data.get("schema_type") || "Organization"), visible_data: visible }),
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Schema build failed");
    } finally {
      setBusy("");
    }
  }

  async function scorePerformance(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setBusy("performance");
    setError("");
    try {
      setPerformanceOutput(await seoApi<Record<string, unknown>>("/api/v1/seo/performance/web-vitals", token, {
        method: "POST",
        body: JSON.stringify({
          lcp_ms: data.get("lcp_ms") ? Number(data.get("lcp_ms")) : null,
          inp_ms: data.get("inp_ms") ? Number(data.get("inp_ms")) : null,
          cls: data.get("cls") ? Number(data.get("cls")) : null,
        }),
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Performance score failed");
    } finally {
      setBusy("");
    }
  }

  async function planChange(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    setBusy("plan");
    setError("");
    try {
      await seoApi<ChangeDraft>(`/api/v1/seo/projects/${selected.id}/autopilot/plan`, token, {
        method: "POST",
        body: JSON.stringify({
          target_url: String(data.get("target_url") || selected.site_url),
          action: String(data.get("action") || ""),
          before: JSON.parse(String(data.get("before") || "{}")),
          after: JSON.parse(String(data.get("after") || "{}")),
          reason: String(data.get("reason") || ""),
        }),
      });
      form.reset();
      setNotice(ar ? "تم إنشاء خطة تغيير Dry Run فقط. لم تتم الكتابة على الموقع." : "Dry-run change plan created. No live website write occurred.");
      await loadProjectState(selected.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Plan failed");
    } finally {
      setBusy("");
    }
  }

  const tabs: Array<{ id: Tab; labelAr: string; labelEn: string; icon: typeof Search }> = [
    { id: "overview", labelAr: "نظرة عامة", labelEn: "Overview", icon: BarChart3 },
    { id: "audit", labelAr: "فحص SEO", labelEn: "Audit", icon: Search },
    { id: "crawl", labelAr: "الزاحف", labelEn: "Crawler", icon: Radar },
    { id: "search", labelAr: "Search Console", labelEn: "Search Console", icon: Globe2 },
    { id: "schema", labelAr: "Schema", labelEn: "Schema", icon: Code2 },
    { id: "performance", labelAr: "الأداء", labelEn: "Performance", icon: Gauge },
    { id: "autopilot", labelAr: "Autopilot", labelEn: "Autopilot", icon: Bot },
  ];

  return <div className="seoWorkspace">
    <section className="seoHero panel">
      <div>
        <span className="eyebrow">WHITE-LABEL SEO ENGINE</span>
        <h2>SEO Autopilot</h2>
        <p>{ar ? "محرك SEO مدمج داخل مساحة الشركة الحالية؛ جميع المواقع والنتائج والخطط معزولة حسب الشركة." : "SEO engine embedded inside the current company workspace; projects, evidence and plans are tenant-isolated."}</p>
      </div>
      <div className="seoSafety"><ShieldCheck size={18}/><span>{ar ? "الكتابة الحية على المواقع غير معروضة في هذه النسخة المدمجة" : "Live website writes are not exposed in this integrated release"}</span></div>
    </section>

    {error && <div className="systemError">{error}</div>}
    {notice && <div className="successNotice">{notice}</div>}

    <div className="seoTopGrid">
      <section className="panel seoProjectPanel">
        <div className="panelHead"><h3>{ar ? "مواقع الشركة" : "Company websites"}</h3><span>{projects.length}</span></div>
        <div className="seoProjectList">
          {projects.map((project) => <button key={project.id} className={selectedId === project.id ? "seoProject active" : "seoProject"} onClick={() => setSelectedId(project.id)}>
            <Globe2 size={16}/><div><strong>{project.name}</strong><span>{project.site_url}</span></div>
          </button>)}
        </div>
        <form className="seoAddProject" onSubmit={createProject}>
          <input name="name" placeholder={ar ? "اسم الموقع" : "Website name"} required/>
          <input name="site_url" type="url" placeholder="https://company.com" required/>
          <button className="secondaryButton" type="submit" disabled={busy === "project"}><Plus size={15}/>{ar ? "إضافة" : "Add"}</button>
        </form>
      </section>

      <section className="panel seoCurrentProject">
        {selected ? <>
          <span className="eyebrow">{selected.site_url}</span>
          <h3>{selected.name}</h3>
          <div className="seoMetricRow">
            <SeoMetric label={ar ? "آخر نتيجة" : "Latest score"} value={dashboard?.latest_audit ? `${dashboard.latest_audit.score}/100 · ${dashboard.latest_audit.grade}` : "—"}/>
            <SeoMetric label={ar ? "الزحف" : "Crawl"} value={dashboard?.latest_crawl_at ? new Date(dashboard.latest_crawl_at).toLocaleDateString(ar ? "ar-EG" : "en-US") : "—"}/>
            <SeoMetric label="Search Console" value={dashboard?.search_console_synced_at ? new Date(dashboard.search_console_synced_at).toLocaleDateString(ar ? "ar-EG" : "en-US") : "—"}/>
            <SeoMetric label={ar ? "خطط التغيير" : "Change plans"} value={String(dashboard?.planned_changes ?? 0)}/>
          </div>
        </> : <div className="seoEmpty"><Globe2 size={27}/><p>{ar ? "أضف موقع الشركة لبدء العمل." : "Add a company website to begin."}</p></div>}
      </section>
    </div>

    {selected && <>
      <div className="seoTabs">
        {tabs.map(({ id, labelAr, labelEn, icon: Icon }) => <button key={id} className={tab === id ? "active" : ""} onClick={() => setTab(id)}><Icon size={16}/><span>{ar ? labelAr : labelEn}</span></button>)}
      </div>

      {tab === "overview" && <section className="panel seoOverview">
        <div className="seoOverviewGrid">
          <article><Sparkles/><strong>{ar ? "محرك أصلي من SEO Autopilot" : "SEO Autopilot engine copy"}</strong><p>{ar ? "تم دمج المحرك البرمجي نفسه داخل المنصة مع بقاء المشروع الأصلي دون تعديل." : "The engine itself is integrated while the original project remains untouched."}</p></article>
          <article><ShieldCheck/><strong>{ar ? "عزل White-Label" : "White-label isolation"}</strong><p>{ar ? "كل شركة ترى مواقعها ونتائجها وخططها فقط، والواجهة ترث هوية الشركة." : "Each company sees only its own websites, results and plans; the UI inherits tenant branding."}</p></article>
          <article><Bot/><strong>{ar ? "Autopilot محمي" : "Guarded Autopilot"}</strong><p>{ar ? "إنشاء خطط وتصنيف مخاطر بدون زر كتابة حي على الموقع في هذه المرحلة." : "Creates plans and risk classifications without exposing a live-write button in this stage."}</p></article>
        </div>
      </section>}

      {tab === "audit" && <div className="seoSplit">
        <form className="panel seoForm" onSubmit={runAudit}>
          <div className="opsTitle"><Search size={18}/><strong>{ar ? "فحص صفحة" : "Page audit"}</strong></div>
          <label>{ar ? "الرابط — اتركه فارغًا لفحص الصفحة الرئيسية" : "URL — leave blank for website root"}<input name="target_url" type="url" placeholder={selected.site_url}/></label>
          <button className="primaryButton" type="submit" disabled={busy === "audit"}>{busy === "audit" ? <RefreshCw className="spin" size={16}/> : <Search size={16}/>} {ar ? "ابدأ الفحص" : "Run audit"}</button>
        </form>
        <section className="panel seoResult">
          {audit ? <>
            <div className="seoScore"><strong>{audit.score}</strong><span>/100 · {audit.grade}</span></div>
            <div className="seoCheckList">{audit.checks.map((check) => <article key={check.key} className={check.passed ? "passed" : "failed"}><CheckCircle2 size={15}/><div><strong>{check.title}</strong><span>{check.detail}</span>{check.recommendation && <small>{check.recommendation}</small>}</div></article>)}</div>
          </> : <EmptyResult ar={ar}/>}
        </section>
      </div>}

      {tab === "crawl" && <div className="seoSplit">
        <form className="panel seoForm" onSubmit={runCrawl}>
          <div className="opsTitle"><Radar size={18}/><strong>{ar ? "زحف آمن داخل الموقع" : "Safe same-site crawl"}</strong></div>
          <label>{ar ? "أقصى عدد صفحات" : "Maximum pages"}<input name="max_pages" type="number" min="1" max="300" defaultValue="60"/></label>
          <label>{ar ? "التوازي" : "Concurrency"}<input name="concurrency" type="number" min="1" max="10" defaultValue="4"/></label>
          <button className="primaryButton" type="submit" disabled={busy === "crawl"}>{busy === "crawl" ? <RefreshCw className="spin" size={16}/> : <Radar size={16}/>} {ar ? "ابدأ الزحف" : "Start crawl"}</button>
        </form>
        <section className="panel seoResult">
          {crawl ? <>
            <div className="crawlTotals">{Object.entries(crawl.totals).slice(0,8).map(([key,value]) => <SeoMetric key={key} label={key.replaceAll("_"," ")} value={String(value)}/>)}</div>
            <div className="seoIssueList">{crawl.issues.slice(0,30).map((issue,index) => <article key={index}><span className={`statusBadge status-${issue.severity === "high" || issue.severity === "critical" ? "blocked" : "pending"}`}>{issue.severity}</span><div><strong>{issue.key}</strong><p>{issue.detail}</p></div></article>)}</div>
          </> : <EmptyResult ar={ar}/>}
        </section>
      </div>}

      {tab === "search" && <div className="seoSplit">
        <form className="panel seoForm" onSubmit={syncSearchConsole}>
          <div className="opsTitle"><Globe2 size={18}/><strong>Google Search Console</strong></div>
          <p className="seoHint">{ar ? "اضبط تكامل google-search-console من Platform Admin مرة واحدة لكل شركة. التوكن يظل مشفرًا ولا يظهر هنا." : "Configure the google-search-console integration once in Platform Admin. The token remains encrypted and is never shown here."}</p>
          <label>{ar ? "من" : "From"}<input name="start_date" type="date" required/></label>
          <label>{ar ? "إلى" : "To"}<input name="end_date" type="date" required/></label>
          <label>{ar ? "الحد الأقصى للصفوف" : "Row limit"}<input name="row_limit" type="number" min="1" max="25000" defaultValue="5000"/></label>
          <button className="primaryButton" type="submit" disabled={busy === "search"}>{busy === "search" ? <RefreshCw className="spin" size={16}/> : <Globe2 size={16}/>} {ar ? "مزامنة البيانات" : "Sync data"}</button>
          <button className="secondaryButton" type="button" onClick={() => void loadOpportunities()} disabled={busy === "opportunities"}><Sparkles size={16}/>{ar ? "استخراج الفرص" : "Build opportunities"}</button>
        </form>
        <section className="panel seoResult">
          <div className="panelHead"><h3>{ar ? "فرص النمو" : "Growth opportunities"}</h3><span>{opportunities.length}</span></div>
          {opportunities.length ? <div className="seoOpportunityList">{opportunities.map((item,index) => <article key={index}><div><span className="eyebrow">{item.key}</span><strong>{item.query || item.page || "Opportunity"}</strong><p>{item.reason}</p><small>{item.recommended_action}</small></div><b>{item.priority.toFixed(2)}</b></article>)}</div> : <EmptyResult ar={ar}/>}
        </section>
      </div>}

      {tab === "schema" && <div className="seoSplit">
        <form className="panel seoForm" onSubmit={buildSchema}>
          <div className="opsTitle"><Code2 size={18}/><strong>Structured Data</strong></div>
          <label>Schema Type<select name="schema_type" defaultValue="Organization"><option>Organization</option><option>WebSite</option><option>BreadcrumbList</option><option>Article</option><option>Product</option><option>LocalBusiness</option></select></label>
          <label>{ar ? "البيانات الظاهرة للمستخدم JSON" : "Visible page data JSON"}<textarea name="visible_data" rows={10} defaultValue={'{"name":"","url":"https://example.com"}'}/></label>
          <button className="primaryButton" type="submit" disabled={busy === "schema"}><Code2 size={16}/>{ar ? "بناء Schema" : "Build schema"}</button>
        </form>
        <section className="panel seoResult codeResult">{schemaOutput ? <pre>{JSON.stringify(schemaOutput,null,2)}</pre> : <EmptyResult ar={ar}/>}</section>
      </div>}

      {tab === "performance" && <div className="seoSplit">
        <form className="panel seoForm" onSubmit={scorePerformance}>
          <div className="opsTitle"><Gauge size={18}/><strong>Core Web Vitals</strong></div>
          <label>LCP ms<input name="lcp_ms" type="number" min="0" step="1"/></label>
          <label>INP ms<input name="inp_ms" type="number" min="0" step="1"/></label>
          <label>CLS<input name="cls" type="number" min="0" step="0.001"/></label>
          <button className="primaryButton" type="submit" disabled={busy === "performance"}><Gauge size={16}/>{ar ? "تقييم الأداء" : "Evaluate"}</button>
        </form>
        <section className="panel seoResult codeResult">{performanceOutput ? <pre>{JSON.stringify(performanceOutput,null,2)}</pre> : <EmptyResult ar={ar}/>}</section>
      </div>}

      {tab === "autopilot" && <div className="seoSplit">
        <form className="panel seoForm" onSubmit={planChange}>
          <div className="opsTitle"><Bot size={18}/><strong>{ar ? "خطة تغيير محمية" : "Guarded change plan"}</strong></div>
          <label>{ar ? "الرابط" : "Target URL"}<input name="target_url" type="url" defaultValue={selected.site_url} required/></label>
          <label>{ar ? "الإجراء" : "Action"}<select name="action" defaultValue="meta_description_rewrite"><option value="meta_description_add">meta_description_add</option><option value="meta_description_rewrite">meta_description_rewrite</option><option value="title_change">title_change</option><option value="internal_link_insert">internal_link_insert</option><option value="schema_deterministic_add">schema_deterministic_add</option><option value="content_update">content_update</option><option value="url_change">url_change</option></select></label>
          <label>Before JSON<textarea name="before" rows={4} defaultValue="{}"/></label>
          <label>After JSON<textarea name="after" rows={4} defaultValue="{}"/></label>
          <label>{ar ? "السبب" : "Reason"}<textarea name="reason" rows={3} required/></label>
          <button className="primaryButton" type="submit" disabled={busy === "plan"}><Bot size={16}/>{ar ? "إنشاء Dry Run" : "Create dry run"}</button>
        </form>
        <section className="panel seoResult">
          <div className="panelHead"><h3>{ar ? "خطط التغيير" : "Change plans"}</h3><span>{plans.length}</span></div>
          <div className="seoPlanList">{plans.map((plan) => <article key={plan.id}><div><strong>{plan.action}</strong><span>{plan.target_url}</span></div><span className={`statusBadge ${plan.risk === "protected" ? "status-blocked" : plan.risk === "review_required" ? "status-pending" : "status-active"}`}>{plan.risk}</span></article>)}</div>
          {!plans.length && <EmptyResult ar={ar}/>}
        </section>
      </div>}
    </>}
  </div>;
}

function SeoMetric({ label, value }: { label: string; value: string }) {
  return <div className="seoMetric"><span>{label}</span><strong>{value}</strong></div>;
}

function EmptyResult({ ar }: { ar: boolean }) {
  return <div className="seoEmpty"><Sparkles size={25}/><p>{ar ? "لا توجد نتيجة بعد." : "No result yet."}</p></div>;
}
