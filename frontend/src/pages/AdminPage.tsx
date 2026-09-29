import CoveragePanel from "@/components/CoveragePanel";
import ReviewQueue from "@/components/ReviewQueue";
import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { apiClient } from "@/api/client";

type Source = { refresh_due: boolean; key: string; title: string; status: string; rows: number; last_success?: string; message?: string; source_url: string; file_present: boolean };
type Backup = {name:string;created_at:string;reason:string;location?:string;verification?:string};
type Status = { backups: Backup[]; sources: Source[]; counts: Record<string, number>; running: boolean; job?: { id: string; status: string; message?: string } };
type Entry = { facility_id: string; kind: string; name: string; source_url: string; source_label: string; verified_on: string; expires_on?: string | null };
const columns = ["facility_id", "kind", "name", "source_url", "source_label", "verified_on", "expires_on"];
const adminHeaders = { "X-CareCompass-Admin": "1" };
function errorText(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map(d => `${d.loc?.join(".")}: ${d.msg}`).join("; ");
  }
  return "The request failed. Please check the file and try again.";
}
function parseCSV(text: string): Entry[] {
  const rows: string[][] = []; let row: string[] = []; let cell = ""; let quoted = false;
  text = text.replace(/^\uFEFF/, "");
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (c === '"') { if (quoted && text[i + 1] === '"') { cell += '"'; i++; } else quoted = !quoted; }
    else if (c === "," && !quoted) { row.push(cell); cell = ""; }
    else if ((c === "\n" || c === "\r") && !quoted) { if (c === "\r" && text[i + 1] === "\n") i++; row.push(cell); if (row.some(s => s.trim())) rows.push(row); row = []; cell = ""; }
    else cell += c;
  }
  if (quoted) throw new Error("CSV has an unclosed quoted value.");
  row.push(cell); if (row.some(s => s.trim())) rows.push(row);
  const header = rows.shift()?.map(s => s.trim()) || [];
  if (new Set(header).size !== header.length || columns.slice(0, 6).some(c => !header.includes(c))) throw new Error("Use the template column names, including source and verification date.");
  if (!rows.length || rows.length > 5000) throw new Error("Choose a file with 1–5,000 records.");
  return rows.map((values, i) => {
    if (values.length !== header.length) throw new Error(`Row ${i + 2} has the wrong number of columns.`);
    const entry = Object.fromEntries(header.map((key, j) => [key, values[j].trim()])) as Entry;
    if (!entry.expires_on) entry.expires_on = null;
    return entry;
  });
}
export default function AdminPage() {
  const cache = useQueryClient();
  const [latest, setLatest] = useState(false); const [geocode, setGeocode] = useState(false);
  const [records, setRecords] = useState<Entry[]>([]); const [fileError, setFileError] = useState("");
  const [destination, setDestination] = useState("");
  const lastCompletedJob = useRef<string | null>(null);
  const { data, isLoading, isError } = useQuery({ queryKey: ["data-status"], queryFn: async () => (await apiClient.get<Status>("/data/status")).data, refetchInterval: 2500 });
  useEffect(() => {
    const job=data?.job;
    if (!job || job.status === "running" || lastCompletedJob.current === job.id) return;
    lastCompletedJob.current=job.id;
    for (const key of ["hospitals", "hospital", "rankings", "nearby", "compare", "specialties", "insurance", "insurance-categories"])
      cache.invalidateQueries({queryKey:[key]});
  }, [data?.job?.id, data?.job?.status, cache]);
  const mirror = useQuery({ queryKey: ["backup-destination"], queryFn: async () => (await apiClient.get<{destination:string|null;enabled:boolean;available:boolean}>("/data/backup-destination",{headers:adminHeaders})).data });
  const saveDestination = useMutation({ mutationFn: async (path:string|null) => (await apiClient.post("/data/backup-destination",{destination:path},{headers:adminHeaders})).data, onSuccess: () => cache.invalidateQueries() });
  const verify = useMutation({ mutationFn: async (name:string) => (await apiClient.post<{table_counts:Record<string,number>}>(`/data/backup/${encodeURIComponent(name)}/verify`,{},{headers:adminHeaders})).data, onSuccess: () => cache.invalidateQueries() });
  const backup = useMutation({ mutationFn: async () => (await apiClient.post<{name:string}>("/data/backup", {}, {headers:adminHeaders})).data, onSuccess: () => cache.invalidateQueries() });
  const refresh = useMutation({ mutationFn: async () => (await apiClient.post("/data/refresh", { download_latest: latest, geocode_missing: geocode }, { headers: adminHeaders })).data, onSuccess: () => cache.invalidateQueries() });
  const upload = useMutation({ mutationFn: async () => (await apiClient.post<{ imported: number }>("/data/directory", { records }, { headers: adminHeaders })).data, onSuccess: () => { setRecords([]); cache.invalidateQueries(); } });
  async function selectFile(file?: File) {
    setFileError(""); setRecords([]); upload.reset();
    if (!file) return;
    if (file.size > 3_000_000) { setFileError("The file must be smaller than 3 MB."); return; }
    try { setRecords(parseCSV(await file.text())); } catch (e) { setFileError(e instanceof Error ? e.message : "Could not read this CSV."); }
  }
  const running = !!data?.running || refresh.isPending || backup.isPending;
  return <div className="mx-auto max-w-6xl space-y-8 px-6 py-10">
    <header><p className="section-kicker">Data management</p><h1 className="mt-2 font-display text-3xl text-compass-950">Keep your hospital data up to date.</h1><p className="mt-3 text-slate-600">Refresh public datasets, see source coverage, and import verified directory records. Data-changing actions are limited to this computer.</p></header>
    <CoveragePanel />
    <ReviewQueue />
    {isLoading && <p>Loading source status…</p>}{isError && <p role="alert" className="text-rose-700">Data status could not be loaded. Check that the updated backend is running.</p>}
    {data && <div className="grid grid-cols-2 gap-4 md:grid-cols-4">{[["Hospitals", data.counts.hospitals], ["Matched coordinates", data.counts.coordinates], ["Detailed measures", data.counts.measures], ["Hospitals with verified plans", data.counts.insurance_hospitals]].map(([label, value]) => <div key={label} className="rounded-2xl border border-slate-200 bg-white p-5"><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-3xl font-semibold text-compass-950">{Number(value || 0).toLocaleString()}</p></div>)}</div>}
    <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6">
      <h2 className="font-display text-2xl text-compass-950">Database backups</h2>
      <p className="text-sm text-slate-600">A checksum-checked database archive is saved before every refresh, directory import, and restore. If backup fails, the data change stops. Choose a folder on another drive to copy every new backup there. When enabled, a failed second copy also stops data changes.</p>
      <p className="text-sm">Other-drive copy: <strong>{mirror.data?.enabled ? (mirror.data.available ? "enabled and available" : "enabled but drive unavailable") : "not configured"}</strong>{mirror.data?.destination && ` · ${mirror.data.destination}`}</p>
      <form className="flex flex-wrap gap-2 text-sm" onSubmit={e => {e.preventDefault();saveDestination.mutate(destination.trim() || null);}}><input aria-label="Other-drive backup folder" className="min-w-72 flex-1 rounded border p-2" placeholder="E:\\CareCompassBackups" value={destination} onChange={e => setDestination(e.target.value)} /><button className="primary-button" type="submit" disabled={saveDestination.isPending}>Save destination</button>{mirror.data?.enabled && <button type="button" className="rounded border px-3" disabled={saveDestination.isPending} onClick={() => saveDestination.mutate(null)}>Disable copy</button>}</form>
      <p className="text-xs text-slate-500">The folder must already exist on another drive or network share. Leave this unset until your drive is ready.</p>
      {saveDestination.isError && <p role="alert" className="text-rose-700">{errorText(saveDestination.error)}</p>}
      <button className="primary-button disabled:opacity-50" disabled={running || !data} onClick={() => backup.mutate()}>{backup.isPending ? "Saving backup…" : "Back up now"}</button>
      {backup.isError && <p role="alert" className="text-rose-700">{errorText(backup.error)}</p>}
      {backup.isSuccess && <p role="status" className="text-compass-700">Saved {backup.data.name}</p>}
      <p className="text-sm text-slate-600">Use Verify restore to restore an archive into a disposable database schema and compare table counts without replacing live data. To actually restore: stop the servers, open CareCompass.cmd, and choose Restore; it requires you to type RESTORE.</p>
      {verify.isError && <p role="alert" className="text-rose-700">{errorText(verify.error)}</p>}{verify.isSuccess && <p role="status" className="text-compass-700">Restore verification passed: {verify.data.table_counts.hospitals.toLocaleString()} hospitals.</p>}
      <ul className="space-y-2 text-xs text-slate-600">{data?.backups?.slice(0,10).map(b => <li className="flex flex-wrap items-center gap-2" key={b.name}><span>{new Date(b.created_at).toLocaleString()} · {b.reason} · {b.location || "local"} · {b.verification || "not restore-tested"} · {b.name}</span><button className="text-compass-700 underline" disabled={verify.isPending || running} onClick={() => verify.mutate(b.name)}>Verify restore</button></li>)}</ul>
    </section>
    <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6">
      <h2 className="font-display text-2xl text-compass-950">Refresh source data</h2>
      <p className="text-sm text-slate-600">By default, import the CSV files already saved with the app. Existing hospital IDs are preserved. Each source is imported in its own transaction; failures retain its previous records.</p>
      <label className="flex gap-3 text-sm"><input type="checkbox" checked={latest} disabled={running} onChange={e => setLatest(e.target.checked)} />Download the latest CMS releases before importing (requires internet)</label>
      <label className="flex gap-3 text-sm"><input type="checkbox" checked={geocode} disabled={running} onChange={e => setGeocode(e.target.checked)} />Retry unmatched hospital addresses with the U.S. Census geocoder (may take several minutes)</label>
      <button className="primary-button disabled:opacity-50" disabled={running || !data} onClick={() => refresh.mutate()}>{running ? "Data operation in progress…" : "Refresh now"}</button>
      {refresh.isError && <p role="alert" className="text-rose-700">{errorText(refresh.error)}</p>}
      {data?.job && <p role="status" className={data.job.status.includes("fail") ? "text-amber-800" : "text-compass-700"}>{data.job.message || data.job.status}</p>}
      <p className="text-xs text-slate-500">Some Census addresses cannot be matched. They remain unknown and are excluded from nearby search. “Last imported” is distinct from each measure’s historical reporting period.</p>
    </section>
    <div className="overflow-x-auto rounded-2xl border border-slate-200"><table className="min-w-full bg-white text-left text-sm"><thead className="bg-slate-100"><tr>{["Source", "Status", "Imported records", "Last imported"].map(h => <th key={h} className="p-4">{h}</th>)}</tr></thead><tbody>{data?.sources.map(s => <tr key={s.key} className="border-t border-slate-100"><td className="p-4"><a className="font-medium text-compass-700 underline" href={s.source_url} target="_blank" rel="noreferrer">{s.title}</a><p className="mt-1 max-w-md text-xs text-slate-500">{s.message || (s.file_present ? "Ready to import" : "Source file missing")}</p></td><td className="p-4">{s.status.replace(/_/g, " ")}{s.refresh_due && <p className="text-amber-800">Refresh recommended (180-day policy)</p>}</td><td className="p-4">{s.rows.toLocaleString()}</td><td className="p-4">{s.last_success ? new Date(s.last_success).toLocaleString() : "Not imported"}</td></tr>)}</tbody></table></div>
    <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6">
      <h2 className="font-display text-2xl text-compass-950">Import verified insurance or specialties</h2>
      <p className="text-sm text-slate-600">Use the hospital’s CMS facility ID, an exact insurance plan or specialty name, a supporting source URL, and the date you verified it. Importing a record means you have checked that source. Unknown coverage stays unknown; expired records are not shown as currently accepted.</p>
      <a className="inline-block text-sm text-compass-700 underline" download="carecompass-directory-template.csv" href={`data:text/csv;charset=utf-8,${encodeURIComponent(columns.join(",") + "\r\n")}`}>Download CSV template</a>
      <p className="text-xs text-slate-500">kind: insurance or specialty. Dates: YYYY-MM-DD. expires_on is optional. Up to 5,000 records; keep leading zeros in facility IDs.</p>
      <input className="block max-w-full text-sm" aria-label="Verified directory CSV" type="file" accept=".csv,text/csv" onChange={e => selectFile(e.target.files?.[0])} />
      {fileError && <p role="alert" className="text-rose-700">{fileError}</p>}
      {!!records.length && <div className="rounded-xl bg-slate-50 p-4"><p className="font-medium">{records.length} records ready for validation</p><ul className="mt-2 text-sm">{records.slice(0,5).map((r,i) => <li key={i}>{r.facility_id} · {r.kind} · {r.name} · {r.verified_on}</li>)}</ul></div>}
      <button className="primary-button disabled:opacity-50" disabled={!records.length || upload.isPending || running} onClick={() => upload.mutate()}>{upload.isPending ? "Importing…" : "Import verified records"}</button>
      {upload.isError && <p role="alert" className="text-rose-700">{errorText(upload.error)}</p>}
      {upload.isSuccess && <p role="status" className="text-compass-700">Imported {upload.data.imported} verified records.</p>}
    </section>
  </div>;
}
