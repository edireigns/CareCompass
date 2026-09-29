import { Link } from 'react-router-dom';
import { usePreferences } from '@/context/Preferences';
export default function SessionPreferences() {
  const {preferences,reset}=usePreferences();
  return <div className="border-b border-slate-200 bg-slate-50 px-5 py-2 text-sm text-slate-600"><div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-5 gap-y-2">
    <span>Preferences saved for this tab’s session · {preferences.point?'Location set':'No location set'}</span>
    <Link to="/rankings" className="text-compass-700 underline">Adjust priorities</Link>
    <Link to="/compare" className="text-compass-700 underline">Compare ({preferences.compared.length}/5)</Link>
    <button className="text-compass-700 underline" onClick={reset}>Reset all preferences</button>
    {!Object.values(preferences.weights).some(w=>w>0) && <span role="alert" className="text-amber-800">Choose at least one priority above zero to show results.</span>}
  </div></div>;
}
