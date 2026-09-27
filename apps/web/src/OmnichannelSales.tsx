import { FormEvent, useEffect, useState } from "react";
import { Bot, CheckCircle2, Headphones, MessageSquare, Plus, RefreshCw, Send, ShieldCheck, Sparkles, Volume2, XCircle } from "lucide-react";

type Locale = "ar" | "en";
const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? "http://localhost:8000" : window.location.origin);

type Conversation = { id:string; channel:string; external_contact:string; display_name?:string|null; status:string; last_message_at:string };
type Message = { id:string; direction:string; sender:string; body:string; created_at:string };
type SalesState = { conversation_id:string; reply_preference:string; journey_stage:string; lead_score:number; campaign_id?:string|null; ad_id?:string|null; auto_reply_enabled:boolean; handoff_required:boolean; handoff_reason?:string|null };
type Outbox = { id:string; conversation_id:string; kind:string; body?:string|null; grounded:boolean; source_confidence:number; status:string; attempts:number; last_error?:string|null };
type Campaign = { campaign_id:string; events:Record<string,number>; revenue:string };
type PropertyContext = { id:string; conversation_id:string; campaign_id?:string|null; ad_id?:string|null; source_url?:string|null; project_id?:string|null; project_name?:string|null; project_city?:string|null; unit_id?:string|null; unit_code?:string|null };
type PropertyMedia = { id:string; project_id?:string|null; unit_id?:string|null; title:string; media_type:string; url:string; source_kind:string; verified:boolean };
type Referral = { id:string; channel:string; campaign_id?:string|null; ad_id:string; project_id:string; project_name:string; unit_id?:string|null; unit_code?:string|null; label?:string|null; source_url?:string|null };
type Project = { id:string; name:string; city:string };
type Unit = { id:string; project_id:string; code:string; unit_type:string; status:string };

async function api<T>(path:string, token:string, init?:RequestInit):Promise<T>{
  const headers=new Headers(init?.headers); headers.set("Authorization","Bearer "+token);
  if(init?.body) headers.set("Content-Type","application/json");
  const response=await fetch(API_URL+path,{...init,headers});
  const body=await response.json().catch(()=>null);
  if(!response.ok) throw new Error(body?.detail||("HTTP "+response.status));
  return body as T;
}

export default function OmnichannelSales({token,locale}:{token:string;locale:Locale}){
  const ar=locale==="ar";
  const [items,setItems]=useState<Conversation[]>([]);
  const [selected,setSelected]=useState("");
  const [messages,setMessages]=useState<Message[]>([]);
  const [state,setState]=useState<SalesState|null>(null);
  const [outbox,setOutbox]=useState<Outbox[]>([]);
  const [campaigns,setCampaigns]=useState<Campaign[]>([]);
  const [voicePlan,setVoicePlan]=useState<string[]>([]);
  const [propertyContext,setPropertyContext]=useState<PropertyContext|null>(null);
  const [propertyMedia,setPropertyMedia]=useState<PropertyMedia[]>([]);
  const [referrals,setReferrals]=useState<Referral[]>([]);
  const [projects,setProjects]=useState<Project[]>([]);
  const [units,setUnits]=useState<Unit[]>([]);
  const [error,setError]=useState("");
  const [notice,setNotice]=useState("");
  const [busy,setBusy]=useState("");

  async function loadConversations(){
    try{
      const data=await api<Conversation[]>("/api/v1/inbox/conversations",token);
      setItems(data); setSelected((v)=>v||data[0]?.id||"");
    }catch(e){setError(e instanceof Error?e.message:"Load failed");}
  }
  async function loadSelected(id:string){
    if(!id){setMessages([]);setState(null);setOutbox([]);setPropertyContext(null);setPropertyMedia([]);return;}
    try{
      const [m,s,o,a,pc]=await Promise.all([
        api<Message[]>("/api/v1/inbox/conversations/"+id+"/messages",token),
        api<SalesState>("/api/v1/omnichannel/conversations/"+id+"/sales-state",token),
        api<Outbox[]>("/api/v1/omnichannel/outbox",token),
        api<Campaign[]>("/api/v1/omnichannel/attribution/campaigns",token),
        api<{context:PropertyContext|null}>("/api/v1/property-sales/conversations/"+id+"/context",token)
      ]);
      setMessages(m); setState(s); setOutbox(o.filter((x)=>x.conversation_id===id)); setCampaigns(a); setPropertyContext(pc.context);
    }catch(e){setError(e instanceof Error?e.message:"Load failed");}
  }
  async function loadPropertySales(){
    try{
      const [r,p,u]=await Promise.all([
        api<Referral[]>("/api/v1/property-sales/ad-referrals",token),
        api<Project[]>("/api/v1/projects",token),
        api<Unit[]>("/api/v1/units",token)
      ]);
      setReferrals(r); setProjects(p); setUnits(u);
    }catch(e){setError(e instanceof Error?e.message:"Property sales load failed");}
  }
  useEffect(()=>{void loadConversations();void loadPropertySales();},[token]);
  useEffect(()=>{void loadSelected(selected);},[selected,token]);

  async function createManual(event:FormEvent<HTMLFormElement>){
    event.preventDefault(); const form=event.currentTarget; const d=new FormData(form); setError(""); setNotice("");
    try{
      const created=await api<Conversation>("/api/v1/inbox/conversations",token,{method:"POST",body:JSON.stringify({
        channel:String(d.get("channel")||"manual"),
        external_contact:String(d.get("external_contact")||"").trim(),
        display_name:String(d.get("display_name")||"").trim()||null
      })});
      form.reset(); await loadConversations(); setSelected(created.id);
    }catch(e){setError(e instanceof Error?e.message:"Conversation creation failed");}
  }

  async function patchState(patch:Record<string,unknown>){
    if(!selected)return;
    try{
      setState(await api<SalesState>("/api/v1/omnichannel/conversations/"+selected+"/sales-state",token,{method:"PATCH",body:JSON.stringify(patch)}));
    }catch(e){setError(e instanceof Error?e.message:"Update failed");}
  }

  async function prepare(event:FormEvent<HTMLFormElement>){
    event.preventDefault(); if(!selected)return;
    const d=new FormData(event.currentTarget); setBusy("reply"); setError(""); setNotice(""); setVoicePlan([]);
    try{
      const result=await api<any>("/api/v1/omnichannel/conversations/"+selected+"/grounded-reply",token,{method:"POST",body:JSON.stringify({
        question:String(d.get("question")||""), city:String(d.get("city")||"")||null,
        max_price:d.get("max_price")?Number(d.get("max_price")):null,
        bedrooms:d.get("bedrooms")?Number(d.get("bedrooms")):null,
        unit_type:String(d.get("unit_type")||"")||null, source_confidence:0.95
      })});
      if(result.voice_plan?.segments)setVoicePlan(result.voice_plan.segments);
      setPropertyMedia(Array.isArray(result.media)?result.media:[]);
      setNotice(result.requires_handoff
        ? (ar?"لا توجد إجابة تجارية مؤكدة؛ تم إنشاء تحويل لموظف.":"No verified commercial answer; a human handoff was created.")
        : result.approval_required
          ? (ar?"الرد مؤكد وهو في انتظار اعتماد موظف.":"Grounded reply is waiting for human approval.")
          : (ar?"الرد مؤكد ومسموح بالإرسال التلقائي.":"Grounded reply is eligible for automatic delivery."));
      await loadSelected(selected);
    }catch(e){setError(e instanceof Error?e.message:"Reply preparation failed");}
    finally{setBusy("");}
  }

  async function createReferral(event:FormEvent<HTMLFormElement>){
    event.preventDefault(); const form=event.currentTarget; const d=new FormData(form); setError(""); setNotice("");
    try{
      await api<Referral>("/api/v1/property-sales/ad-referrals",token,{method:"POST",body:JSON.stringify({
        channel:"whatsapp",
        campaign_id:String(d.get("campaign_id")||"").trim()||null,
        ad_id:String(d.get("ad_id")||"").trim(),
        project_id:String(d.get("project_id")||""),
        unit_id:String(d.get("unit_id")||"")||null,
        label:String(d.get("label")||"").trim()||null,
        source_url:String(d.get("source_url")||"").trim()||null
      })});
      form.reset(); setNotice(ar?"تم ربط الإعلان بالعقار.":"Ad mapped to property."); await loadPropertySales();
    }catch(e){setError(e instanceof Error?e.message:"Referral mapping failed");}
  }

  async function queueMedia(){
    if(!selected||propertyMedia.length===0)return; setBusy("media"); setError(""); setNotice("");
    try{
      const rows=await api<any[]>("/api/v1/property-sales/conversations/"+selected+"/media-outbox",token,{method:"POST",body:JSON.stringify({asset_ids:propertyMedia.map((x)=>x.id).slice(0,10)})});
      setNotice(ar?`تمت إضافة ${rows.length} وسائط موثقة إلى صندوق الإرسال.`:`${rows.length} verified media items queued.`);
      await loadSelected(selected);
    }catch(e){setError(e instanceof Error?e.message:"Media queue failed");}
    finally{setBusy("");}
  }

  async function action(id:string,kind:"approve"|"reject"|"dispatch"){
    setBusy(id); setError(""); setNotice("");
    try{
      const result=await api<Outbox>("/api/v1/omnichannel/outbox/"+id+"/"+kind,token,{method:"POST"});
      setNotice(kind==="dispatch"
        ? (result.status==="sent"?(ar?"تم الإرسال عبر WhatsApp الرسمي.":"Sent through official WhatsApp."):(result.last_error||result.status))
        : kind==="approve"?(ar?"تم اعتماد الرسالة.":"Message approved."):(ar?"تم رفض الرسالة.":"Message rejected."));
      await loadSelected(selected);
    }catch(e){setError(e instanceof Error?e.message:"Action failed");}
    finally{setBusy("");}
  }

  async function handoff(event:FormEvent<HTMLFormElement>){
    event.preventDefault(); if(!selected)return; const d=new FormData(event.currentTarget);
    try{
      await api("/api/v1/omnichannel/conversations/"+selected+"/handoff",token,{method:"POST",body:JSON.stringify({reason:String(d.get("reason")||"")})});
      setNotice(ar?"تم التحويل لموظف وإنشاء مهمة متابعة.":"Handoff created with a follow-up task.");
      (event.currentTarget as HTMLFormElement).reset(); await loadSelected(selected);
    }catch(e){setError(e instanceof Error?e.message:"Handoff failed");}
  }

  return <div className="salesInbox">
    <div className="opsHeading"><div><span className="eyebrow">GROUNDED OMNICHANNEL SALES</span><h2>{ar?"مبيعات ومحادثات العملاء":"Customer conversations & AI sales"}</h2></div><button className="iconButton" onClick={()=>{void loadConversations();void loadSelected(selected);}}><RefreshCw size={17}/></button></div>
    <div className="panel salesSafety"><ShieldCheck size={18}/><div><strong>{ar?"الرد التلقائي للبيانات المؤكدة فقط":"Auto-replies require grounded data"}</strong><span>{ar?"السعر والتوافر من قاعدة الوحدات؛ غير المؤكد يتحول لموظف.":"Price and availability come from inventory; unverified facts are handed to staff."}</span></div></div>
    {error&&<div className="systemError">{error}</div>}{notice&&<div className="successNotice">{notice}</div>}

    <div className="salesInboxLayout">
      <aside className="panel salesConversationRail"><div className="panelHead"><h3>{ar?"المحادثات":"Conversations"}</h3><span>{items.length}</span></div><form className="salesConversationCreate" onSubmit={createManual}><select name="channel" defaultValue="manual"><option value="manual">Manual</option><option value="whatsapp">WhatsApp</option><option value="messenger">Messenger</option><option value="instagram">Instagram</option><option value="website">Website</option></select><input name="external_contact" required placeholder={ar?"رقم/معرّف العميل":"Customer contact"}/><input name="display_name" placeholder={ar?"اسم العميل":"Customer name"}/><button className="secondaryButton"><Plus size={14}/>{ar?"إضافة":"Add"}</button></form><div className="conversationList">{items.map((x)=><button key={x.id} className={selected===x.id?"conversationItem active":"conversationItem"} onClick={()=>setSelected(x.id)}><strong>{x.display_name||x.external_contact}</strong><span>{x.channel+" · "+x.status}</span></button>)}</div></aside>
      <section className="panel salesConversationMain">
        {!selected&&<div className="seoEmpty"><MessageSquare size={26}/><p>{ar?"اختر محادثة.":"Select a conversation."}</p></div>}
        {selected&&<>
          <div className="salesStateBar">
            <label>{ar?"طريقة الرد":"Reply"}<select value={state?.reply_preference||"unset"} onChange={(e)=>void patchState({reply_preference:e.target.value})}><option value="unset">{ar?"غير محدد":"Unset"}</option><option value="text">{ar?"كتابة":"Text"}</option><option value="voice">{ar?"صوت":"Voice"}</option></select></label>
            <label>{ar?"المرحلة":"Stage"}<select value={state?.journey_stage||"new"} onChange={(e)=>void patchState({journey_stage:e.target.value})}><option value="new">New</option><option value="asked_price">Asked price</option><option value="interested">Interested</option><option value="explained">Explained</option><option value="qualified">Qualified</option><option value="viewing_requested">Viewing</option><option value="high_intent">High intent</option><option value="reservation_requested">Reservation</option><option value="won">Won</option><option value="lost">Lost</option></select></label>
            <label>{ar?"Lead Score":"Lead score"}<input type="number" min="0" max="100" value={state?.lead_score??0} onChange={(e)=>void patchState({lead_score:Number(e.target.value)})}/></label>
            <label className="autoReplyToggle"><input type="checkbox" checked={Boolean(state?.auto_reply_enabled)} onChange={(e)=>void patchState({auto_reply_enabled:e.target.checked})}/><span>{ar?"رد تلقائي مؤكد فقط":"Grounded auto-reply only"}</span></label>
          </div>
          {(state?.campaign_id||state?.ad_id)&&<div className="campaignContext"><Sparkles size={14}/><span>{(state?.campaign_id||"")+" "+(state?.ad_id?"· "+state.ad_id:"")}</span></div>}
          {propertyContext&&<div className="campaignContext propertyContext"><ShieldCheck size={14}/><span>{ar?"العقار المرتبط: ":"Property context: "}{propertyContext.project_name||propertyContext.project_id}{propertyContext.unit_code?" · "+propertyContext.unit_code:""}{propertyContext.source_url&&<a href={propertyContext.source_url} target="_blank" rel="noreferrer">{ar?"مصدر الإعلان":"Ad source"}</a>}</span></div>}
          {state?.handoff_required&&<div className="handoffBadge"><Headphones size={14}/>{state.handoff_reason|| (ar?"مطلوب موظف":"Human required")}</div>}
          <div className="salesMessages">{messages.map((m)=><article key={m.id} className={"messageBubble "+m.direction}><small>{m.sender}</small><p>{m.body}</p></article>)}</div>
        </>}
      </section>
    </div>

    {selected&&<div className="salesToolsGrid">
      <form className="panel opsForm" onSubmit={prepare}><div className="opsTitle"><Bot size={19}/><strong>{ar?"تجهيز رد مبيعات مؤكد":"Prepare grounded sales reply"}</strong></div>
        <label>{ar?"سؤال العميل":"Customer question"}<textarea name="question" rows={4} required/></label>
        <div className="formGrid"><label>{ar?"المدينة":"City"}<input name="city"/></label><label>{ar?"أقصى سعر":"Max price"}<input name="max_price" type="number" min="0"/></label><label>{ar?"الغرف":"Bedrooms"}<input name="bedrooms" type="number" min="0"/></label><label>{ar?"نوع الوحدة":"Unit type"}<input name="unit_type"/></label></div>
        <button className="primaryButton" disabled={busy==="reply"}>{busy==="reply"?<RefreshCw size={16} className="spin"/>:<Bot size={16}/>} {ar?"تجهيز الرد":"Prepare reply"}</button>
        {voicePlan.length>0&&<div className="voicePlan"><Volume2 size={17}/><div><strong>{ar?"خطة صوت أنثوي احترافي":"Professional female voice plan"}</strong>{voicePlan.map((x,i)=><p key={i}>{String(i+1)+". "+x}</p>)}</div></div>}
        {propertyMedia.length>0&&<div className="propertyMediaResult"><div className="opsTitle"><ShieldCheck size={17}/><strong>{ar?"وسائط العقار الموثقة":"Verified property media"}</strong></div><div className="propertyMediaCards">{propertyMedia.map((m)=><article key={m.id}><span>{m.media_type}</span><strong>{m.title}</strong><a href={m.url} target="_blank" rel="noreferrer">{ar?"فتح المصدر":"Open source"}</a></article>)}</div><button type="button" className="secondaryButton" disabled={busy==="media"} onClick={()=>void queueMedia()}><Send size={15}/>{ar?"إضافة الوسائط إلى Outbox":"Queue media to Outbox"}</button></div>}
      </form>

      <section className="panel outboxPanel"><div className="panelHead"><h3>{ar?"Outbox والموافقات":"Outbox & approvals"}</h3><span>{outbox.length}</span></div><div className="outboxList">{outbox.map((x)=><article key={x.id}><div>{x.status==="sent"?<CheckCircle2 size={17}/>:x.status==="rejected"?<XCircle size={17}/>:<Send size={17}/>}</div><div><strong>{x.kind+" · "+x.status}</strong><p>{x.body||"—"}</p><small>{(x.grounded?"grounded":"not grounded")+" · "+Number(x.source_confidence).toFixed(2)}</small>{x.last_error&&<small className="outboxError">{x.last_error}</small>}</div><div className="outboxActions">{x.status==="pending_approval"&&<><button className="secondaryButton" onClick={()=>void action(x.id,"approve")}>{ar?"اعتماد":"Approve"}</button><button className="secondaryButton" onClick={()=>void action(x.id,"reject")}>{ar?"رفض":"Reject"}</button></>}{x.status==="approved"&&<button className="primaryButton" onClick={()=>void action(x.id,"dispatch")}>{ar?"إرسال رسمي":"Dispatch"}</button>}</div></article>)}</div></section>

      <form className="panel opsForm" onSubmit={handoff}><div className="opsTitle"><Headphones size={19}/><strong>{ar?"تحويل لموظف":"Human handoff"}</strong></div><label>{ar?"السبب":"Reason"}<textarea name="reason" rows={4} required/></label><button className="secondaryButton"><Headphones size={15}/>{ar?"تحويل وإنشاء مهمة":"Handoff & create task"}</button></form>

      <section className="panel attributionPanel"><div className="panelHead"><h3>{ar?"نسب الحملات":"Campaign attribution"}</h3><span>{campaigns.length}</span></div><div className="attributionCards">{campaigns.map((c)=><article key={c.campaign_id}><strong>{c.campaign_id}</strong><div>{Object.entries(c.events).map(([k,v])=><span key={k}>{k+": "+v}</span>)}</div><b>{"Revenue: "+Number(c.revenue).toLocaleString()}</b></article>)}</div></section>
    </div>}

    <section className="panel referralManager">
      <div className="panelHead"><div><span className="eyebrow">WHATSAPP AD → PROPERTY</span><h3>{ar?"ربط إعلانات واتساب بالمشروعات والوحدات":"Map WhatsApp ads to projects & units"}</h3></div><span>{referrals.length}</span></div>
      <form className="referralForm" onSubmit={createReferral}>
        <label>{ar?"Ad ID":"Ad ID"}<input name="ad_id" required placeholder="2385..."/></label>
        <label>{ar?"Campaign ID":"Campaign ID"}<input name="campaign_id"/></label>
        <label>{ar?"المشروع":"Project"}<select name="project_id" required defaultValue=""><option value="" disabled>{ar?"اختر المشروع":"Select project"}</option>{projects.map((p)=><option key={p.id} value={p.id}>{p.name+" · "+p.city}</option>)}</select></label>
        <label>{ar?"الوحدة (اختياري)":"Unit (optional)"}<select name="unit_id" defaultValue=""><option value="">{ar?"المشروع فقط":"Project only"}</option>{units.map((u)=><option key={u.id} value={u.id}>{u.code+" · "+u.unit_type}</option>)}</select></label>
        <label>{ar?"وصف الإعلان":"Label"}<input name="label"/></label>
        <label>{ar?"رابط مصدر الإعلان":"Source URL"}<input name="source_url" type="url"/></label>
        <button className="primaryButton"><Plus size={15}/>{ar?"حفظ الربط":"Save mapping"}</button>
      </form>
      {referrals.length>0&&<div className="referralList">{referrals.slice(0,8).map((r)=><article key={r.id}><strong>{r.label||r.ad_id}</strong><span>{r.project_name+(r.unit_code?" · "+r.unit_code:"")}</span><small>{r.ad_id+(r.campaign_id?" · "+r.campaign_id:"")}</small></article>)}</div>}
    </section>
  </div>;
}
