import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import axios from "axios";

const headers = { "X-CareCompass-Admin": "1" };
type Item = { issue_id: string; kind: "address" | "record" | "presence"; facility_id: string; hospital_name: string; detail: string; source_url: string; last_reviewed_at?: string | null; last_note?: string | null };
type Queue = { total: number; counts: Record<string, number>; items: Item[] };
type Event = { id: string; created_at: string; issue_type: string; action: string; note: string; source_url: string; old_value: string; new_value: string };
function message(error: unknown) { return axios.isAxiosError(error) ? String(error.response?.data?.detail || error.message) : String(error); }

export default function ReviewQueue() {
  const cache = useQueryClient();
  const [kind, setKind] = useState(""); const [search, setSearch] = useState(""); const [showReviewed, setShowReviewed] = useState(false); const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState<Item | null>(null); const [action, setAction] = useState("reviewed"); const [note, setNote] = useState(""); const [source, setSource] = useState("");
  const [latitude, setLatitude] = useState(""); const [longitude, setLongitude] = useState(""); const [newName, setNewName] = useState(""); const [expiresOn, setExpiresOn] = useState("");
  const [historyFor, setHistoryFor] = useState("");
  const queue = useQuery({ queryKey: ["review-queue", kind, search, showReviewed, offset], queryFn: async () => (await apiClient.get<Queue>("/data/review/queue", { headers, params: { kind: kind || undefined, search, show_reviewed: showReviewed, offset, limit: 20 } })).data });
  const history = useQuery({ queryKey: ["review-history", historyFor], enabled: !!historyFor, queryFn: async () => (await apiClient.get<Event[]>(`/data/review/history/${encodeURIComponent(historyFor)}`, { headers })).data });
  const save = useMutation({ mutationFn: async () => {
    if (!selected) throw new Error("Choose an item.");
    return (await apiClient.post("/data/review", { issue_id: selected.issue_id, action, note, source_url: source, latitude: latitude ? Number(latitude) : null, longitude: longitude ? Number(longitude) : null, new_name: newName || null, expires_on: expiresOn || null }, { headers })).data;
  }, onSuccess: () => { setSelected(null); setNote(""); cache.invalidateQueries(); } });
  function choose(item: Item) { setSelected(item); setAction("reviewed"); setSource(item.source_url); setNote(""); setLatitude(""); setLongitude(""); setNewName(""); setExpiresOn(""); save.reset(); }
  const actions = selected?.kind === "address" ? ["reviewed", "correct"] : selected?.kind === "record" ? ["reviewed", "confirm", "correct", "retire"] : ["reviewed"];
  return <section className="surface-card space-y-4 p-6">
    <h2 className="font-display text-2xl text-compass-950">Data review queue</h2>
    <p className="text-sm text-slate-600">Review unmatched locations, directory records due for rechecking, and hospitals absent from the latest complete CMS release. An absence alone does not mean a hospital closed. Each review keeps its source and correction history.</p>
    <p className="text-sm text-slate-600">Open items: {Object.entries(queue.data?.counts || {}).map(([key, value]) => `${key} ${value}`).join(" · ") || "loading…"}</p>
    <div className="flex flex-wrap gap-3 text-sm">
      <select aria-label="Review category" className="rounded border p-2" value={kind} onChange={e => { setKind(e.target.value); setOffset(0); }}><option value="">All categories</option><option value="address">Unmatched addresses</option><option value="record">Directory records</option><option value="presence">Absent from CMS</option></select>
      <input aria-label="Search review queue" className="rounded border p-2" placeholder="Hospital or facility ID" value={search} onChange={e => { setSearch(e.target.value); setOffset(0); }} />
      <label className="flex items-center gap-2"><input type="checkbox" checked={showReviewed} onChange={e => { setShowReviewed(e.target.checked); setOffset(0); }} />Include reviewed</label>
    </div>
    {queue.isError && <p role="alert" className="text-rose-700">{message(queue.error)}</p>}
    {queue.isLoading && <p>Loading review queue…</p>}
    <div className="space-y-3">{queue.data?.items.map(item => <article key={item.issue_id} className="rounded-xl border border-slate-200 p-4 text-sm"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="font-semibold text-compass-950">{item.hospital_name} <span className="font-normal text-slate-500">({item.facility_id})</span></p><p className="mt-1 text-slate-600">{item.detail}</p><a className="text-compass-700 underline" href={item.source_url} target="_blank" rel="noreferrer">Source</a>{item.last_reviewed_at && <p className="mt-1 text-xs text-slate-500">Last review: {new Date(item.last_reviewed_at).toLocaleString()} · {item.last_note}</p>}</div><div className="flex gap-2"><button className="text-compass-700 underline" onClick={() => choose(item)}>Review</button><button className="text-compass-700 underline" onClick={() => setHistoryFor(item.facility_id)}>History</button></div></div></article>)}</div>
    {queue.data && !queue.data.items.length && <p className="text-sm text-slate-600">No items match these filters.</p>}
    <div className="flex gap-3 text-sm"><button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 20))}>Previous</button><span>{queue.data ? `${offset + 1}–${Math.min(offset + 20, queue.data.total)} of ${queue.data.total}` : ""}</span><button disabled={!queue.data || offset + 20 >= queue.data.total} onClick={() => setOffset(offset + 20)}>Next</button></div>
    {selected && <form className="space-y-3 rounded-xl bg-slate-50 p-5 text-sm" onSubmit={e => { e.preventDefault(); save.mutate(); }}><h3 className="font-semibold">Review {selected.hospital_name}: {selected.kind}</h3>
      <label className="block">Action <select className="ml-2 rounded border p-2" value={action} onChange={e => setAction(e.target.value)}>{actions.map(value => <option key={value} value={value}>{value === "reviewed" ? "Mark reviewed" : value === "confirm" ? "Reconfirm record" : value === "retire" ? "Retire record" : "Correct"}</option>)}</select></label>
      {selected.kind === "address" && action === "correct" && <div className="flex gap-3"><label>Latitude <input required type="number" step="any" min="-90" max="90" className="ml-2 w-32 rounded border p-2" value={latitude} onChange={e => setLatitude(e.target.value)} /></label><label>Longitude <input required type="number" step="any" min="-180" max="180" className="ml-2 w-32 rounded border p-2" value={longitude} onChange={e => setLongitude(e.target.value)} /></label></div>}
      {selected.kind === "record" && action === "correct" && <label className="block">Exact replacement name <input required className="ml-2 rounded border p-2" value={newName} onChange={e => setNewName(e.target.value)} /></label>}
      {selected.kind === "record" && ["confirm", "correct"].includes(action) && <label className="block">Expiry (optional) <input type="date" className="ml-2 rounded border p-2" value={expiresOn} onChange={e => setExpiresOn(e.target.value)} /></label>}
      <label className="block">Evidence URL <input required type="url" className="mt-1 w-full rounded border p-2" value={source} onChange={e => setSource(e.target.value)} /></label>
      <label className="block">Review note <textarea required minLength={3} className="mt-1 w-full rounded border p-2" value={note} onChange={e => setNote(e.target.value)} /></label>
      <div className="flex gap-3"><button type="submit" disabled={save.isPending} className="primary-button">{save.isPending ? "Saving…" : "Save review"}</button><button type="button" onClick={() => setSelected(null)}>Cancel</button></div>{save.isError && <p role="alert" className="text-rose-700">{message(save.error)}</p>}
    </form>}
    {historyFor && <div className="rounded-xl bg-slate-50 p-5 text-sm"><div className="flex justify-between"><h3 className="font-semibold">Correction history · {historyFor}</h3><button onClick={() => setHistoryFor("")}>Close</button></div>{history.data?.map(event => <div className="mt-3 border-t pt-3" key={event.id}><p>{new Date(event.created_at).toLocaleString()} · {event.issue_type} · {event.action}</p><p>{event.note} · <a className="text-compass-700 underline" href={event.source_url} target="_blank" rel="noreferrer">Evidence</a></p><details><summary>Old and new values</summary><pre className="overflow-auto whitespace-pre-wrap text-xs">Before: {event.old_value}{"\n"}After: {event.new_value}</pre></details></div>)}{history.data && !history.data.length && <p>No reviews recorded yet.</p>}</div>}
  </section>;
}
