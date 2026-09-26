import { FormEvent, useEffect, useState } from "react";
import { CheckCircle2, KeyRound, MessageSquare, Phone, Plus, RefreshCw, ShieldCheck } from "lucide-react";

type Locale = "ar" | "en";
const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? "http://localhost:8000" : window.location.origin);

type Channel = {
  id: string;
  display_name: string;
  phone_number_id: string;
  waba_id?: string | null;
  business_phone?: string | null;
  graph_api_version: string;
  status: string;
  is_default: boolean;
  configured_secret_keys: string[];
  created_at: string;
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

export default function WhatsAppOps({ token, locale }: { token: string; locale: Locale }) {
  const ar = locale === "ar";
  const [channels, setChannels] = useState<Channel[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    setBusy(true);
    try {
      setChannels(await api<Channel[]>("/api/v1/whatsapp/channels", token));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    } finally { setBusy(false); }
  }

  useEffect(() => { void load(); }, [token]);

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setError(""); setNotice("");
    try {
      await api("/api/v1/whatsapp/channels", token, {
        method: "POST",
        body: JSON.stringify({
          display_name: String(data.get("display_name") || ""),
          phone_number_id: String(data.get("phone_number_id") || ""),
          waba_id: String(data.get("waba_id") || "") || null,
          business_phone: String(data.get("business_phone") || "") || null,
          graph_api_version: String(data.get("graph_api_version") || "v23.0"),
          access_token: String(data.get("access_token") || "") || null,
          app_secret: String(data.get("app_secret") || "") || null,
          is_default: data.get("is_default") === "on",
          enabled: data.get("enabled") === "on",
        }),
      });
      form.reset();
      setNotice(ar ? "تم حفظ قناة WhatsApp ومفاتيحها بصورة مشفرة." : "WhatsApp channel and encrypted credentials saved.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    }
  }

  async function readiness(channel: Channel) {
    setError(""); setNotice("");
    try {
      const result = await api<{ ready: boolean; checks: Record<string, boolean> }>(`/api/v1/whatsapp/channels/${channel.id}/readiness`, token);
      setNotice(result.ready
        ? (ar ? `${channel.display_name}: القناة جاهزة للاستخدام من ناحية الإعدادات.` : `${channel.display_name}: configuration is ready.`)
        : (ar ? `${channel.display_name}: توجد إعدادات ناقصة — ${Object.entries(result.checks).filter(([,ok])=>!ok).map(([key])=>key).join("، ")}` : `${channel.display_name}: missing ${Object.entries(result.checks).filter(([,ok])=>!ok).map(([key])=>key).join(", ")}`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Readiness check failed");
    }
  }

  return <div className="opsPage whatsappOps">
    <div className="opsHeading">
      <div><span className="eyebrow">WHATSAPP TENANT CHANNELS</span><h2>{ar ? "قنوات WhatsApp الخاصة بالشركة" : "Company WhatsApp channels"}</h2></div>
      <button className="iconButton" onClick={() => void load()} disabled={busy}><RefreshCw size={17} className={busy ? "spin" : ""}/></button>
    </div>
    {error && <div className="systemError">{error}</div>}
    {notice && <div className="successNotice">{notice}</div>}

    <div className="whatsappGrid">
      <form className="panel opsForm whatsappForm" onSubmit={create}>
        <div className="opsTitle"><MessageSquare size={19}/><strong>{ar ? "إضافة قناة" : "Add channel"}</strong></div>
        <label>{ar ? "الاسم الظاهر" : "Display name"}<input name="display_name" required placeholder="Sales WhatsApp"/></label>
        <div className="formGrid">
          <label>Phone Number ID<input name="phone_number_id" required/></label>
          <label>WABA ID<input name="waba_id"/></label>
          <label>{ar ? "رقم النشاط" : "Business phone"}<input name="business_phone" placeholder="+20..."/></label>
          <label>Graph API<select name="graph_api_version" defaultValue="v23.0"><option value="v23.0">v23.0</option><option value="v22.0">v22.0</option><option value="v21.0">v21.0</option></select></label>
        </div>
        <div className="secretBox">
          <KeyRound size={17}/>
          <div><strong>{ar ? "بيانات سرية مشفرة" : "Encrypted credentials"}</strong><span>{ar ? "بعد الحفظ لا تعيد الواجهة عرض قيمة التوكن أو App Secret." : "Token and App Secret values are never echoed back after saving."}</span></div>
        </div>
        <label>Access Token<input name="access_token" type="password" autoComplete="off"/></label>
        <label>App Secret<input name="app_secret" type="password" autoComplete="off"/></label>
        <div className="templateFlags">
          <label className="checkLabel"><input name="enabled" type="checkbox" defaultChecked/><span>{ar ? "تفعيل القناة" : "Enable channel"}</span></label>
          <label className="checkLabel"><input name="is_default" type="checkbox"/><span>{ar ? "القناة الافتراضية" : "Default channel"}</span></label>
        </div>
        <button className="primaryButton"><Plus size={16}/>{ar ? "حفظ القناة" : "Save channel"}</button>
      </form>

      <section className="panel whatsappList">
        <div className="panelHead"><h2>{ar ? "القنوات المحفوظة" : "Configured channels"}</h2><span>{channels.length}</span></div>
        {channels.map(channel => <article className="whatsappChannelCard" key={channel.id}>
          <div className="channelIcon"><Phone size={19}/></div>
          <div className="channelMain"><strong>{channel.display_name}</strong><span>{channel.business_phone || channel.phone_number_id} · {channel.graph_api_version}</span><small>{channel.configured_secret_keys.length ? channel.configured_secret_keys.join(" · ") : (ar ? "لا توجد مفاتيح سرية" : "No secret keys")}</small></div>
          <span className={`statusBadge status-${channel.status}`}>{channel.status}</span>
          {channel.is_default && <span className="defaultBadge">{ar ? "افتراضية" : "Default"}</span>}
          <button className="secondaryButton" onClick={() => void readiness(channel)}><ShieldCheck size={15}/>{ar ? "فحص الجاهزية" : "Readiness"}</button>
        </article>)}
        {!channels.length && <div className="seoEmpty"><MessageSquare size={27}/><p>{ar ? "لم تتم إضافة قناة WhatsApp لهذه الشركة بعد." : "No WhatsApp channel has been added for this company."}</p></div>}
        <div className="channelPolicyNote"><CheckCircle2 size={16}/><span>{ar ? "هذه الشاشة تدير الإعدادات والاعتمادات لكل شركة. إرسال الرسائل الفعلي يظل خاضعًا لقواعد WhatsApp والقوالب المسموح بها." : "This screen manages per-tenant configuration and credentials. Actual delivery remains subject to WhatsApp messaging/template rules."}</span></div>
      </section>
    </div>
  </div>;
}
