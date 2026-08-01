import { useState } from "react";
import { useCompare } from "@/hooks/useHospitals";
import ComparisonTable from "@/components/ComparisonTable";

export default function ComparePage() {
  // Scaffold: comma-separated ID entry. Swap for a proper multi-select
  // once /search results can be "added to comparison".
  const [idsInput, setIdsInput] = useState("");
  const ids = idsInput.split(",").map((s) => s.trim()).filter(Boolean);
  const { data: hospitals, isLoading, isError } = useCompare(ids);

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <h1 className="font-display text-2xl text-compass-950 mb-4">Compare hospitals</h1>
      <p className="text-compass-700 text-sm mb-4">
        Paste 2–5 hospital IDs (comma-separated) from the search page to compare them side by side.
      </p>
      <input
        value={idsInput}
        onChange={(e) => setIdsInput(e.target.value)}
        placeholder="id-1, id-2, id-3"
        className="border border-compass-300 rounded-lg px-4 py-2 w-full mb-6"
      />

      {ids.length >= 2 && isLoading && <p className="text-compass-700">Loading comparison…</p>}
      {isError && <p className="text-signal-600">Couldn't load one or more hospitals.</p>}
      {hospitals && hospitals.length > 0 && <ComparisonTable hospitals={hospitals} />}
    </div>
  );
}
