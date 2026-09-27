import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  BarChart3,
  BookOpenCheck,
  Camera,
  CircleDollarSign,
  Flag,
  Megaphone,
  MessageCircleQuestion,
  Plus,
  RefreshCw,
  Route,
  Sparkles,
  Target,
  UsersRound,
} from "lucide-react";

type Locale = "ar" | "en";
type Tab = "overview" | "campaigns" | "journeys" | "audiences" | "media" | "playbooks" | "feedback";
const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? "http://localhost:8000" : window.location.origin);

async function api<T>(path:string, token:string, init?:RequestInit):Promise<T>{
  const headers=new Headers(init?.headers); headers.set("Authorization",`Bearer ${token}`);
  if(init?.body) headers.set("Content-Type","application/json");
  const response=await fetch(`${API_URL}${path}`,{...init,headers});
  const body=await response.json().catch(()=>null);
  if(!response.ok) throw new Error(body?.detail||`HTTP ${response.status}`);
  return body as T;
}

type Lead={id:string;full_name:string;source:string;status:string;score:number;preferred_city?:string|null;budget?:number|null};
type Project={id:string;name:string;city:string};
type Unit={id:string;project_id:string;code:string;unit_type:string};
type Campaign={id:string;name:string;channel:string;objective?:string|null;status:string;budget:number;spend:number;currency:string;utm_source?:string|null;utm_medium?:string|null;utm_campaign?:string|null};
type Attribution={campaign_id:string;campaign_name:string;channel:string;spend:number;currency:string;leads_touched:number;contracts_last_touch:number;revenue_last_touch:number;cost_per_lead?:number|null;roas_last_touch?:number|null};
type Journey={id:string;lead_id:string;campaign_id?:string|null;event_type:string;channel?:string|null;metadata:Record<string,unknown>;occurred_at:string};
type Audience={id:string;name:string;description?:string|null;rules:Record<string,unknown>;is_active:boolean;created_at:string};
type Media={id:string;project_id?:string|null;unit_id?:string|null;title:string;media_type:string;url:string;tags:string[];source_kind:string;is_verified:boolean;created_at:string};
type Playbook={id:string;name:string;description?:string|null;trigger_stage?:string|null;steps:string[];is_active:boolean;created_at:string};
type Feedback={id:string;lead_id?:string|null;conversation_id?:string|null;channel?:string|null;category:string;rating?:number|null;comment:string;created_at:string};
type FeedbackSummary={total:number;average_rating?:number|null;rated_count:number;categories:Array<{category:string;count:number}>};

export default function GrowthCenter({token,locale}:{token:string;locale:Locale}){
  const ar=locale==="ar";
  const [tab,setTab]=useState<Tab>("overview");
  const [leads,setLeads]=useState<Lead[]>([]);
  const [projects,setProjects]=useState<Project[]>([]);
  const [units,setUnits]=useState<Unit[]>([]);
  const [campaigns,setCampaigns]=useState<Campaign[]>([]);
  const [attribution,setAttribution]=useState<Attribution[]>([]);
  const [audiences,setAudiences]=useState<Audience[]>([]);
  const [media,setMedia]=useState<Media[]>([]);
  const [playbooks,setPlaybooks]=useState<Playbook[]>([]);
  const [feedback,setFeedback]=useState<Feedback[]>([]);
  const [feedbackSummary,setFeedbackSummary]=useState<FeedbackSummary|null>(null);
  const [journeyLeadId,setJourneyLeadId]=useState("");
  const [journey,setJourney]=useState<Journey[]>([]);
  const [error,setError]=useState("");
  const [notice,setNotice]=useState("");
  const [busy,setBusy]=useState("");

  async function load(){
    setError("");
    try{
      const [l,p,u,c,aud,m,pb,fb,fs,att]=await Promise.all([
        api<Lead[]>("/api/v1/leads",token),
        api<Project[]>("/api/v1/projects",token),
        api<Unit[]>("/api/v1/units",token),
        api<Campaign[]>("/api/v1/growth/campaigns",token),
        api<Audience[]>("/api/v1/growth/audiences",token),
        api<Media[]>("/api/v1/growth/media",token),
        api<Playbook[]>("/api/v1/growth/playbooks",token),
        api<Feedback[]>("/api/v1/growth/feedback",token),
        api<FeedbackSummary>("/api/v1/growth/feedback/summary",token),
        api<Attribution[]>("/api/v1/growth/attribution/campaigns",token),
      ]);
      setLeads(l); setProjects(p); setUnits(u); setCampaigns(c); setAudiences(aud); setMedia(m); setPlaybooks(pb); setFeedback(fb); setFeedbackSummary(fs); setAttribution(att);
      setJourneyLeadId(current=>current||l[0]?.id||"");
    }catch(err){setError(err instanceof Error?err.message:"Load failed");}
  }
  useEffect(()=>{void load();},[token]);
  useEffect(()=>{if(journeyLeadId) void loadJourney(journeyLeadId); else setJourney([]);},[journeyLeadId]);

  async function loadJourney(leadId:string){
    try{setJourney(await api<Journey[]>(`/api/v1/growth/journeys/${leadId}`,token));}
    catch(err){setError(err instanceof Error?err.message:"Journey load failed");}
  }

  async function createCampaign(event:FormEvent<HTMLFormElement>){
    event.preventDefault();const form=event.currentTarget;const d=new FormData(form);setBusy("campaign");setError("");setNotice("");
    try{
      await api("/api/v1/growth/campaigns",token,{method:"POST",body:JSON.stringify({
        name:String(d.get("name")||""),channel:String(d.get("channel")||"facebook"),objective:String(d.get("objective")||"")||null,
        status:String(d.get("status")||"draft"),budget:Number(d.get("budget")||0),spend:Number(d.get("spend")||0),currency:String(d.get("currency")||"EGP"),
        utm_source:String(d.get("utm_source")||"")||null,utm_medium:String(d.get("utm_medium")||"")||null,utm_campaign:String(d.get("utm_campaign")||"")||null,
      })});
      form.reset();setNotice(ar?"تم إنشاء الحملة.":"Campaign created.");await load();
    }catch(err){setError(err instanceof Error?err.message:"Campaign failed");}finally{setBusy("");}
  }

  async function addJourney(event:FormEvent<HTMLFormElement>){
    event.preventDefault();const form=event.currentTarget;const d=new FormData(form);setBusy("journey");setError("");setNotice("");
    try{
      const leadId=String(d.get("lead_id")||"");
      await api("/api/v1/growth/journeys/events",token,{method:"POST",body:JSON.stringify({
        lead_id:leadId,campaign_id:String(d.get("campaign_id")||"")||null,event_type:String(d.get("event_type")||"campaign_touch"),
        channel:String(d.get("channel")||"")||null,metadata:{note:String(d.get("note")||"")},
      })});
      setJourneyLeadId(leadId);setNotice(ar?"تم تسجيل نقطة الرحلة.":"Journey touchpoint recorded.");await loadJourney(leadId);await load();
    }catch(err){setError(err instanceof Error?err.message:"Journey event failed");}finally{setBusy("");}
  }

  async function createAudience(event:FormEvent<HTMLFormElement>){
    event.preventDefault();const form=event.currentTarget;const d=new FormData(form);setBusy("audience");setError("");setNotice("");
    try{
      await api("/api/v1/growth/audiences",token,{method:"POST",body:JSON.stringify({
        name:String(d.get("name")||""),description:String(d.get("description")||"")||null,is_active:true,
        rules:{
          sources:String(d.get("sources")||"").split(",").map(x=>x.trim()).filter(Boolean),
          statuses:String(d.get("statuses")||"").split(",").map(x=>x.trim()).filter(Boolean),
          min_score:d.get("min_score")?Number(d.get("min_score")):null,
          preferred_city:String(d.get("preferred_city")||"")||null,
          min_budget:d.get("min_budget")?Number(d.get("min_budget")):null,
          max_budget:d.get("max_budget")?Number(d.get("max_budget")):null,
        },
      })});
      form.reset();setNotice(ar?"تم حفظ شريحة الجمهور.":"Audience segment saved.");await load();
    }catch(err){setError(err instanceof Error?err.message:"Audience failed");}finally{setBusy("");}
  }

  async function addMedia(event:FormEvent<HTMLFormElement>){
    event.preventDefault();const form=event.currentTarget;const d=new FormData(form);setBusy("media");setError("");setNotice("");
    try{
      const unitId=String(d.get("unit_id")||"")||null;
      const selectedUnit=units.find(u=>u.id===unitId);
      await api("/api/v1/growth/media",token,{method:"POST",body:JSON.stringify({
        project_id:String(d.get("project_id")||"")||selectedUnit?.project_id||null,unit_id:unitId,title:String(d.get("title")||""),
        media_type:String(d.get("media_type")||"image"),url:String(d.get("url")||""),
        tags:String(d.get("tags")||"").split(",").map(x=>x.trim()).filter(Boolean),source_kind:String(d.get("source_kind")||"company"),
        is_verified:d.get("is_verified")==="on",
      })});
      form.reset();setNotice(ar?"تمت إضافة الأصل إلى مكتبة الوسائط.":"Media asset added.");await load();
    }catch(err){setError(err instanceof Error?err.message:"Media failed");}finally{setBusy("");}
  }

  async function createPlaybook(event:FormEvent<HTMLFormElement>){
    event.preventDefault();const form=event.currentTarget;const d=new FormData(form);setBusy("playbook");setError("");setNotice("");
    try{
      await api("/api/v1/growth/playbooks",token,{method:"POST",body:JSON.stringify({
        name:String(d.get("name")||""),description:String(d.get("description")||"")||null,trigger_stage:String(d.get("trigger_stage")||"")||null,
        steps:String(d.get("steps")||"").split("\n").map(x=>x.trim()).filter(Boolean),is_active:true,
      })});
      form.reset();setNotice(ar?"تم حفظ دليل إجراءات المبيعات.":"Sales playbook saved.");await load();
    }catch(err){setError(err instanceof Error?err.message:"Playbook failed");}finally{setBusy("");}
  }

  async function addFeedback(event:FormEvent<HTMLFormElement>){
    event.preventDefault();const form=event.currentTarget;const d=new FormData(form);setBusy("feedback");setError("");setNotice("");
    try{
      await api("/api/v1/growth/feedback",token,{method:"POST",body:JSON.stringify({
        lead_id:String(d.get("lead_id")||"")||null,channel:String(d.get("channel")||"")||null,category:String(d.get("category")||"general"),
        rating:d.get("rating")?Number(d.get("rating")):null,comment:String(d.get("comment")||""),
      })});
      form.reset();setNotice(ar?"تم تسجيل صوت العميل.":"Customer feedback recorded.");await load();
    }catch(err){setError(err instanceof Error?err.message:"Feedback failed");}finally{setBusy("");}
  }

  async function previewAudience(segment:Audience){
    setBusy(segment.id);setError("");
    try{
      const result=await api<{count:number;leads:Array<{name:string;score:number;status:string}>}>(`/api/v1/growth/audiences/${segment.id}/preview`,token);
      setNotice(ar?`${segment.name}: ${result.count} عميل مطابق.`:`${segment.name}: ${result.count} matching leads.`);
    }catch(err){setError(err instanceof Error?err.message:"Preview failed");}finally{setBusy("");}
  }

  const totalRevenue=attribution.reduce((s,x)=>s+Number(x.revenue_last_touch||0),0);
  const totalSpend=attribution.reduce((s,x)=>s+Number(x.spend||0),0);
  const totalTouched=attribution.reduce((s,x)=>s+Number(x.leads_touched||0),0);
  const selectedLead=leads.find(l=>l.id===journeyLeadId);
  const unitLabel=(id?:string|null)=>{const u=units.find(x=>x.id===id);return u?u.code:"—";};
  const projectLabel=(id?:string|null)=>{const p=projects.find(x=>x.id===id);return p?p.name:"—";};

  const tabs:Array<{id:Tab;ar:string;en:string;icon:any}>=[
    {id:"overview",ar:"نظرة عامة",en:"Overview",icon:BarChart3},
    {id:"campaigns",ar:"الحملات والإسناد",en:"Campaigns & Attribution",icon:Megaphone},
    {id:"journeys",ar:"رحلات العملاء",en:"Customer Journeys",icon:Route},
    {id:"audiences",ar:"الجمهور 360",en:"Audience 360",icon:UsersRound},
    {id:"media",ar:"مكتبة الوسائط",en:"Media Library",icon:Camera},
    {id:"playbooks",ar:"دليل الإجراءات",en:"Playbooks",icon:BookOpenCheck},
    {id:"feedback",ar:"صوت العميل",en:"Voice of Customer",icon:MessageCircleQuestion},
  ];

  return <div className="growthCenter">
    <section className="panel growthHero">
      <div><span className="eyebrow">GROWTH & SALES INTELLIGENCE</span><h2>{ar?"مركز النمو والمبيعات":"Growth & Sales Center"}</h2><p>{ar?"مستوحى من أفضل وحدات NEXVARY-DA Marketing OS: الحملات، الرحلات، الإسناد، الجمهور 360، الوسائط، Playbooks وصوت العميل — ومربوط ببيانات العقارات الفعلية.":"Campaigns, journeys, attribution, Audience 360, media, playbooks and customer feedback, grounded in real-estate transactional data."}</p></div>
      <button className="iconButton" onClick={()=>void load()}><RefreshCw size={17}/></button>
    </section>
    {error&&<div className="systemError">{error}</div>}
    {notice&&<div className="successNotice">{notice}</div>}
    <div className="growthTabs">{tabs.map(({id,ar:la,en,icon:Icon})=><button key={id} className={tab===id?"active":""} onClick={()=>setTab(id)}><Icon size={16}/><span>{ar?la:en}</span></button>)}</div>

    {tab==="overview"&&<div className="growthOverview">
      <div className="growthMetrics">
        <Metric label={ar?"الحملات":"Campaigns"} value={String(campaigns.length)} icon={<Megaphone size={18}/>}/>
        <Metric label={ar?"العملاء المتأثرون":"Touched leads"} value={String(totalTouched)} icon={<UsersRound size={18}/>}/>
        <Metric label={ar?"الإنفاق":"Spend"} value={totalSpend.toLocaleString()} icon={<CircleDollarSign size={18}/>}/>
        <Metric label={ar?"إيراد Last-touch":"Last-touch revenue"} value={totalRevenue.toLocaleString()} icon={<Target size={18}/>}/>
        <Metric label={ar?"أصول الوسائط":"Media assets"} value={String(media.length)} icon={<Camera size={18}/>}/>
        <Metric label={ar?"متوسط التقييم":"Avg feedback"} value={feedbackSummary?.average_rating?.toFixed(1)||"—"} icon={<MessageCircleQuestion size={18}/>}/>
      </div>
      <section className="panel growthExplain"><Sparkles size={22}/><div><strong>{ar?"لماذا أضفنا هذه الوحدات؟":"Why these modules?"}</strong><p>{ar?"حتى لا نعرف عدد الـLeads فقط؛ نعرف الحملة التي جلبت العميل، أين وصل في الرحلة، ما الوسائط المناسبة له، وما الخطوات القياسية التي ينفذها الفريق، ثم نربط الصفقة بالإيراد الحقيقي.":"They connect acquisition to lead journey, verified media, repeatable sales actions and real contract revenue instead of stopping at lead counts."}</p></div></section>
    </div>}

    {tab==="campaigns"&&<div className="growthTwoCol">
      <form className="panel growthForm" onSubmit={createCampaign}>
        <div className="opsTitle"><Megaphone size={18}/><strong>{ar?"حملة جديدة":"New campaign"}</strong></div>
        <label>{ar?"الاسم":"Name"}<input name="name" required/></label>
        <div className="formGrid">
          <label>{ar?"القناة":"Channel"}<select name="channel"><option value="facebook">Facebook</option><option value="instagram">Instagram</option><option value="whatsapp">WhatsApp</option><option value="website">Website</option><option value="referral">Referral</option><option value="other">Other</option></select></label>
          <label>{ar?"الحالة":"Status"}<select name="status"><option value="draft">Draft</option><option value="active">Active</option><option value="paused">Paused</option><option value="completed">Completed</option></select></label>
          <label>{ar?"الميزانية":"Budget"}<input name="budget" type="number" min="0" step="0.01" defaultValue="0"/></label>
          <label>{ar?"الإنفاق الفعلي":"Spend"}<input name="spend" type="number" min="0" step="0.01" defaultValue="0"/></label>
          <label>{ar?"العملة":"Currency"}<input name="currency" defaultValue="EGP"/></label>
        </div>
        <label>{ar?"الهدف":"Objective"}<input name="objective"/></label>
        <div className="formGrid"><label>UTM Source<input name="utm_source"/></label><label>UTM Medium<input name="utm_medium"/></label><label>UTM Campaign<input name="utm_campaign"/></label></div>
        <button className="primaryButton" disabled={busy==="campaign"}><Plus size={15}/>{ar?"إنشاء الحملة":"Create campaign"}</button>
      </form>
      <section className="panel attributionPanel">
        <div className="panelHead"><h3>{ar?"الإسناد إلى الإيراد":"Revenue attribution"}</h3><span>Last-touch</span></div>
        <div className="attributionRows">{attribution.map(x=><article key={x.campaign_id}><div><strong>{x.campaign_name}</strong><span>{x.channel}</span></div><span>{x.leads_touched} Leads</span><span>{x.contracts_last_touch} Deals</span><b>{Number(x.revenue_last_touch).toLocaleString()} {x.currency}</b><small>ROAS {x.roas_last_touch??"—"}</small></article>)}</div>
      </section>
    </div>}

    {tab==="journeys"&&<div className="growthTwoCol">
      <form className="panel growthForm" onSubmit={addJourney}>
        <div className="opsTitle"><Route size={18}/><strong>{ar?"تسجيل نقطة رحلة":"Record journey touchpoint"}</strong></div>
        <label>{ar?"العميل":"Lead"}<select name="lead_id" required defaultValue={journeyLeadId} onChange={e=>setJourneyLeadId(e.target.value)}><option value="">{ar?"اختر":"Select"}</option>{leads.map(l=><option key={l.id} value={l.id}>{l.full_name} · {l.status}</option>)}</select></label>
        <label>{ar?"الحملة":"Campaign"}<select name="campaign_id"><option value="">{ar?"بدون حملة":"No campaign"}</option>{campaigns.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
        <div className="formGrid"><label>{ar?"الحدث":"Event"}<select name="event_type"><option value="campaign_touch">campaign_touch</option><option value="message_received">message_received</option><option value="brochure_sent">brochure_sent</option><option value="video_sent">video_sent</option><option value="viewing_requested">viewing_requested</option><option value="follow_up">follow_up</option></select></label><label>{ar?"القناة":"Channel"}<input name="channel" placeholder="facebook / whatsapp"/></label></div>
        <label>{ar?"ملاحظة":"Note"}<textarea name="note" rows={3}/></label>
        <button className="primaryButton" disabled={busy==="journey"}><Plus size={15}/>{ar?"تسجيل الحدث":"Record event"}</button>
      </form>
      <section className="panel journeyTimeline">
        <div className="panelHead"><h3>{ar?"مسار العميل":"Customer journey"}</h3><span>{selectedLead?.full_name||"—"}</span></div>
        {journey.map(item=><article key={item.id}><span className="journeyDot"/><div><strong>{item.event_type}</strong><span>{item.channel||"—"} · {new Date(item.occurred_at).toLocaleString(ar?"ar-EG":"en-US")}</span>{item.campaign_id&&<small>{campaigns.find(c=>c.id===item.campaign_id)?.name||item.campaign_id}</small>}</div></article>)}
        {!journey.length&&<div className="seoEmpty"><Route size={25}/><p>{ar?"لا توجد أحداث بعد.":"No journey events yet."}</p></div>}
      </section>
    </div>}

    {tab==="audiences"&&<div className="growthTwoCol">
      <form className="panel growthForm" onSubmit={createAudience}>
        <div className="opsTitle"><UsersRound size={18}/><strong>{ar?"شريحة جمهور جديدة":"New audience segment"}</strong></div>
        <label>{ar?"الاسم":"Name"}<input name="name" required/></label>
        <label>{ar?"الوصف":"Description"}<textarea name="description" rows={2}/></label>
        <label>{ar?"المصادر مفصولة بفاصلة":"Sources, comma separated"}<input name="sources" placeholder="facebook,whatsapp"/></label>
        <label>{ar?"المراحل مفصولة بفاصلة":"Statuses, comma separated"}<input name="statuses" placeholder="new,qualified,viewing"/></label>
        <div className="formGrid"><label>{ar?"أقل Score":"Min score"}<input name="min_score" type="number" min="0" max="100"/></label><label>{ar?"المدينة":"City"}<input name="preferred_city"/></label><label>{ar?"أقل ميزانية":"Min budget"}<input name="min_budget" type="number" min="0"/></label><label>{ar?"أقصى ميزانية":"Max budget"}<input name="max_budget" type="number" min="0"/></label></div>
        <button className="primaryButton" disabled={busy==="audience"}><Plus size={15}/>{ar?"حفظ الشريحة":"Save segment"}</button>
      </form>
      <section className="panel audienceList"><div className="panelHead"><h3>Audience 360</h3><span>{audiences.length}</span></div>{audiences.map(a=><article key={a.id}><div><strong>{a.name}</strong><span>{a.description||"—"}</span><small>{JSON.stringify(a.rules)}</small></div><button className="secondaryButton" onClick={()=>void previewAudience(a)} disabled={busy===a.id}>{ar?"معاينة":"Preview"}</button></article>)}</section>
    </div>}

    {tab==="media"&&<div className="growthTwoCol">
      <form className="panel growthForm" onSubmit={addMedia}>
        <div className="opsTitle"><Camera size={18}/><strong>{ar?"إضافة أصل حقيقي":"Add media asset"}</strong></div>
        <label>{ar?"المشروع":"Project"}<select name="project_id"><option value="">{ar?"اختياري":"Optional"}</option>{projects.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
        <label>{ar?"الوحدة":"Unit"}<select name="unit_id"><option value="">{ar?"اختياري":"Optional"}</option>{units.map(u=><option key={u.id} value={u.id}>{u.code} · {projectLabel(u.project_id)}</option>)}</select></label>
        <label>{ar?"العنوان":"Title"}<input name="title" required/></label>
        <div className="formGrid"><label>{ar?"النوع":"Type"}<select name="media_type"><option value="image">Image</option><option value="video">Video</option><option value="pdf">PDF</option><option value="floorplan">Floorplan</option><option value="virtual_tour">Virtual tour</option></select></label><label>{ar?"المصدر":"Source"}<select name="source_kind"><option value="company">Company</option><option value="developer">Developer</option><option value="verified">Verified</option><option value="generated">Generated</option></select></label></div>
        <label>URL<input name="url" type="url" required/></label>
        <label>{ar?"وسوم":"Tags"}<input name="tags" placeholder="night, pool, facade"/></label>
        <label className="checkLabel"><input name="is_verified" type="checkbox"/><span>{ar?"تم التحقق من الأصل":"Verified asset"}</span></label>
        <button className="primaryButton" disabled={busy==="media"}><Plus size={15}/>{ar?"إضافة للمكتبة":"Add to library"}</button>
      </form>
      <section className="panel mediaShelf"><div className="panelHead"><h3>{ar?"مكتبة الوسائط":"Media Library"}</h3><span>{media.length}</span></div><div className="mediaRows">{media.map(m=><article key={m.id}><div><strong>{m.title}</strong><span>{m.media_type} · {m.source_kind}{m.is_verified?" · verified":""}</span><small>{projectLabel(m.project_id)} · {unitLabel(m.unit_id)}</small></div><a href={m.url} target="_blank" rel="noreferrer">{ar?"فتح":"Open"}</a></article>)}</div></section>
    </div>}

    {tab==="playbooks"&&<div className="growthTwoCol">
      <form className="panel growthForm" onSubmit={createPlaybook}>
        <div className="opsTitle"><BookOpenCheck size={18}/><strong>{ar?"دليل إجراءات جديد":"New sales playbook"}</strong></div>
        <label>{ar?"الاسم":"Name"}<input name="name" required/></label>
        <label>{ar?"يظهر عند مرحلة":"Trigger stage"}<select name="trigger_stage"><option value="">{ar?"كل المراحل":"All stages"}</option>{["new","qualified","viewing","negotiation","won","lost"].map(x=><option key={x} value={x}>{x}</option>)}</select></label>
        <label>{ar?"الوصف":"Description"}<textarea name="description" rows={2}/></label>
        <label>{ar?"الخطوات — سطر لكل خطوة":"Steps — one per line"}<textarea name="steps" rows={8} required placeholder={ar?"تحقق من الميزانية\nأرسل المشروع المناسب\nحدد موعد معاينة":"Confirm budget\nSend matching project\nSchedule viewing"}/></label>
        <button className="primaryButton" disabled={busy==="playbook"}><Plus size={15}/>{ar?"حفظ الدليل":"Save playbook"}</button>
      </form>
      <section className="panel playbookList"><div className="panelHead"><h3>Playbooks</h3><span>{playbooks.length}</span></div>{playbooks.map(p=><article key={p.id}><Flag size={17}/><div><strong>{p.name}</strong><span>{p.trigger_stage||"all stages"}</span><ol>{p.steps.map((s,i)=><li key={i}>{s}</li>)}</ol></div></article>)}</section>
    </div>}

    {tab==="feedback"&&<div className="growthTwoCol">
      <form className="panel growthForm" onSubmit={addFeedback}>
        <div className="opsTitle"><MessageCircleQuestion size={18}/><strong>{ar?"تسجيل رأي العميل":"Record customer feedback"}</strong></div>
        <label>{ar?"العميل":"Lead"}<select name="lead_id"><option value="">{ar?"اختياري":"Optional"}</option>{leads.map(l=><option key={l.id} value={l.id}>{l.full_name}</option>)}</select></label>
        <div className="formGrid"><label>{ar?"القناة":"Channel"}<input name="channel" placeholder="whatsapp"/></label><label>{ar?"التصنيف":"Category"}<input name="category" defaultValue="general"/></label><label>{ar?"التقييم 1-5":"Rating 1-5"}<input name="rating" type="number" min="1" max="5"/></label></div>
        <label>{ar?"الملاحظة":"Comment"}<textarea name="comment" rows={5} required/></label>
        <button className="primaryButton" disabled={busy==="feedback"}><Plus size={15}/>{ar?"حفظ الرأي":"Save feedback"}</button>
      </form>
      <section className="panel feedbackList">
        <div className="feedbackSummary"><strong>{feedbackSummary?.average_rating?.toFixed(1)||"—"}</strong><span>{ar?"متوسط التقييم":"Average rating"}</span><small>{feedbackSummary?.total||0} records</small></div>
        {feedback.map(f=><article key={f.id}><div><strong>{f.category}{f.rating?` · ${f.rating}/5`:""}</strong><p>{f.comment}</p><small>{f.channel||"—"} · {new Date(f.created_at).toLocaleDateString(ar?"ar-EG":"en-US")}</small></div></article>)}
      </section>
    </div>}
  </div>;
}

function Metric({label,value,icon}:{label:string;value:string;icon:any}){
  return <article className="growthMetric"><div>{icon}</div><span>{label}</span><strong>{value}</strong></article>;
}
