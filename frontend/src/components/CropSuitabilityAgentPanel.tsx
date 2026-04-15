import { useState } from "react";
import { runCropSuitabilityAgent } from "../lib/insightsApi";
import type { FarmContext } from "../types/farm";
import { defaultFarmContext } from "../types/farm";
import type { CropSuitability, SuitabilityReport } from "../types/insights";
import { AgentBadge } from "./AgentBadge";
import { EnvironmentForm } from "./EnvironmentForm";
import { FarmContextForm } from "./FarmContextForm";
import { RichText } from "./RichText";

function scoreBand(score: number): string {
  if (score >= 85) return "excellent";
  if (score >= 70) return "good";
  if (score >= 55) return "fair";
  return "poor";
}

function FitBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="fit-bar">
      <div className="fit-bar__label">
        <span>{label}</span>
        <span>{value}</span>
      </div>
      <div className="fit-bar__track" aria-hidden>
        <div
          className={`fit-bar__fill fit-bar__fill--${scoreBand(value)}`}
          style={{ width: `${Math.max(4, value)}%` }}
        />
      </div>
    </div>
  );
}

function CropCard({ crop, rank }: { crop: CropSuitability; rank: number }) {
  const band = scoreBand(crop.score);
  return (
    <article className={`crop-card crop-card--${band}`}>
      <header className="crop-card__head">
        <div className="crop-card__rank" aria-hidden>
          #{rank}
        </div>
        <div className="crop-card__title-group">
          <h3 className="crop-card__title">{crop.name}</h3>
          <div className="crop-card__meta">
            <span className={`crop-card__badge crop-card__badge--${band}`}>
              {crop.score}/100 · {band}
            </span>
            <span className="crop-card__confidence">
              Confidence {Math.round(crop.confidence * 100)}%
            </span>
          </div>
        </div>
      </header>

      <div className="crop-card__fits">
        <FitBar label="Temperature" value={crop.fit.temperature} />
        <FitBar label="Humidity" value={crop.fit.humidity} />
        <FitBar label="Rainfall" value={crop.fit.rainfall} />
        <FitBar label="Soil" value={crop.fit.soil} />
        <FitBar label="Wind" value={crop.fit.wind} />
      </div>

      <p className="crop-card__rationale">{crop.rationale}</p>

      <div className="crop-card__foot">
        <div className="crop-card__window">
          <span className="crop-card__foot-label">Planting window</span>
          <span>{crop.plantingWindow}</span>
        </div>
        {crop.warnings.length > 0 ? (
          <ul className="crop-card__warnings">
            {crop.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        ) : null}
      </div>
    </article>
  );
}

export function CropSuitabilityAgentPanel() {
  const [context, setContext] = useState<FarmContext>(defaultFarmContext());
  const [report, setReport] = useState<SuitabilityReport | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setRunning(true);
    setError(null);
    try {
      const result = await runCropSuitabilityAgent(context);
      setReport(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Agent failed");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="suit-page">
      <header className="page-head">
        <div>
          <div className="page-head__kicker">Agent 1 of 3 · AI agent</div>
          <h1 className="page-head__title">Crop Suitability Agent</h1>
          <p className="page-head__sub">
            Goal-based agent — ranks crops by how well they fit the current
            weather, soil and season. Tune the inputs on the right and re-run
            any time.
          </p>
          <AgentBadge
            accent="suit"
            name="Agent 1 · Crop Suitability"
            type="goal-based"
            role="Maximizes expected yield by matching crop requirements to environmental inputs."
          />
        </div>
        <button
          type="button"
          className="btn btn--primary page-head__cta"
          onClick={() => void run()}
          disabled={running}
        >
          {running ? "Running agent…" : report ? "Re-run agent" : "Run agent"}
        </button>
      </header>

      <div className="suit-layout">
        <div className="suit-layout__main">
          {error ? <p className="panel-error">{error}</p> : null}

          {!report && !running ? (
            <div className="card suit-empty">
              <div className="suit-empty__icon" aria-hidden>
                🌱
              </div>
              <h2>Ready when you are</h2>
              <p>
                The agent scores 8 reference crops (maize, rice, wheat, lentil,
                tomato, potato, mustard, soybean) against your environmental
                inputs and returns the best fits with a rationale, planting
                window, and warnings.
              </p>
              <button
                type="button"
                className="btn btn--primary"
                onClick={() => void run()}
              >
                Run suitability agent
              </button>
            </div>
          ) : null}

          {running ? (
            <div className="card suit-running" aria-busy>
              <div className="suit-running__spinner" aria-hidden />
              <div>
                <strong>Agent is thinking…</strong>
                <p>Matching environmental profile against crop comfort bands.</p>
              </div>
            </div>
          ) : null}

          {report ? (
            <>
              <section className="card suit-summary">
                <h2 className="suit-summary__title">Agent summary</h2>
                <RichText text={report.summary} />
                <p className="suit-summary__rotation">
                  <strong>Rotation tip:</strong> {report.rotationSuggestion}
                </p>
              </section>

              <section className="crop-grid" aria-label="Ranked crops">
                {report.crops.map((c, i) => (
                  <CropCard key={c.name} crop={c} rank={i + 1} />
                ))}
              </section>
            </>
          ) : null}
        </div>

        <aside className="suit-layout__side">
          <div className="card">
            <EnvironmentForm
              value={context.env}
              onChange={(env) => setContext({ ...context, env })}
            />
          </div>
          <div className="card farm-context-card">
            <FarmContextForm value={context} onChange={setContext} />
          </div>
        </aside>
      </div>
    </div>
  );
}
