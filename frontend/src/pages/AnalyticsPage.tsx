import { useRankings } from "@/hooks/useHospitals";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export default function AnalyticsPage() {
  const { data: hospitals, isLoading } = useRankings(10);

  const chartData = (hospitals ?? []).map((h) => ({
    name: h.name.length > 18 ? h.name.slice(0, 18) + "…" : h.name,
    score: h.overall_score ?? 0,
  }));

  return (
    <div className="page-shell max-w-6xl">
      <p className="section-kicker">At a glance</p><h1 className="page-title mb-8 mt-2">Hospital insights.</h1>
      <div className="surface-card p-5 sm:p-7">
        <h2 className="text-sm font-semibold text-compass-950 mb-4">Overall score by hospital</h2>
        {isLoading ? (
          <p className="text-compass-700">Loading…</p>
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={chartData}>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-20} textAnchor="end" height={60} />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Bar dataKey="score" fill="#2d8a85" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
      <p className="text-xs text-compass-700 mt-3">
        More trend graphs (readmission over time, regional comparisons) plug in here once
        the ETL pipeline is loading historical CMS snapshots.
      </p>
    </div>
  );
}
