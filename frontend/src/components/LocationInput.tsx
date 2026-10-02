import { useEffect, useState } from "react";
export type Point = { lat: number; lon: number };

export default function LocationInput({ point, onChange }: { point?: Point; onChange: (point?: Point) => void }) {
  const [message, setMessage] = useState("");
  const [lat, setLat] = useState(point?.lat.toString()||"");
  const [lon, setLon] = useState(point?.lon.toString()||"");
  useEffect(()=>{setLat(point?.lat.toString()||'');setLon(point?.lon.toString()||'');},[point]);
  function locate() {
    if (!navigator.geolocation) { setMessage("Location is unavailable in this browser. Enter coordinates below."); return; }
    setMessage("Waiting for your browser's location permission…");
    navigator.geolocation.getCurrentPosition(({ coords }) => {
      onChange({ lat: coords.latitude, lon: coords.longitude }); setMessage("");
    }, () => setMessage("Location was unavailable or permission was declined. You can enter coordinates below."), { timeout: 15000 });
  }
  function applyCoordinates() {
    const a = Number(lat), b = Number(lon);
    if (!lat.trim() || !lon.trim() || !Number.isFinite(a) || !Number.isFinite(b) || Math.abs(a) > 90 || Math.abs(b) > 180) { setMessage("Enter a latitude from −90 to 90 and longitude from −180 to 180."); return; }
    onChange({ lat: a, lon: b }); setMessage("");
  }
  return <div className="surface-card space-y-3 p-5">
    <button type="button" onClick={locate} className="secondary-button w-full">Use my location</button>
    {point && <p className="text-sm text-compass-700">Location set. <button type="button" className="underline" onClick={() => onChange(undefined)}>Clear location</button></p>}
    <p className="text-xs text-slate-500">Remembered in this tab’s session until you clear or reset it. Distance is straight-line distance, not driving time.</p>
    <details><summary className="cursor-pointer text-sm text-compass-700">Enter coordinates instead</summary>
      <label className="mt-3 block text-sm">Latitude<input aria-label="Latitude" className="form-input mt-1" type="number" min="-90" max="90" step="any" value={lat} onChange={e => setLat(e.target.value)} /></label>
      <label className="mt-3 block text-sm">Longitude<input aria-label="Longitude" className="form-input mt-1" type="number" min="-180" max="180" step="any" value={lon} onChange={e => setLon(e.target.value)} /></label>
      <button type="button" onClick={applyCoordinates} className="secondary-button mt-3">Set location</button>
    </details>
    {message && <p role="status" className="text-sm text-amber-800">{message}</p>}
  </div>;
}
