import { useSearchParams } from "react-router-dom";
import { Stepper } from "@/components/wizard/Stepper";
import StepKeys from "@/components/wizard/StepKeys";
import StepSource from "@/components/wizard/StepSource";
import StepStudio from "@/components/wizard/StepStudio";

export default function Setup() {
  const [params, setParams] = useSearchParams();
  const step = Math.min(3, Math.max(1, Number(params.get("step")) || 1));
  const go = (n) => setParams({ step: String(n) });
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10">
      <Stepper step={step} onChange={go} />
      <div className="mt-8 bg-white border border-slate-200 rounded-[1.75rem] shadow-[0_20px_60px_-30px_rgba(11,19,43,.3)] p-6 sm:p-10 rise" key={step}>
        {step === 1 && <StepKeys onNext={() => go(2)} />}
        {step === 2 && <StepSource onBack={() => go(1)} onNext={() => go(3)} />}
        {step === 3 && <StepStudio onBack={() => go(2)} />}
      </div>
    </div>
  );
}
