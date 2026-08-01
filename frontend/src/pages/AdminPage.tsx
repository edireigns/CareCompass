export default function AdminPage() {
  // Scaffold placeholder for the "Admin Data Refresh" page described in
  // the spec. In the full build this triggers the ETL pipeline
  // (backend/scripts/seed.py today; a scheduled CMS/CDC fetch later)
  // and shows dataset_metadata freshness per source.
  return (
    <div className="max-w-3xl mx-auto px-6 py-10">
      <h1 className="font-display text-2xl text-compass-950 mb-4">Data refresh</h1>
      <div className="bg-white rounded-xl border border-compass-100 p-5 text-sm text-compass-700 space-y-3">
        <p>This page will show, per data source (CMS Care Compare, CMS Hospital General Information, CDC datasets):</p>
        <ul className="list-disc list-inside space-y-1">
          <li>Last successful fetch time</li>
          <li>Row counts ingested</li>
          <li>Success / failure status</li>
          <li>A manual "Refresh now" trigger</li>
        </ul>
        <p>Backed by the <code className="bg-compass-100 px-1 rounded">dataset_metadata</code> table already defined in the schema.</p>
      </div>
    </div>
  );
}
