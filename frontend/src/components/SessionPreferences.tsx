import { Link } from 'react-router-dom';
import { usePreferences } from '@/context/Preferences';
export default function SessionPreferences() {
  const {preferences,reset}=usePreferences();
  return <div className="border-b border-[#dce6ed] bg-[#f2f7f9] px-5 py-2.5 text-xs text-[#57707e]"><div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-5 gap-y-2">
    <span className="font-semibold">Your session · {preferences.point?'Location set':'No location set'}</span>
    <Link to="/rankings" className="font-semibold text-compass-700 hover:underline">Adjust priorities</Link>
    <Link to="/compare" className="font-semibold text-compass-700 hover:underline">Compare ({preferences.compared.length}/5)</Link>
    <button className="font-semibold text-compass-700 hover:underline" onClick={reset}>Reset preferences</button>
    {!Object.values(preferences.weights).some(w=>w>0) && <span role="alert" className="text-amber-800">Choose at least one priority above zero to show results.</span>}
  </div></div>;
}
