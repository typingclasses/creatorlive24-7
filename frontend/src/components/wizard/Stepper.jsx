const steps = ["YouTube & Key", "Stream Source", "Go Live Studio"];

export const Stepper = ({ step, onChange }) => (
  <div className="flex justify-center">
    <div className="inline-flex gap-1 bg-white border border-slate-200 rounded-full p-1.5 shadow-sm overflow-x-auto max-w-full">
      {steps.map((s, i) => (
        <button key={s} onClick={() => onChange(i + 1)} data-testid={`wizard-step-${i + 1}-tab`}
          className={`px-4 sm:px-6 py-2 rounded-full text-xs sm:text-sm font-semibold whitespace-nowrap transition-colors ${step === i + 1 ? "bg-[#E50914] text-white" : "text-slate-600 hover:bg-slate-100 hover:text-[#0B132B]"}`}>
          {i + 1}. {s}
        </button>
      ))}
    </div>
  </div>
);
