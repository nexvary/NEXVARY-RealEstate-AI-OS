import { FormEvent, useEffect, useState } from "react";
import {
  BookOpen,
  Building2,
  CheckCircle2,
  ClipboardCheck,
  MessageSquare,
  Plus,
  RefreshCw,
  Send,
  UserPlus,
} from "lucide-react";

type Locale = "ar" | "en";

const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? "http://localhost:8000" : window.location.origin);

async function callApi<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Authorization", `Bearer ${token}`);
  if (init?.body) headers.set("Content-Type", "application/json");
  const response = await fetch(`${API_URL}${path}`, { ...init, headers });
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new Error(body?.detail || `HTTP ${response.status}`);
  return body as T;
}

function money(value: number, currency: string, locale: Locale) {
  try {
    return new Intl.NumberFormat(locale === "ar" ? "ar-EG" : "en-US", {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    }).format(value);
  } catch {
    return `${value.toLocaleString()} ${currency}`;
  }
}

type Project = { id: string; name: string; city: string; developer?: string | null };
type Plan = { id: string; project_id: string; name: string; down_payment_percent: number; years: number };
type Unit = { id: string; project_id: string; code: string; unit_type: string; bedrooms?: number | null; area_sqm: number; price: number; currency: string; status: string };
type KnowledgeDoc = { id: string; title: string; category: string; source_name?: string | null; chunk_count: number };
type KnowledgeHit = { document_id: string; document_title: string; source_name?: string | null; chunk_position: number; text: string; score: number };
type Task = { id: string; title: string; notes?: string | null; due_at?: string | null; status: string };
type Conversation = { id: string; channel: string; external_contact: string; display_name?: string | null; status: string };
type Message = { id: string; conversation_id: string; direction: string; sender: string; body: string; created_at: string };
type TeamUser = { id: string; email: string; display_name: string; role: string; is_active: number };

export function InventoryOps({ token, locale }: { token: string; locale: Locale }) {
  const ar = locale === "ar";
  const [projects, setProjects] = useState<Project[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    setBusy(true);
    setError("");
    try {
      const [p, pp, u] = await Promise.all([
        callApi<Project[]>("/api/v1/projects", token),
        callApi<Plan[]>("/api/v1/payment-plans", token),
        callApi<Unit[]>("/api/v1/units", token),
      ]);
      setProjects(p); setPlans(pp); setUnits(u);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    } finally { setBusy(false); }
  }

  useEffect(() => { void load(); }, [token]);

  async function createProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = event.currentTarget; const data = new FormData(form);
    try {
      await callApi("/api/v1/projects", token, { method: "POST", body: JSON.stringify({
        name: String(data.get("name") || ""), city: String(data.get("city") || ""),
        developer: String(data.get("developer") || "") || null,
      })});
      form.reset(); await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Save failed"); }
  }

  async function createPlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = event.currentTarget; const data = new FormData(form);
    try {
      await callApi("/api/v1/payment-plans", token, { method: "POST", body: JSON.stringify({
        project_id: String(data.get("project_id") || ""), name: String(data.get("name") || ""),
        down_payment_percent: Number(data.get("down_payment_percent") || 0),
        years: Number(data.get("years") || 1), installment_frequency_months: Number(data.get("frequency") || 3),
      })});
      form.reset(); await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Save failed"); }
  }

  async function createUnit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = event.currentTarget; const data = new FormData(form);
    try {
      await callApi("/api/v1/units", token, { method: "POST", body: JSON.stringify({
        project_id: String(data.get("project_id") || ""),
        payment_plan_id: String(data.get("payment_plan_id") || "") || null,
        code: String(data.get("code") || ""), unit_type: String(data.get("unit_type") || ""),
        bedrooms: data.get("bedrooms") ? Number(data.get("bedrooms")) : null,
        area_sqm: Number(data.get("area_sqm") || 0), price: Number(data.get("price") || 0),
        currency: String(data.get("currency") || "EGP"),
      })});
      form.reset(); await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Save failed"); }
  }

  return <div className="opsPage">
    <div className="opsHeading"><div><span className="eyebrow">INVENTORY CONTROL</span><h2>{ar ? "إدارة المشروعات والوحدات" : "Projects & inventory management"}</h2></div>
      <button className="iconButton" onClick={() => void load()} disabled={busy}><RefreshCw size={17} className={busy ? "spin" : ""}/></button></div>
    {error && <div className="systemError">{error}</div>}
    <div className="opsGrid">
      <form className="panel opsForm" onSubmit={createProject}>
        <div className="opsTitle"><Building2 size={19}/><strong>{ar ? "مشروع جديد" : "New project"}</strong></div>
        <label>{ar ? "اسم المشروع" : "Project name"}<input name="name" required /></label>
        <label>{ar ? "المدينة" : "City"}<input name="city" required /></label>
        <label>{ar ? "المطور" : "Developer"}<input name="developer" /></label>
        <button className="primaryButton" type="submit"><Plus size={16}/>{ar ? "إضافة المشروع" : "Add project"}</button>
      </form>

      <form className="panel opsForm" onSubmit={createPlan}>
        <div className="opsTitle"><ClipboardCheck size={19}/><strong>{ar ? "خطة سداد" : "Payment plan"}</strong></div>
        <label>{ar ? "المشروع" : "Project"}<select name="project_id" required><option value="">{ar ? "اختر" : "Select"}</option>{projects.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
        <label>{ar ? "اسم الخطة" : "Plan name"}<input name="name" required placeholder="10% / 8 years" /></label>
        <div className="inlineFields"><label>{ar ? "المقدم %" : "Down %"}<input name="down_payment_percent" type="number" min="0" max="100" defaultValue="10"/></label><label>{ar ? "سنوات" : "Years"}<input name="years" type="number" min="1" max="30" defaultValue="8"/></label></div>
        <label>{ar ? "دورية القسط بالشهور" : "Installment frequency (months)"}<input name="frequency" type="number" min="1" max="12" defaultValue="3"/></label>
        <button className="primaryButton" type="submit"><Plus size={16}/>{ar ? "إضافة الخطة" : "Add plan"}</button>
      </form>

      <form className="panel opsForm wideForm" onSubmit={createUnit}>
        <div className="opsTitle"><Building2 size={19}/><strong>{ar ? "وحدة جديدة" : "New unit"}</strong></div>
        <div className="formGrid">
          <label>{ar ? "المشروع" : "Project"}<select name="project_id" required><option value="">{ar ? "اختر" : "Select"}</option>{projects.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
          <label>{ar ? "خطة السداد" : "Payment plan"}<select name="payment_plan_id"><option value="">{ar ? "بدون" : "None"}</option>{plans.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
          <label>{ar ? "كود الوحدة" : "Unit code"}<input name="code" required /></label>
          <label>{ar ? "النوع" : "Type"}<input name="unit_type" required placeholder={ar ? "شقة / فيلا" : "Apartment / Villa"} /></label>
          <label>{ar ? "غرف النوم" : "Bedrooms"}<input name="bedrooms" type="number" min="0" max="30"/></label>
          <label>{ar ? "المساحة م²" : "Area m²"}<input name="area_sqm" type="number" min="1" step="0.01" required /></label>
          <label>{ar ? "السعر" : "Price"}<input name="price" type="number" min="1" step="1" required /></label>
          <label>{ar ? "العملة" : "Currency"}<input name="currency" defaultValue="EGP" required /></label>
        </div>
        <button className="primaryButton" type="submit"><Plus size={16}/>{ar ? "إضافة الوحدة" : "Add unit"}</button>
      </form>
    </div>
    <section className="panel opsList">
      <div className="panelHead"><h2>{ar ? "الوحدات الحالية" : "Current units"}</h2><span>{units.length}</span></div>
      <div className="compactTable">{units.map(u=><div className="compactRow" key={u.id}><strong>{u.code}</strong><span>{u.unit_type}</span><span>{u.bedrooms ?? "—"} BR</span><span>{Number(u.area_sqm).toLocaleString()} m²</span><span>{money(Number(u.price),u.currency,locale)}</span><span className={`statusBadge status-${u.status}`}>{u.status}</span></div>)}</div>
    </section>
  </div>;
}

export function KnowledgeOps({ token, locale }: { token: string; locale: Locale }) {
  const ar=locale==="ar"; const [docs,setDocs]=useState<KnowledgeDoc[]>([]); const [hits,setHits]=useState<KnowledgeHit[]>([]); const [error,setError]=useState("");
  async function load(){ try{setDocs(await callApi("/api/v1/knowledge/documents",token));}catch(e){setError(e instanceof Error?e.message:"Load failed");}}
  useEffect(()=>{void load();},[token]);
  async function add(event:FormEvent<HTMLFormElement>){event.preventDefault();const form=event.currentTarget;const d=new FormData(form);try{await callApi("/api/v1/knowledge/documents",token,{method:"POST",body:JSON.stringify({title:String(d.get("title")||""),category:String(d.get("category")||"general"),source_name:String(d.get("source_name")||"")||null,content:String(d.get("content")||"")})});form.reset();await load();}catch(e){setError(e instanceof Error?e.message:"Save failed");}}
  async function query(event:FormEvent<HTMLFormElement>){event.preventDefault();const d=new FormData(event.currentTarget);try{const r=await callApi<{hits:KnowledgeHit[]}>("/api/v1/knowledge/query",token,{method:"POST",body:JSON.stringify({question:String(d.get("question")||""),limit:6})});setHits(r.hits);}catch(e){setError(e instanceof Error?e.message:"Query failed");}}
  return <div className="opsPage"><div className="opsHeading"><div><span className="eyebrow">GROUNDED KNOWLEDGE</span><h2>{ar?"قاعدة المعرفة والاسترجاع":"Knowledge base & retrieval"}</h2></div></div>{error&&<div className="systemError">{error}</div>}
    <div className="knowledgeGrid"><form className="panel opsForm" onSubmit={add}><div className="opsTitle"><BookOpen size={19}/><strong>{ar?"إضافة معرفة":"Add knowledge"}</strong></div><label>{ar?"العنوان":"Title"}<input name="title" required/></label><label>{ar?"التصنيف":"Category"}<input name="category" defaultValue="brochure"/></label><label>{ar?"اسم المصدر":"Source name"}<input name="source_name" placeholder="brochure.pdf"/></label><label>{ar?"المحتوى":"Content"}<textarea name="content" required minLength={20} rows={9}/></label><button className="primaryButton" type="submit"><Plus size={16}/>{ar?"فهرسة المحتوى":"Index content"}</button></form>
      <div className="panel opsForm"><form onSubmit={query}><div className="opsTitle"><BookOpen size={19}/><strong>{ar?"اسأل قاعدة المعرفة":"Query knowledge"}</strong></div><label>{ar?"السؤال":"Question"}<textarea name="question" required rows={4}/></label><button className="primaryButton" type="submit">{ar?"بحث بالمصادر":"Search sources"}</button></form><div className="hitList">{hits.map((h,i)=><article key={h.document_id+"-"+h.chunk_position}><span className="eyebrow">#{i+1} · score {h.score}</span><strong>{h.document_title}</strong><p>{h.text}</p><small>{h.source_name||"internal"}</small></article>)}</div></div>
    </div><section className="panel opsList"><div className="panelHead"><h2>{ar?"المستندات المفهرسة":"Indexed documents"}</h2><span>{docs.length}</span></div>{docs.map(d=><div className="docRow" key={d.id}><BookOpen size={17}/><strong>{d.title}</strong><span>{d.category}</span><span>{d.chunk_count} chunks</span></div>)}</section></div>;
}

export function TasksOps({ token, locale }: { token: string; locale: Locale }) {
  const ar=locale==="ar"; const [tasks,setTasks]=useState<Task[]>([]); const [error,setError]=useState("");
  async function load(){try{setTasks(await callApi("/api/v1/tasks",token));}catch(e){setError(e instanceof Error?e.message:"Load failed");}}
  useEffect(()=>{void load();},[token]);
  async function add(event:FormEvent<HTMLFormElement>){event.preventDefault();const form=event.currentTarget;const d=new FormData(form);try{await callApi("/api/v1/tasks",token,{method:"POST",body:JSON.stringify({title:String(d.get("title")||""),notes:String(d.get("notes")||"")||null,due_at:d.get("due_at")?new Date(String(d.get("due_at"))).toISOString():null})});form.reset();await load();}catch(e){setError(e instanceof Error?e.message:"Save failed");}}
  async function complete(id:string){try{await callApi(`/api/v1/tasks/${id}/complete`,token,{method:"POST"});await load();}catch(e){setError(e instanceof Error?e.message:"Update failed");}}
  return <div className="opsPage"><div className="opsHeading"><div><span className="eyebrow">FOLLOW-UP ENGINE</span><h2>{ar?"المهام والمتابعة":"Tasks & follow-up"}</h2></div></div>{error&&<div className="systemError">{error}</div>}<div className="tasksLayout"><form className="panel opsForm" onSubmit={add}><div className="opsTitle"><ClipboardCheck size={19}/><strong>{ar?"مهمة جديدة":"New task"}</strong></div><label>{ar?"العنوان":"Title"}<input name="title" required/></label><label>{ar?"الموعد":"Due"}<input name="due_at" type="datetime-local"/></label><label>{ar?"ملاحظات":"Notes"}<textarea name="notes" rows={5}/></label><button className="primaryButton" type="submit"><Plus size={16}/>{ar?"إضافة":"Add"}</button></form><section className="panel opsList"><div className="panelHead"><h2>{ar?"قائمة المتابعة":"Follow-up list"}</h2><span>{tasks.length}</span></div>{tasks.map(task=><div className="taskRow" key={task.id}><div><strong>{task.title}</strong><span>{task.due_at?new Date(task.due_at).toLocaleString(ar?"ar-EG":"en-US"):"—"}{task.notes?` · ${task.notes}`:""}</span></div><span className={`statusBadge status-${task.status}`}>{task.status}</span>{task.status==="open"&&<button className="secondaryButton" onClick={()=>void complete(task.id)}><CheckCircle2 size={15}/>{ar?"تم":"Done"}</button>}</div>)}</section></div></div>;
}

export function InboxOps({ token, locale }: { token: string; locale: Locale }) {
  const ar=locale==="ar"; const [items,setItems]=useState<Conversation[]>([]); const [selected,setSelected]=useState<string>(""); const [messages,setMessages]=useState<Message[]>([]); const [error,setError]=useState("");
  async function load(){try{const data=await callApi<Conversation[]>("/api/v1/inbox/conversations",token);setItems(data);if(!selected&&data[0])setSelected(data[0].id);}catch(e){setError(e instanceof Error?e.message:"Load failed");}}
  async function loadMessages(id:string){if(!id){setMessages([]);return;}try{setMessages(await callApi(`/api/v1/inbox/conversations/${id}/messages`,token));}catch(e){setError(e instanceof Error?e.message:"Load failed");}}
  useEffect(()=>{void load();},[token]); useEffect(()=>{void loadMessages(selected);},[selected]);
  async function addConversation(event:FormEvent<HTMLFormElement>){event.preventDefault();const form=event.currentTarget;const d=new FormData(form);try{const c=await callApi<Conversation>("/api/v1/inbox/conversations",token,{method:"POST",body:JSON.stringify({channel:String(d.get("channel")||"manual"),external_contact:String(d.get("external_contact")||""),display_name:String(d.get("display_name")||"")||null})});form.reset();await load();setSelected(c.id);}catch(e){setError(e instanceof Error?e.message:"Save failed");}}
  async function send(event:FormEvent<HTMLFormElement>){event.preventDefault();if(!selected)return;const form=event.currentTarget;const d=new FormData(form);try{await callApi(`/api/v1/inbox/conversations/${selected}/messages`,token,{method:"POST",body:JSON.stringify({direction:"outbound",sender:"operator",body:String(d.get("body")||"")})});form.reset();await loadMessages(selected);}catch(e){setError(e instanceof Error?e.message:"Send failed");}}
  return <div className="opsPage"><div className="opsHeading"><div><span className="eyebrow">OMNICHANNEL INBOX</span><h2>{ar?"صندوق المحادثات الموحد":"Unified conversations"}</h2></div></div>{error&&<div className="systemError">{error}</div>}<div className="inboxLayout"><aside className="panel conversationPane"><form onSubmit={addConversation}><div className="opsTitle"><MessageSquare size={18}/><strong>{ar?"محادثة جديدة":"New conversation"}</strong></div><select name="channel" defaultValue="manual"><option value="manual">Manual</option><option value="whatsapp">WhatsApp</option><option value="instagram">Instagram</option><option value="messenger">Messenger</option><option value="telegram">Telegram</option><option value="website">Website</option><option value="phone">Phone</option></select><input name="external_contact" required placeholder={ar?"رقم/معرّف العميل":"Customer contact"}/><input name="display_name" placeholder={ar?"اسم العميل":"Display name"}/><button className="secondaryButton" type="submit"><Plus size={15}/>{ar?"إضافة":"Add"}</button></form><div className="conversationList">{items.map(item=><button key={item.id} className={selected===item.id?"conversationItem active":"conversationItem"} onClick={()=>setSelected(item.id)}><strong>{item.display_name||item.external_contact}</strong><span>{item.channel} · {item.status}</span></button>)}</div></aside><section className="panel messagePane"><div className="messageList">{messages.map(m=><article key={m.id} className={`messageBubble ${m.direction}`}><small>{m.sender}</small><p>{m.body}</p></article>)}</div>{selected&&<form className="messageComposer" onSubmit={send}><input name="body" required placeholder={ar?"اكتب رسالة...":"Write a message..."}/><button className="primaryButton" type="submit"><Send size={16}/></button></form>}</section></div></div>;
}

export function TeamOps({ token, locale }: { token: string; locale: Locale }) {
  const ar=locale==="ar"; const [users,setUsers]=useState<TeamUser[]>([]); const [error,setError]=useState("");
  async function load(){try{setUsers(await callApi("/api/v1/users",token));}catch(e){setError(e instanceof Error?e.message:"Load failed");}}
  useEffect(()=>{void load();},[token]);
  async function add(event:FormEvent<HTMLFormElement>){event.preventDefault();const form=event.currentTarget;const d=new FormData(form);try{await callApi("/api/v1/users",token,{method:"POST",body:JSON.stringify({email:String(d.get("email")||""),display_name:String(d.get("display_name")||""),password:String(d.get("password")||""),role:String(d.get("role")||"sales_agent")})});form.reset();await load();}catch(e){setError(e instanceof Error?e.message:"Save failed");}}
  return <div className="opsPage"><div className="opsHeading"><div><span className="eyebrow">RBAC</span><h2>{ar?"الفريق والصلاحيات":"Team & permissions"}</h2></div></div>{error&&<div className="systemError">{error}</div>}<div className="tasksLayout"><form className="panel opsForm" onSubmit={add}><div className="opsTitle"><UserPlus size={19}/><strong>{ar?"مستخدم جديد":"New user"}</strong></div><label>{ar?"الاسم":"Name"}<input name="display_name" required/></label><label>Email<input name="email" type="email" required/></label><label>{ar?"كلمة المرور":"Password"}<input name="password" type="password" minLength={10} required/></label><label>{ar?"الصلاحية":"Role"}<select name="role"><option value="sales_agent">Sales Agent</option><option value="sales_manager">Sales Manager</option><option value="finance">Finance</option><option value="viewer">Viewer</option><option value="admin">Admin</option></select></label><button className="primaryButton" type="submit"><UserPlus size={16}/>{ar?"إضافة المستخدم":"Add user"}</button></form><section className="panel opsList"><div className="panelHead"><h2>{ar?"المستخدمون":"Users"}</h2><span>{users.length}</span></div>{users.map(user=><div className="teamRow" key={user.id}><div className="avatar">{user.display_name.slice(0,1)}</div><div><strong>{user.display_name}</strong><span>{user.email}</span></div><span className="statusBadge">{user.role}</span></div>)}</section></div></div>;
}
