import { FormEvent, useState } from "react";

import HospitalCard from "@/components/HospitalCard";
import { useRecommend } from "@/hooks/useHospitals";


export default function AIAssistantPage() {
  const [question, setQuestion] = useState("");
  const [city, setCity] = useState("");
  const [state, setState] = useState("");
  const [zipCode, setZipCode] = useState("");

  const {
    mutate,
    data,
    isPending,
    isError,
  } = useRecommend();

  const stateIsValid = state.length === 0 || state.length === 2;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();

    if (!question.trim() || !stateIsValid) {
      return;
    }

    mutate({
      question: question.trim(),
      city: city.trim() || undefined,
      state: state.trim().toUpperCase() || undefined,
      zip_code: zipCode.trim() || undefined,
    });
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <h1 className="font-display text-2xl text-compass-950">
        Ask CareCompass
      </h1>

      <p className="mb-6 mt-2 text-sm text-compass-700">
        Ask questions about hospitals and receive explanations grounded in
        public CMS quality data.
      </p>

      <form
        onSubmit={handleSubmit}
        className="mb-8 space-y-5 rounded-2xl border border-slate-200 bg-white p-6 shadow-card"
      >
        <div>
          <label
            htmlFor="ai-question"
            className="block text-sm font-semibold text-slate-700"
          >
            Your question
          </label>

          <textarea
            id="ai-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Which hospital has the strongest overall quality?"
            rows={4}
            maxLength={1000}
            required
            className="form-input mt-2 resize-y"
          />
        </div>

        <div>
          <p className="text-sm font-semibold text-slate-700">
            Location filters
          </p>

          <p className="mt-1 text-xs text-slate-500">
            Optional. Add a location to receive recommendations from that
            area instead of nationwide results.
          </p>

          <div className="mt-3 grid gap-4 sm:grid-cols-[1fr_100px_140px]">
            <label className="block text-sm text-slate-700">
              City
              <input
                value={city}
                onChange={(event) => setCity(event.target.value)}
                placeholder="Seattle"
                className="form-input mt-2"
              />
            </label>

            <label className="block text-sm text-slate-700">
              State
              <input
                value={state}
                onChange={(event) =>
                  setState(
                    event.target.value
                      .replace(/[^a-zA-Z]/g, "")
                      .slice(0, 2)
                      .toUpperCase(),
                  )
                }
                placeholder="WA"
                maxLength={2}
                className="form-input mt-2 uppercase"
              />
            </label>

            <label className="block text-sm text-slate-700">
              ZIP code
              <input
                value={zipCode}
                onChange={(event) =>
                  setZipCode(
                    event.target.value
                      .replace(/\D/g, "")
                      .slice(0, 5),
                  )
                }
                placeholder="98101"
                inputMode="numeric"
                maxLength={5}
                className="form-input mt-2"
              />
            </label>
          </div>

          {!stateIsValid && (
            <p className="mt-2 text-sm text-rose-700">
              Enter a two-letter state code, such as WA.
            </p>
          )}
        </div>

        <button
          type="submit"
          disabled={
            isPending ||
            !question.trim() ||
            !stateIsValid
          }
          className="primary-button w-full disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isPending ? "Analyzing CMS data..." : "Ask CareCompass"}
        </button>
      </form>

      {isError && (
        <div className="mb-6 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
          The AI assistant could not complete the request. Please try again.
        </div>
      )}

      {data && (
        <div>
          <div className="rounded-xl border border-compass-100 bg-white p-5">
            <h2 className="font-display text-xl text-compass-950">
              CareCompass explanation
            </h2>

            <p className="mt-3 whitespace-pre-wrap text-compass-950">
              {data.answer}
            </p>
          </div>

          <p className="mb-6 mt-2 text-xs text-compass-700">
            {data.disclaimer}
          </p>

          <h2 className="mb-4 font-display text-xl text-compass-950">
            Supporting hospitals
          </h2>

          <div className="grid gap-4 md:grid-cols-2">
            {data.supporting_hospitals.map((hospital) => (
              <HospitalCard
                key={hospital.id}
                hospital={hospital}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}