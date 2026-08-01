import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";

const LandingPage = lazy(() => import("./pages/LandingPage"));
const SearchPage = lazy(() => import("./pages/SearchPage"));
const HospitalDetailsPage = lazy(() => import("./pages/HospitalDetailsPage"));
const ComparePage = lazy(() => import("./pages/ComparePage"));
const AIAssistantPage = lazy(() => import("./pages/AIAssistantPage"));
const RankingsPage = lazy(() => import("./pages/RankingsPage"));
const AnalyticsPage = lazy(() => import("./pages/AnalyticsPage"));
const AdminPage = lazy(() => import("./pages/AdminPage"));

function AppLoader() {
  return (
    <div className="grid min-h-[50vh] place-items-center bg-slate-50">
      <div className="text-center">
        <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-compass-100 border-t-compass-700" />
        <p className="mt-4 text-sm font-medium text-slate-600">Loading CareCompass…</p>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">
        <Suspense fallback={<AppLoader />}>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/hospital/:id" element={<HospitalDetailsPage />} />
            <Route path="/compare" element={<ComparePage />} />
            <Route path="/assistant" element={<AIAssistantPage />} />
            <Route path="/rankings" element={<RankingsPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </Suspense>
      </main>
      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-2 px-5 py-6 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between lg:px-8">
          <span>© 2026 CareCompass</span>
          <span>Hospital information is educational and not medical advice.</span>
        </div>
      </footer>
    </div>
  );
}
