import { useEffect, useMemo, useState } from "react";
import { Building2, FileText, Home, RefreshCw, Search, Sparkles } from "lucide-react";

type Locale = "ar" | "en";
const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? "http://localhost:8000" : window.location.origin);

type Project = { id: string; name: string; city: string; developer?: string | null; description?: string | null };
type Unit = { id: string; project_id: string; code: string; unit_type: string; bedrooms?: number | null; area_sqm: number; price: number; currency: string; status: string };
type SEOPage = {
  id: string;
  seo_project_id: string;
  entity_type: string;
  entity_id: string;
  slug: string;
  page_url: string;
  title: string;
  meta_description: string;
  body: Record<string, unknown>;
  structured_data: Record<string, unknown>;
  status: string;
  source_hash: string;
  updated_at: string;
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

export default function RealEstateSEO({
  token,
  locale,
  seoProjectId,
}: {
  token: string;
  locale: Locale;
  seoProjectId: string;
}) {
  const ar = locale === "ar";
  const [projects, setProjects] = useState<Project[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [pages, setPages] = useState<SEOPage[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState("");

  async function load() {
    setError("");
    try {
      const [projectData, unitData, pageData] = await Promise.all([
        api<Project[]>("/api/v1/projects", token),
        api<Unit[]>("/api/v1/units", token),
        api<SEOPage[]>(`/api/v1/seo/real-estate/pages?seo_project_id=${encodeURIComponent(seoProjectId)}`, token),
      ]);
      setProjects(projectData);
      setUnits(unitData);
      setPages(pageData);
      setSelectedProjectId((current) => current || projectData[0]?.id || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    }
  }

  useEffect(() => { if (seoProjectId) void load(); }, [token, seoProjectId]);

  const selectedProject = useMemo(() => projects.find((p) => p.id === selectedProjectId) || null, [projects, selectedProjectId]);
  const selectedUnits = useMemo(() => units.filter((u) => u.project_id === selectedProjectId), [units, selectedProjectId]);
  const projectPage = useMemo(() => pages.find((p) => p.entity_type === "project" && p.entity_id === selectedProjectId) || null, [pages, selectedProjectId]);
  const unitPages = useMemo(() => new Map(pages.filter((p) => p.entity_type === "unit").map((p) => [p.entity_id, p])), [pages]);

  async function generateProject() {
    if (!selectedProjectId) return;
    setBusy("project"); setError(""); setNotice("");
    try {
      await api(`/api/v1/seo/real-estate/projects/${selectedProjectId}/generate?seo_project_id=${encodeURIComponent(seoProjectId)}`, token, { method: "POST" });
      setNotice(ar ? "تم إنشاء/تحديث صفحة المشروع من بيانات قاعدة العقارات." : "Project page generated/refreshed from transactional real-estate data.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally { setBusy(""); }
  }

  async function generateUnit(unitId: string) {
    setBusy(unitId); setError(""); setNotice("");
    try {
      await api(`/api/v1/seo/real-estate/units/${unitId}/generate?seo_project_id=${encodeURIComponent(seoProjectId)}`, token, { method: "POST" });
      setNotice(ar ? "تم إنشاء/تحديث صفحة الوحدة." : "Unit page generated/refreshed.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally { setBusy(""); }
  }

  async function syncAll() {
    if (!selectedProjectId) return;
    setBusy("all"); setError(""); setNotice("");
    try {
      const result = await api<{ unit_pages: number; hallucinated_fields: number }>(`/api/v1/seo/real-estate/projects/${selectedProjectId}/sync-all?seo_project_id=${encodeURIComponent(seoProjectId)}`, token, { method: "POST" });
      setNotice(ar
        ? `تمت مزامنة صفحة المشروع و${result.unit_pages} صفحة وحدة. حقول مختلقة: ${result.hallucinated_fields}.`
        : `Synced the project page and ${result.unit_pages} unit pages. Hallucinated fields: ${result.hallucinated_fields}.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sync failed");
    } finally { setBusy(""); }
  }

  if (!seoProjectId) return null;

  return <div className="realEstateSeo">
    <div className="opsHeading">
      <div><span className="eyebrow">TRANSACTIONAL SEO PAGES</span><h3>{ar ? "صفحات المشروعات والوحدات العقارية" : "Project & unit SEO pages"}</h3></div>
      <button className="iconButton" onClick={() => void load()}><RefreshCw size={16}/></button>
    </div>
    <p className="seoHint">{ar
      ? "العنوان والوصف والسعر والتوافر تُشتق من قاعدة البيانات فقط. عند تغيير بيانات المشروع أو الوحدة يمكن مزامنة الصفحة مجددًا دون اختراع مواصفات."
      : "Titles, descriptions, pricing and availability are derived only from transactional data. Re-sync after inventory changes without inventing specifications."}</p>
    {error && <div className="systemError">{error}</div>}
    {notice && <div className="successNotice">{notice}</div>}

    <div className="realEstateSeoControls panel">
      <label>{ar ? "المشروع العقاري" : "Real-estate project"}
        <select value={selectedProjectId} onChange={(event) => setSelectedProjectId(event.target.value)}>
          <option value="">{ar ? "اختر المشروع" : "Select project"}</option>
          {projects.map((project) => <option key={project.id} value={project.id}>{project.name} · {project.city}</option>)}
        </select>
      </label>
      <button className="secondaryButton" disabled={!selectedProjectId || busy==="project"} onClick={() => void generateProject()}><FileText size={15}/>{ar ? "صفحة المشروع" : "Project page"}</button>
      <button className="primaryButton" disabled={!selectedProjectId || busy==="all"} onClick={() => void syncAll()}>{busy==="all" ? <RefreshCw size={15} className="spin"/> : <Sparkles size={15}/>} {ar ? "مزامنة المشروع وكل وحداته" : "Sync project + all units"}</button>
    </div>

    {selectedProject && <section className="panel generatedProjectCard">
      <div className="generatedEntityHead"><div className="entityIcon"><Building2 size={19}/></div><div><strong>{selectedProject.name}</strong><span>{selectedProject.city}{selectedProject.developer ? ` · ${selectedProject.developer}` : ""}</span></div><span className={`statusBadge ${projectPage ? "status-active" : "status-pending"}`}>{projectPage ? "SEO ready" : "not generated"}</span></div>
      {projectPage && <div className="generatedSeoMeta"><strong>{projectPage.title}</strong><p>{projectPage.meta_description}</p><a href={projectPage.page_url} target="_blank" rel="noreferrer">{projectPage.page_url}</a></div>}
    </section>}

    <section className="panel generatedUnitsPanel">
      <div className="panelHead"><h3>{ar ? "الوحدات" : "Units"}</h3><span>{selectedUnits.length}</span></div>
      <div className="generatedUnitRows">{selectedUnits.map((unit) => {
        const page = unitPages.get(unit.id);
        return <article key={unit.id}>
          <div className="entityIcon"><Home size={17}/></div>
          <div><strong>{unit.code} · {unit.unit_type}</strong><span>{unit.bedrooms ?? "—"} BR · {Number(unit.area_sqm).toLocaleString()} m² · {Number(unit.price).toLocaleString()} {unit.currency} · {unit.status}</span>{page && <small>{page.page_url}</small>}</div>
          <span className={`statusBadge ${page ? "status-active" : "status-pending"}`}>{page ? page.status : "not generated"}</span>
          <button className="secondaryButton" disabled={busy===unit.id} onClick={() => void generateUnit(unit.id)}>{busy===unit.id ? <RefreshCw size={14} className="spin"/> : <Search size={14}/>} {page ? (ar?"تحديث":"Refresh") : (ar?"إنشاء":"Generate")}</button>
        </article>;
      })}</div>
      {!selectedUnits.length && <div className="seoEmpty"><Home size={25}/><p>{ar ? "لا توجد وحدات في المشروع المحدد." : "No units in the selected project."}</p></div>}
    </section>
  </div>;
}
