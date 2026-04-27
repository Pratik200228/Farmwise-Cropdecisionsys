import { useState } from "react";
import { runMultiAgentSeasonPlan } from "../lib/multiAgentApi";
import { defaultFarmContext, type FarmContext } from "../types/farm";
import type { MultiAgentSeasonPlan, OrchestrationStep } from "../types/agents";
import { FarmContextForm } from "./FarmContextForm";
import { RichText } from "./RichText";

function StepTimeline({ steps }: { steps: OrchestrationStep[] }) {
  return (
    <ol className="agent-steps" aria-label="Agent execution order">
      {steps.map((s) => (
        <li
          key={s.kind}
          className={`agent-steps__item agent-steps__item--${s.status}`}
        >
          <span className="agent-steps__badge" aria-hidden>
            {s.status === "done"
              ? "✓"
              : s.status === "running"
                ? "…"
                : s.status === "error"
                  ? "!"
                  : "○"}
          </span>
          <div>
            <div className="agent-steps__label">{s.label}</div>
            {s.error ? (
              <div className="agent-steps__err">{s.error}</div>
            ) : null}
          </div>
        </li>
      ))}
    </ol>
  );
}

export function MultiAgentPlanPanel() {
  const [context, setContext] = useState<FarmContext>(defaultFarmContext());
  const [symptomsNote, setSymptomsNote] = useState("");
  const [running, setRunning] = useState(false);
  const [steps, setSteps] = useState<OrchestrationStep[]>([]);
  const [plan, setPlan] = useState<MultiAgentSeasonPlan | null>(null);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setError(null);
    setPlan(null);
    setRunning(true);
    setSteps([]);
    try {
      const result = await runMultiAgentSeasonPlan(
        context,
        setSteps,
        symptomsNote,
      );
      setPlan(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Orchestration failed");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="multi-agent">
      <header className="multi-agent__head">
        <h1 className="multi-agent__title">Season Intelligence Plan</h1>
        <p className="multi-agent__sub">
          Generates a comprehensive farm strategy by correlating
          <strong> environmental suitability</strong>, <strong>market trends</strong>, and <strong>health risks</strong> into a single cohesive season plan.
        </p>
      </header>

      <div className="multi-agent__grid">
        <div className="card multi-agent__context">
          <FarmContextForm value={context} onChange={setContext} />
          <label className="field">
            <span className="field__label">Symptoms note (optional, health agent)</span>
            <textarea
              className="field__input field__input--area"
              rows={2}
              placeholder="e.g. lower leaves yellowing, brown spots on tomato…"
              value={symptomsNote}
              onChange={(e) => setSymptomsNote(e.target.value)}
            />
          </label>
          <button
            type="button"
            className="btn btn--primary multi-agent__run"
            disabled={running}
            onClick={() => void run()}
          >
            {running ? "Running three agents…" : "Run full three-agent analysis"}
          </button>
          {error ? (
            <p className="multi-agent__error" role="alert">
              {error}
            </p>
          ) : null}
        </div>

        <div className="multi-agent__main">
          {(running || steps.length > 0) && (
            <div className="card multi-agent__timeline">
              <h2 className="multi-agent__h2">Orchestration</h2>
              <StepTimeline
                steps={
                  steps.length > 0
                    ? steps
                    : [
                        {
                          kind: "suitability",
                          label: "Calculate environmental suitability",
                          status: "idle",
                        },
                        {
                          kind: "market",
                          label: "Analyze market intelligence",
                          status: "idle",
                        },
                        {
                          kind: "health",
                          label: "Monitor crop health risks",
                          status: "idle",
                        },
                        {
                          kind: "planner",
                          label: "Generate integrated season plan (AI planner)",
                          status: "idle",
                        },
                      ]
                }
              />
            </div>
          )}

          {plan ? (
            <>
              <div className="card multi-agent__summary">
                <h2 className="multi-agent__h2">Integrated summary</h2>
                <RichText text={plan.integratedSummary} />
                <p className="multi-agent__focus">
                  Focus crop from suitability agent:{" "}
                  <strong>{plan.focusCrop}</strong>
                </p>
              </div>

              <div className="agent-cards">
                <section className="card agent-card agent-card--suit">
                  <h3 className="agent-card__title">Suitability Forecast</h3>
                  <RichText text={plan.suitability.environmentalSummary} />
                  <ul className="agent-card__list">
                    {plan.suitability.rankedCrops.map((c) => (
                      <li key={c.name}>
                        <strong>{c.name}</strong> — {c.score}/100 — {c.rationale}
                      </li>
                    ))}
                  </ul>
                </section>

                <section className="card agent-card agent-card--market">
                  <h3 className="agent-card__title">Market Forecast</h3>
                  <RichText text={plan.market.outlook} />
                  <p className="agent-card__muted">{plan.market.riskNotes}</p>
                  <ul className="agent-card__list">
                    {plan.market.suggestedWindows.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </section>

                <section className="card agent-card agent-card--health">
                  <h3 className="agent-card__title">Health Monitoring</h3>
                  <ul className="agent-card__list agent-card__list--rich">
                    {plan.health.scoutingPlan.map((w, i) => (
                      <li key={i}>
                        <div className="rich-in-li">
                          <RichText text={w} />
                        </div>
                      </li>
                    ))}
                  </ul>
                  <p className="agent-card__risks">
                    <strong>Priority risks:</strong>{" "}
                    {plan.health.priorityRisks.join("; ")}
                  </p>
                  <p className="agent-card__muted">{plan.health.whenToEscalate}</p>
                </section>
              </div>
            </>
          ) : null}
        </div>
      </div>

    </div>
  );
}
