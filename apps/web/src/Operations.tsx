import { FormEvent, useEffect, useState } from "react";
import {
  BookOpen,
  Bot,
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
  async function load(){ try{setDocs(await callApi<KnowledgeDoc[]>("/api/v1/knowledge/documents",token));}catch(e){setError(e instanceof Error?e.message:"Load failed");}}
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
  async function load(){try{setTasks(await callApi<Task[]>("/api/v1/tasks",token));}catch(e){setError(e instanceof Error?e.message:"Load failed");}}
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
  async function load(){try{setUsers(await callApi<TeamUser[]>("/api/v1/users",token));}catch(e){setError(e instanceof Error?e.message:"Load failed");}}
  useEffect(()=>{void load();},[token]);
  async function add(event:FormEvent<HTMLFormElement>){event.preventDefault();const form=event.currentTarget;const d=new FormData(form);try{await callApi("/api/v1/users",token,{method:"POST",body:JSON.stringify({email:String(d.get("email")||""),display_name:String(d.get("display_name")||""),password:String(d.get("password")||""),role:String(d.get("role")||"sales_agent")})});form.reset();await load();}catch(e){setError(e instanceof Error?e.message:"Save failed");}}
  return <div className="opsPage"><div className="opsHeading"><div><span className="eyebrow">RBAC</span><h2>{ar?"الفريق والصلاحيات":"Team & permissions"}</h2></div></div>{error&&<div className="systemError">{error}</div>}<div className="tasksLayout"><form className="panel opsForm" onSubmit={add}><div className="opsTitle"><UserPlus size={19}/><strong>{ar?"مستخدم جديد":"New user"}</strong></div><label>{ar?"الاسم":"Name"}<input name="display_name" required/></label><label>Email<input name="email" type="email" required/></label><label>{ar?"كلمة المرور":"Password"}<input name="password" type="password" minLength={10} required/></label><label>{ar?"الصلاحية":"Role"}<select name="role"><option value="sales_agent">Sales Agent</option><option value="sales_manager">Sales Manager</option><option value="finance">Finance</option><option value="viewer">Viewer</option><option value="admin">Admin</option></select></label><button className="primaryButton" type="submit"><UserPlus size={16}/>{ar?"إضافة المستخدم":"Add user"}</button></form><section className="panel opsList"><div className="panelHead"><h2>{ar?"المستخدمون":"Users"}</h2><span>{users.length}</span></div>{users.map(user=><div className="teamRow" key={user.id}><div className="avatar">{user.display_name.slice(0,1)}</div><div><strong>{user.display_name}</strong><span>{user.email}</span></div><span className="statusBadge">{user.role}</span></div>)}</section></div></div>;
}


type Reservation = {
  id: string;
  lead_id: string;
  unit_id: string;
  reservation_amount: number;
  status: string;
  created_at: string;
};
type Contract = {
  id: string;
  reservation_id: string;
  lead_id: string;
  unit_id: string;
  contract_number: string;
  total_price: number;
  currency: string;
  status: string;
  signed_at: string;
};
type Installment = {
  id: string;
  contract_id: string;
  sequence: number;
  due_at: string;
  amount: number;
  status: string;
  paid_at?: string | null;
};
type Commission = {
  id: string;
  contract_id: string;
  broker_name: string;
  rate_percent: number;
  amount: number;
  status: string;
};

export function FinanceOps({ token, locale }: { token: string; locale: Locale }) {
  const ar = locale === "ar";
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [commissions, setCommissions] = useState<Commission[]>([]);
  const [selectedContract, setSelectedContract] = useState("");
  const [installments, setInstallments] = useState<Installment[]>([]);
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      const [r, c, cm] = await Promise.all([
        callApi<Reservation[]>("/api/v1/reservations", token),
        callApi<Contract[]>("/api/v1/contracts", token),
        callApi<Commission[]>("/api/v1/commissions", token),
      ]);
      setReservations(r);
      setContracts(c);
      setCommissions(cm);
      if (!selectedContract && c[0]) setSelectedContract(c[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    }
  }

  async function loadInstallments(contractId: string) {
    if (!contractId) { setInstallments([]); return; }
    try {
      setInstallments(await callApi<Installment[]>(`/api/v1/contracts/${contractId}/installments`, token));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    }
  }

  useEffect(() => { void load(); }, [token]);
  useEffect(() => { void loadInstallments(selectedContract); }, [selectedContract]);

  async function createContract(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const reservationId = String(data.get("reservation_id") || "");
    try {
      const created = await callApi<Contract>(`/api/v1/contracts/from-reservation/${reservationId}`, token, {
        method: "POST",
        body: JSON.stringify({ contract_number: String(data.get("contract_number") || "") }),
      });
      form.reset();
      await load();
      setSelectedContract(created.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Contract failed");
    }
  }

  async function createSchedule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedContract) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    try {
      await callApi(`/api/v1/contracts/${selectedContract}/schedule`, token, {
        method: "POST",
        body: JSON.stringify({
          first_due_at: new Date(String(data.get("first_due_at") || "")).toISOString(),
          installment_count: Number(data.get("installment_count") || 1),
          frequency_months: Number(data.get("frequency_months") || 1),
        }),
      });
      await loadInstallments(selectedContract);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Schedule failed");
    }
  }

  async function payInstallment(id: string) {
    try {
      await callApi(`/api/v1/installments/${id}/pay`, token, { method: "POST" });
      await loadInstallments(selectedContract);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Payment failed");
    }
  }

  async function createCommission(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedContract) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    try {
      await callApi(`/api/v1/contracts/${selectedContract}/commissions`, token, {
        method: "POST",
        body: JSON.stringify({
          broker_name: String(data.get("broker_name") || ""),
          rate_percent: Number(data.get("rate_percent") || 0),
        }),
      });
      form.reset();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Commission failed");
    }
  }

  async function payCommission(id: string) {
    try {
      await callApi(`/api/v1/commissions/${id}/pay`, token, { method: "POST" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Payment failed");
    }
  }

  const activeReservations = reservations.filter((item) => item.status === "active");
  const selected = contracts.find((item) => item.id === selectedContract);

  return <div className="opsPage">
    <div className="opsHeading"><div><span className="eyebrow">CONTRACTS & FINANCE</span><h2>{ar ? "العقود والأقساط والعمولات" : "Contracts, installments & commissions"}</h2></div></div>
    {error && <div className="systemError">{error}</div>}

    <div className="opsGrid financeGrid">
      <form className="panel opsForm" onSubmit={createContract}>
        <div className="opsTitle"><ClipboardCheck size={19}/><strong>{ar ? "تحويل حجز إلى عقد" : "Convert reservation to contract"}</strong></div>
        <label>{ar ? "الحجز النشط" : "Active reservation"}
          <select name="reservation_id" required><option value="">{ar ? "اختر الحجز" : "Select reservation"}</option>{activeReservations.map(r=><option key={r.id} value={r.id}>{r.id.slice(0,8)} · {r.unit_id.slice(0,8)} · {money(Number(r.reservation_amount),"EGP",locale)}</option>)}</select>
        </label>
        <label>{ar ? "رقم العقد" : "Contract number"}<input name="contract_number" required placeholder="CNT-2026-001"/></label>
        <button className="primaryButton" type="submit">{ar ? "إنشاء العقد وتثبيت البيع" : "Create contract & close sale"}</button>
      </form>

      <section className="panel opsForm">
        <div className="opsTitle"><ClipboardCheck size={19}/><strong>{ar ? "العقد الحالي" : "Selected contract"}</strong></div>
        <label>{ar ? "العقد" : "Contract"}
          <select value={selectedContract} onChange={e=>setSelectedContract(e.target.value)}><option value="">{ar ? "اختر" : "Select"}</option>{contracts.map(c=><option key={c.id} value={c.id}>{c.contract_number}</option>)}</select>
        </label>
        {selected && <div className="financeSummary"><strong>{selected.contract_number}</strong><span>{money(Number(selected.total_price),selected.currency,locale)}</span><span className={`statusBadge status-${selected.status}`}>{selected.status}</span></div>}
      </section>

      <form className="panel opsForm" onSubmit={createSchedule}>
        <div className="opsTitle"><ClipboardCheck size={19}/><strong>{ar ? "جدول الأقساط" : "Installment schedule"}</strong></div>
        <label>{ar ? "أول استحقاق" : "First due date"}<input name="first_due_at" type="datetime-local" required /></label>
        <div className="inlineFields"><label>{ar ? "عدد الأقساط" : "Count"}<input name="installment_count" type="number" min="1" max="240" defaultValue="12" required/></label><label>{ar ? "كل كم شهر" : "Every months"}<input name="frequency_months" type="number" min="1" max="12" defaultValue="1" required/></label></div>
        <button className="primaryButton" type="submit" disabled={!selectedContract}>{ar ? "توليد الجدول" : "Generate schedule"}</button>
      </form>

      <form className="panel opsForm" onSubmit={createCommission}>
        <div className="opsTitle"><ClipboardCheck size={19}/><strong>{ar ? "عمولة وسيط" : "Broker commission"}</strong></div>
        <label>{ar ? "اسم الوسيط" : "Broker name"}<input name="broker_name" required/></label>
        <label>{ar ? "نسبة العمولة %" : "Commission %"}<input name="rate_percent" type="number" min="0.001" max="100" step="0.001" required/></label>
        <button className="primaryButton" type="submit" disabled={!selectedContract}>{ar ? "إضافة العمولة" : "Add commission"}</button>
      </form>
    </div>

    <section className="panel opsList">
      <div className="panelHead"><h2>{ar ? "الأقساط" : "Installments"}</h2><span>{installments.length}</span></div>
      <div className="financeRows">{installments.map(item=><div className="financeRow" key={item.id}><strong>#{item.sequence}</strong><span>{new Date(item.due_at).toLocaleDateString(ar?"ar-EG":"en-US")}</span><span>{money(Number(item.amount), selected?.currency || "EGP", locale)}</span><span className={`statusBadge status-${item.status}`}>{item.status}</span>{item.status==="due"&&<button className="secondaryButton" onClick={()=>void payInstallment(item.id)}>{ar?"تسجيل سداد":"Mark paid"}</button>}</div>)}</div>
    </section>

    <section className="panel opsList">
      <div className="panelHead"><h2>{ar ? "العمولات" : "Commissions"}</h2><span>{commissions.length}</span></div>
      <div className="financeRows">{commissions.map(item=><div className="financeRow" key={item.id}><strong>{item.broker_name}</strong><span>{Number(item.rate_percent)}%</span><span>{money(Number(item.amount), selected?.currency || "EGP", locale)}</span><span className={`statusBadge status-${item.status}`}>{item.status}</span>{item.status==="pending"&&<button className="secondaryButton" onClick={()=>void payCommission(item.id)}>{ar?"تسجيل السداد":"Mark paid"}</button>}</div>)}</div>
    </section>
  </div>;
}


type CopilotResult = {
  answer: string;
  units: Array<{
    id: string;
    code: string;
    project_id: string;
    unit_type: string;
    bedrooms?: number | null;
    area_sqm: number;
    price: number;
    currency: string;
  }>;
  media: Array<{
    id: string;
    project_id?: string | null;
    unit_id?: string | null;
    title: string;
    media_type: string;
    url: string;
    verified: boolean;
  }>;
  evidence: Array<{
    document_title: string;
    source_name?: string | null;
    chunk_position: number;
    text: string;
    score: number;
  }>;
  grounding: string[];
  mode: string;
};

export function AICopilotOps({ token, locale }: { token: string; locale: Locale }) {
  const ar = locale === "ar";
  const [result, setResult] = useState<CopilotResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function ask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setBusy(true);
    setError("");
    try {
      const response = await callApi<CopilotResult>("/api/v1/ai/sales/assist", token, {
        method: "POST",
        body: JSON.stringify({
          question: String(data.get("question") || ""),
          city: String(data.get("city") || "") || null,
          max_price: data.get("max_price") ? Number(data.get("max_price")) : null,
          bedrooms: data.get("bedrooms") ? Number(data.get("bedrooms")) : null,
          unit_type: String(data.get("unit_type") || "") || null,
          limit: 8,
        }),
      });
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "AI query failed");
    } finally {
      setBusy(false);
    }
  }

  return <div className="opsPage">
    <div className="opsHeading">
      <div><span className="eyebrow">GROUNDED AI SALES COPILOT</span><h2>{ar ? "مساعد المبيعات الذكي" : "AI Sales Copilot"}</h2></div>
    </div>
    {error && <div className="systemError">{error}</div>}
    <div className="aiOpsGrid">
      <form className="panel opsForm" onSubmit={ask}>
        <div className="opsTitle"><Bot size={20}/><strong>{ar ? "اسأل عن الوحدات أو المشروع" : "Ask about inventory or a project"}</strong></div>
        <label>{ar ? "السؤال" : "Question"}<textarea name="question" required rows={6} placeholder={ar ? "مثال: أريد شقة 3 غرف في القاهرة الجديدة..." : "Example: I need a 3-bedroom apartment in New Cairo..."}/></label>
        <div className="formGrid">
          <label>{ar ? "المدينة" : "City"}<input name="city"/></label>
          <label>{ar ? "أقصى سعر" : "Max price"}<input name="max_price" type="number" min="0"/></label>
          <label>{ar ? "غرف النوم" : "Bedrooms"}<input name="bedrooms" type="number" min="0" max="30"/></label>
          <label>{ar ? "نوع الوحدة" : "Unit type"}<input name="unit_type"/></label>
        </div>
        <button className="primaryButton" type="submit" disabled={busy}>
          {busy ? <RefreshCw size={17} className="spin"/> : <Bot size={17}/>}
          {ar ? "تحليل البيانات" : "Analyze live data"}
        </button>
        <div className="truthRules"><span>DB → Price</span><span>DB → Availability</span><span>Knowledge → Evidence</span><span>Media → Verified assets</span></div>
      </form>

      <section className="panel copilotResult">
        {!result && <div className="emptyAi"><Bot size={30}/><p>{ar ? "سيعرض المساعد النتائج المؤكدة هنا بدون اختراع أسعار أو وحدات." : "Grounded results appear here without invented pricing or inventory."}</p></div>}
        {result && <>
          <span className="eyebrow">{result.mode}</span>
          <h3>{ar ? "النتيجة" : "Result"}</h3>
          <p className="copilotAnswer">{result.answer}</p>
          <div className="groundingRow">{result.grounding.map(item=><span key={item}>{item}</span>)}</div>
          <h3>{ar ? "الوحدات المطابقة" : "Matching units"}</h3>
          <div className="copilotUnits">{result.units.map(unit=><article key={unit.id}><strong>{unit.code}</strong><span>{unit.unit_type} · {unit.bedrooms ?? "—"} BR · {Number(unit.area_sqm).toLocaleString()} m²</span><b>{money(Number(unit.price), unit.currency, locale)}</b></article>)}</div>
          <h3>{ar ? "الوسائط المرتبطة" : "Related media"}</h3>
          <div className="copilotMedia">{result.media.map(item=><a key={item.id} href={item.url} target="_blank" rel="noreferrer"><strong>{item.title}</strong><span>{item.media_type}{item.verified ? " · verified" : ""}</span></a>)}</div>
          <h3>{ar ? "المصادر" : "Sources"}</h3>
          <div className="hitList">{result.evidence.map((hit,index)=><article key={hit.document_title+"-"+hit.chunk_position}><span className="eyebrow">#{index+1} · score {hit.score}</span><strong>{hit.document_title}</strong><p>{hit.text}</p><small>{hit.source_name || "internal"}</small></article>)}</div>
        </>}
      </section>
    </div>
  </div>;
}


type TenantSettings = {
  id: string;
  name: string;
  slug: string;
  brand_name?: string | null;
  primary_color: string;
  logo_data_url?: string | null;
  cover_data_url?: string | null;
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
type AuditEntry = {
  id: string;
  actor: string;
  action: string;
  entity_type: string;
  entity_id?: string | null;
  details?: string | null;
  created_at: string;
};

export function SettingsOps({
  token,
  locale,
  onSaved,
}: {
  token: string;
  locale: Locale;
  onSaved?: () => void;
}) {
  const ar = locale === "ar";
  const [settings, setSettings] = useState<TenantSettings | null>(null);
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");
  const [logoData, setLogoData] = useState<string | null>(null);
  const [coverData, setCoverData] = useState<string | null>(null);

  async function load() {
    try {
      const [s, a] = await Promise.all([
        callApi<TenantSettings>("/api/v1/tenant/settings", token),
        callApi<AuditEntry[]>("/api/v1/audit?limit=80", token),
      ]);
      setSettings(s);
      setLogoData(s.logo_data_url || null);
      setCoverData(s.cover_data_url || null);
      setAudit(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    }
  }

  useEffect(() => { void load(); }, [token]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setError("");
    setSaved("");
    try {
      const updated = await callApi<TenantSettings>("/api/v1/tenant/settings", token, {
        method: "PATCH",
        body: JSON.stringify({
          brand_name: String(data.get("brand_name") || "").trim(),
          primary_color: String(data.get("primary_color") || "#0B1F33"),
          logo_data_url: logoData,
          cover_data_url: coverData,
          contact_email: String(data.get("contact_email") || "").trim() || null,
          website_url: String(data.get("website_url") || "").trim() || null,
          facebook_url: String(data.get("facebook_url") || "").trim() || null,
          linkedin_url: String(data.get("linkedin_url") || "").trim() || null,
          youtube_url: String(data.get("youtube_url") || "").trim() || null,
          x_url: String(data.get("x_url") || "").trim() || null,
          tiktok_url: String(data.get("tiktok_url") || "").trim() || null,
        }),
      });
      setSettings(updated);
      setSaved(ar ? "تم حفظ الهوية." : "Brand settings saved.");
      onSaved?.();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    }
  }

  async function backup() {
    setError("");
    try {
      const response = await fetch(`${API_URL}/api/v1/backup/export`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body?.detail || "Backup failed");
      const blob = new Blob([JSON.stringify(body, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const date = new Date().toISOString().slice(0, 10);
      anchor.href = url;
      anchor.download = `NEXVARY-RealEstate-Backup-${date}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Backup failed");
    }
  }

  return <div className="opsPage">
    <div className="opsHeading"><div><span className="eyebrow">WHITE LABEL & AUDIT</span><h2>{ar ? "إعدادات الشركة والسجل" : "Company settings & audit"}</h2></div></div>
    {error && <div className="systemError">{error}</div>}
    {saved && <div className="successNotice">{saved}</div>}
    <div className="settingsGrid">
      <form className="panel opsForm" onSubmit={save}>
        <div className="opsTitle"><Building2 size={19}/><strong>{ar ? "هوية الشركة" : "Company identity"}</strong></div>
        <label>{ar ? "اسم الشركة المسجل" : "Registered company"}<input value={settings?.name || ""} disabled /></label>
        <label>{ar ? "معرّف الشركة" : "Company identifier"}<input value={settings?.slug || ""} disabled /></label>
        <label>{ar ? "الاسم التجاري الظاهر" : "Displayed brand"}<input name="brand_name" defaultValue={settings?.brand_name || settings?.name || ""} key={settings?.brand_name || settings?.name}/></label>
        <label>{ar ? "لون الهوية" : "Brand color"}<input name="primary_color" type="color" defaultValue={settings?.primary_color || "#0B1F33"} key={settings?.primary_color}/></label>
        <div className="brandLogoEditor">
          <div className="brandLogoPreview">
            {logoData ? <img src={logoData} alt="Company logo"/> : <Building2 size={28}/>}
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
              reader.onload = () => setLogoData(typeof reader.result === "string" ? reader.result : null);
              reader.readAsDataURL(file);
            }}/>
          </label>
          {logoData && <button type="button" className="secondaryButton" onClick={() => setLogoData(null)}>{ar ? "إزالة الشعار" : "Remove logo"}</button>}
        </div>
        <div className="brandCoverEditor">
          <div className="brandCoverPreview" style={coverData ? { backgroundImage: `linear-gradient(90deg, rgba(2,8,16,.62), rgba(2,8,16,.22)), url("${coverData}")` } : undefined}>
            {!coverData && <><span>NEXVARY</span><small>{ar ? "غلاف الشركة" : "Company cover"}</small></>}
          </div>
          <label>{ar ? "صورة غلاف الشركة PNG/JPG/WEBP" : "Company cover PNG/JPG/WEBP"}
            <input type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => {
              const file = event.target.files?.[0];
              if (!file) return;
              if (file.size > 3_000_000) {
                setError(ar ? "حجم صورة الغلاف يجب ألا يتجاوز 3 ميجابايت." : "Cover image must be 3 MB or smaller.");
                event.target.value = "";
                return;
              }
              const reader = new FileReader();
              reader.onload = () => setCoverData(typeof reader.result === "string" ? reader.result : null);
              reader.readAsDataURL(file);
            }}/>
          </label>
          {coverData && <button type="button" className="secondaryButton" onClick={() => setCoverData(null)}>{ar ? "إزالة صورة الغلاف" : "Remove cover"}</button>}
        </div>
        <div className="formGrid">
          <label>{ar ? "بريد التواصل" : "Contact email"}<input name="contact_email" type="email" defaultValue={settings?.contact_email || ""}/></label>
          <label>{ar ? "الموقع الإلكتروني" : "Website"}<input name="website_url" defaultValue={settings?.website_url || ""} placeholder="https://company.com"/></label>
          <label>Facebook<input name="facebook_url" defaultValue={settings?.facebook_url || ""}/></label>
          <label>LinkedIn<input name="linkedin_url" defaultValue={settings?.linkedin_url || ""}/></label>
          <label>YouTube<input name="youtube_url" defaultValue={settings?.youtube_url || ""}/></label>
          <label>X<input name="x_url" defaultValue={settings?.x_url || ""}/></label>
          <label>TikTok<input name="tiktok_url" defaultValue={settings?.tiktok_url || ""}/></label>
          <label>{ar ? "النطاق المخصص" : "Custom domain"}<input value={settings?.custom_domain || "—"} disabled/></label>
        </div>
        <div className="planReadOnly">
          <span>{ar ? "الخطة" : "Plan"}: <strong>{settings?.plan || "—"}</strong></span>
          <span>{ar ? "الحالة" : "Status"}: <strong>{settings?.lifecycle || "—"}</strong></span>
        </div>
        <button className="primaryButton" type="submit">{ar ? "حفظ الهوية" : "Save branding"}</button>
        <button className="secondaryButton" type="button" onClick={() => void backup()}>{ar ? "تصدير نسخة احتياطية JSON" : "Export JSON backup"}</button>
      </form>
      <section className="panel opsList">
        <div className="panelHead"><h2>{ar ? "سجل العمليات" : "Audit log"}</h2><span>{audit.length}</span></div>
        <div className="auditList">{audit.map(item=><div className="auditRow" key={item.id}><div><strong>{item.action}</strong><span>{item.actor} · {item.entity_type}</span></div><span>{new Date(item.created_at).toLocaleString(ar?"ar-EG":"en-US")}</span></div>)}</div>
      </section>
    </div>
  </div>;
}
