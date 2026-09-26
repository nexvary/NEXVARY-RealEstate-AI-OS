import { FormEvent, useEffect, useMemo, useState } from "react";
import { CheckCircle2, KeyRound, MessageSquare, Phone, Plus, RefreshCw, Send, ShieldCheck, Webhook } from "lucide-react";

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

type WhatsAppMessage = {
  id: string;
  channel_id: string;
  direction: "inbound" | "outbound";
  external_message_id?: string | null;
  contact: string;
  message_type: string;
  status: string;
  content: Record<string, unknown>;
  error_text?: string | null;
  provider_timestamp?: string | null;
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
  const [messages, setMessages] = useState<WhatsAppMessage[]>([]);
  const [selectedChannel, setSelectedChannel] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [sending, setSending] = useState(false);

  const activeChannel = useMemo(
    () => channels.find((channel) => channel.id === selectedChannel) || channels.find((channel) => channel.is_default) || channels[0],
    [channels, selectedChannel],
  );

  async function load() {
    setBusy(true);
    try {
      const channelData = await api<Channel[]>("/api/v1/whatsapp/channels", token);
      setChannels(channelData);
      const preferred = selectedChannel || channelData.find((channel) => channel.is_default)?.id || channelData[0]?.id || "";
      if (preferred && preferred !== selectedChannel) setSelectedChannel(preferred);
      const suffix = preferred ? `?channel_id=${encodeURIComponent(preferred)}&limit=100` : "?limit=100";
      setMessages(await api<WhatsAppMessage[]>(`/api/v1/whatsapp/messages${suffix}`, token));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    } finally { setBusy(false); }
  }

  useEffect(() => { void load(); }, [token]);

  useEffect(() => {
    if (!selectedChannel) return;
    void api<WhatsAppMessage[]>(`/api/v1/whatsapp/messages?channel_id=${encodeURIComponent(selectedChannel)}&limit=100`, token)
      .then(setMessages)
      .catch((err) => setError(err instanceof Error ? err.message : "Message load failed"));
  }, [selectedChannel, token]);

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setError(""); setNotice("");
    try {
      const created = await api<Channel>("/api/v1/whatsapp/channels", token, {
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
      setSelectedChannel(created.id);
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
        ? (ar ? `${channel.display_name}: القناة جاهزة للإرسال الفعلي.` : `${channel.display_name}: configuration is ready for live sending.`)
        : (ar ? `${channel.display_name}: توجد إعدادات ناقصة — ${Object.entries(result.checks).filter(([,ok])=>!ok).map(([key])=>key).join("، ")}` : `${channel.display_name}: missing ${Object.entries(result.checks).filter(([,ok])=>!ok).map(([key])=>key).join(", ")}`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Readiness check failed");
    }
  }

  async function configureWebhook(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeChannel) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    setError(""); setNotice("");
    try {
      const result = await api<{ callback_path: string }>(`/api/v1/whatsapp/channels/${activeChannel.id}/webhook-config`, token, {
        method: "PUT",
        body: JSON.stringify({ verify_token: String(data.get("verify_token") || "") }),
      });
      form.reset();
      setNotice(ar
        ? `تم تجهيز Webhook. استخدم مسار Callback التالي في Meta: ${result.callback_path}`
        : `Webhook configured. Use this callback path in Meta: ${result.callback_path}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Webhook configuration failed");
    }
  }

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeChannel) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    const messageType = String(data.get("message_type") || "text");
    setSending(true); setError(""); setNotice("");
    try {
      const result = await api<WhatsAppMessage>(`/api/v1/whatsapp/channels/${activeChannel.id}/messages`, token, {
        method: "POST",
        body: JSON.stringify({
          to: String(data.get("to") || ""),
          message_type: messageType,
          text: messageType === "text" ? String(data.get("text") || "") : null,
          media_url: messageType !== "text" ? String(data.get("media_url") || "") : null,
          caption: messageType !== "text" ? String(data.get("caption") || "") || null : null,
        }),
      });
      setNotice(ar ? `تم قبول الرسالة للإرسال: ${result.external_message_id || result.id}` : `Message accepted: ${result.external_message_id || result.id}`);
      form.reset();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Message send failed");
    } finally { setSending(false); }
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
          <button className="secondaryButton" onClick={() => { setSelectedChannel(channel.id); void readiness(channel); }}><ShieldCheck size={15}/>{ar ? "فحص الجاهزية" : "Readiness"}</button>
        </article>)}
        {!channels.length && <div className="seoEmpty"><MessageSquare size={27}/><p>{ar ? "لم تتم إضافة قناة WhatsApp لهذه الشركة بعد." : "No WhatsApp channel has been added for this company."}</p></div>}
      </section>
    </div>

    {channels.length > 0 && <div className="commercialGrid">
      <form className="panel opsForm" onSubmit={configureWebhook}>
        <div className="opsTitle"><Webhook size={19}/><strong>{ar ? "Webhook الفعلي" : "Live webhook"}</strong></div>
        <label>{ar ? "القناة" : "Channel"}<select value={activeChannel?.id || ""} onChange={(event) => setSelectedChannel(event.target.value)}>{channels.map((channel) => <option key={channel.id} value={channel.id}>{channel.display_name}</option>)}</select></label>
        <label>Verify Token<input name="verify_token" type="password" required minLength={12} autoComplete="off"/></label>
        <button className="secondaryButton"><Webhook size={15}/>{ar ? "تجهيز Callback" : "Configure callback"}</button>
        <div className="channelPolicyNote"><ShieldCheck size={16}/><span>{ar ? "استقبال الأحداث يرفض أي طلب لا يحمل توقيع Meta الصحيح باستخدام App Secret المحفوظ." : "Inbound events reject requests that do not carry a valid Meta signature using the stored App Secret."}</span></div>
      </form>

      <form className="panel opsForm" onSubmit={sendMessage}>
        <div className="opsTitle"><Send size={19}/><strong>{ar ? "إرسال رسالة فعلية" : "Send live message"}</strong></div>
        <label>{ar ? "القناة" : "Channel"}<select value={activeChannel?.id || ""} onChange={(event) => setSelectedChannel(event.target.value)}>{channels.map((channel) => <option key={channel.id} value={channel.id}>{channel.display_name}</option>)}</select></label>
        <div className="formGrid">
          <label>{ar ? "رقم العميل بصيغة دولية" : "Recipient number"}<input name="to" required placeholder="2010..."/></label>
          <label>{ar ? "النوع" : "Type"}<select name="message_type" defaultValue="text"><option value="text">Text</option><option value="image">Image</option><option value="video">Video</option><option value="document">Document</option></select></label>
        </div>
        <label>{ar ? "النص" : "Text"}<textarea name="text" rows={3} placeholder={ar ? "اكتب الرسالة النصية هنا" : "Text message body"}/></label>
        <label>{ar ? "رابط الوسائط HTTPS للصورة/الفيديو/المستند" : "HTTPS media URL for image/video/document"}<input name="media_url" placeholder="https://..."/></label>
        <label>{ar ? "تعليق الوسائط" : "Media caption"}<input name="caption"/></label>
        <button className="primaryButton" disabled={sending || activeChannel?.status !== "ready"}><Send size={16}/>{sending ? (ar ? "جارٍ الإرسال..." : "Sending...") : (ar ? "إرسال عبر WhatsApp" : "Send via WhatsApp")}</button>
      </form>
    </div>}

    <section className="panel whatsappList">
      <div className="panelHead"><h2>{ar ? "سجل الرسائل الفعلي" : "Live message ledger"}</h2><span>{messages.length}</span></div>
      {messages.map((message) => <article className="whatsappChannelCard" key={message.id}>
        <div className="channelIcon"><MessageSquare size={18}/></div>
        <div className="channelMain"><strong>{message.direction === "inbound" ? (ar ? "واردة" : "Inbound") : (ar ? "صادرة" : "Outbound")} · {message.contact}</strong><span>{message.message_type} · {message.external_message_id || message.id}</span><small>{new Date(message.created_at).toLocaleString(ar ? "ar-EG" : "en-US")}{message.error_text ? ` · ${message.error_text}` : ""}</small></div>
        <span className={`statusBadge status-${message.status}`}>{message.status}</span>
      </article>)}
      {!messages.length && <div className="seoEmpty"><MessageSquare size={27}/><p>{ar ? "لا توجد رسائل مسجلة لهذه القناة بعد." : "No messages have been recorded for this channel yet."}</p></div>}
      <div className="channelPolicyNote"><CheckCircle2 size={16}/><span>{ar ? "الإرسال الفعلي يخضع لقواعد نافذة المحادثة وقوالب WhatsApp المعتمدة. النظام لا يتجاوز سياسات Meta." : "Live delivery remains subject to WhatsApp conversation-window and approved-template rules; the platform does not bypass Meta policy."}</span></div>
    </section>
  </div>;
}
