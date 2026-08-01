import { useState } from "react";
import { useRecommend } from "@/hooks/useHospitals";
import HospitalCard from "@/components/HospitalCard";

export default function AIAssistantPage() {
  const [question, setQuestion] = useState("");
  const { mutate, data, isPending } = useRecommend();

  return (
    <div className="max-w-3xl mx-auto px-6 py-10">
      <h1 className="font-display text-2xl text-compass-950 mb-2">Ask CareCompass</h1>
      <p className="text-compass-700 text-sm mb-6">
        Ask things like "which ER should I visit near me?" or "best hospital for heart surgery outcomes."
        Answers are grounded in public quality and outcomes data — never invented.
      </p>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (question.trim()) mutate({ question });
        }}
        className="flex gap-3 mb-8"
      >
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Which hospital has the best heart surgery outcomes?"
          className="border border-compass-300 rounded-lg px-4 py-2 flex-1"
        />
        <button
          type="submit"
          disabled={isPending}
          className="bg-signal-500 hover:bg-signal-600 disabled:opacity-50 text-white px-5 py-2 rounded-lg font-medium"
        >
          {isPending ? "Thinking…" : "Ask"}
        </button>
      </form>

      {data && (
        <div>
          <p className="bg-white border border-compass-100 rounded-xl p-5 text-compass-950">{data.answer}</p>
          <p className="text-xs text-compass-700 mt-2 mb-6">{data.disclaimer}</p>
          <div className="grid gap-4 md:grid-cols-2">
            {data.supporting_hospitals.map((h) => (
              <HospitalCard key={h.id} hospital={h} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
