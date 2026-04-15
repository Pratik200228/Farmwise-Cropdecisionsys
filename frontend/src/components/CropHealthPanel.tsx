import { useState, type FormEvent } from "react";
import { runHealthMonitoring, supportedMarketCrops } from "../lib/insightsApi";
import type { HealthIssue, HealthReport } from "../types/insights";

const GROWTH_STAGES = [
  "seedling",
  "vegetative",
  "flowering",
  "fruiting",
  "maturity",
];

const SYMPTOM_PRESETS = [
  "Yellow leaves on lower canopy",
  "Brown spots with yellow halos",
  "White powdery film on leaves",
  "Leaves curling with sticky residue",
  "Wilting in the afternoon",
  "Irregular holes chewed in leaves",
];

function severityTone(sev: HealthIssue["severity"]): string {
  return sev;
}

function IssueCard({ issue }: { issue: HealthIssue }) {
  return (
    <article className={`issue-card issue-card--${severityTone(issue.severity)}`}>
      <header className="issue-card__head">
        <div>
          <span className="issue-card__kind">{issue.kind}</span>
          <h3 className="issue-card__title">{issue.name}</h3>
        </div>
        <div className="issue-card__right">
          <span className={`sev-pill sev-pill--${issue.severity}`}>
            {issue.severity}
          </span>
          <span className="issue-card__prob">
            {Math.round(issue.probability * 100)}% likely
          </span>
        </div>
      </header>

      <div className="issue-card__body">
        <div>
          <h4 className="issue-card__h4">Symptoms</h4>
          <ul className="issue-card__list">
            {issue.symptoms.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </div>
        <div>
          <h4 className="issue-card__h4">Treatment</h4>
          <ul className="issue-card__list">
            {issue.treatment.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </div>
        <div>
          <h4 className="issue-card__h4">Prevent next time</h4>
          <ul className="issue-card__list issue-card__list--muted">
            {issue.preventive.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </div>
      </div>
    </article>
  );
}

export function CropHealthPanel() {
  const crops = supportedMarketCrops();
  const [crop, setCrop] = useState(crops[0]);
  const [growthStage, setGrowthStage] = useState("vegetative");
  const [symptoms, setSymptoms] = useState("");
  const [report, setReport] = useState<HealthReport | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async (note: string) => {
    setRunning(true);
    setError(null);
    try {
      const result = await runHealthMonitoring(crop, growthStage, note);
      setReport(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Health request failed");
    } finally {
      setRunning(false);
    }
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    void run(symptoms);
  };

  const onPreset = (preset: string) => {
    setSymptoms(preset);
    void run(preset);
  };

  return (
    <div className="health-page">
      <header className="page-head">
        <div>
          <div className="page-head__kicker">API integration</div>
          <h1 className="page-head__title">Crop Health</h1>
          <p className="page-head__sub">
            Describe what you see (or upload photos later) and the health API
            identifies likely diseases, pests, and nutrient issues — with
            treatment steps you can act on today.
          </p>
        </div>
      </header>

      <div className="health-grid">
        <form className="card health-input" onSubmit={onSubmit}>
          <div className="health-input__row">
            <label className="field">
              <span className="field__label">Crop</span>
              <select
                className="field__input"
                value={crop}
                onChange={(e) => setCrop(e.target.value)}
              >
                {crops.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span className="field__label">Growth stage</span>
              <select
                className="field__input"
                value={growthStage}
                onChange={(e) => setGrowthStage(e.target.value)}
              >
                {GROWTH_STAGES.map((g) => (
                  <option key={g} value={g}>
                    {g}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <label className="field">
            <span className="field__label">What do you see?</span>
            <textarea
              className="field__input field__input--area"
              rows={4}
              placeholder="e.g. lower leaves turning yellow with brown rings; some leaves curling"
              value={symptoms}
              onChange={(e) => setSymptoms(e.target.value)}
            />
          </label>

          <div className="health-presets">
            <div className="health-presets__label">Quick examples</div>
            <div className="health-presets__chips">
              {SYMPTOM_PRESETS.map((p) => (
                <button
                  key={p}
                  type="button"
                  className="suggestion-chip"
                  disabled={running}
                  onClick={() => onPreset(p)}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div className="health-input__actions">
            <button type="submit" className="btn btn--primary" disabled={running}>
              {running ? "Analyzing…" : "Analyze crop health"}
            </button>
            <span className="health-input__hint">
              Photos will plug into PlantVillage / Plantix when the backend is
              wired.
            </span>
          </div>

          {error ? <p className="panel-error">{error}</p> : null}
        </form>

        <div className="health-output">
          {!report && !running ? (
            <div className="card health-empty">
              <div className="health-empty__icon" aria-hidden>
                🩺
              </div>
              <h2>No scan yet</h2>
              <p>
                Describe a symptom or tap a quick example to run the health
                monitor. The API returns probable issues, treatment steps, and
                a 7-day scouting plan.
              </p>
            </div>
          ) : null}

          {running ? (
            <div className="card suit-running" aria-busy>
              <div className="suit-running__spinner" aria-hidden />
              <div>
                <strong>Running health check…</strong>
                <p>Matching patterns against the disease & pest database.</p>
              </div>
            </div>
          ) : null}

          {report ? (
            <>
              <section className={`card health-hero health-hero--${report.overallSeverity}`}>
                <div className="health-hero__meter" aria-hidden>
                  <svg viewBox="0 0 120 120" width="120" height="120">
                    <circle cx="60" cy="60" r="50" className="health-hero__bg" />
                    <circle
                      cx="60"
                      cy="60"
                      r="50"
                      className="health-hero__fg"
                      strokeDasharray={`${(report.healthScore / 100) * 314} 314`}
                      transform="rotate(-90 60 60)"
                    />
                    <text
                      x="60"
                      y="66"
                      textAnchor="middle"
                      className="health-hero__number"
                    >
                      {report.healthScore}
                    </text>
                  </svg>
                </div>
                <div className="health-hero__body">
                  <span className={`sev-pill sev-pill--${report.overallSeverity}`}>
                    {report.overallSeverity}
                  </span>
                  <h2 className="health-hero__title">
                    {report.crop} · {report.growthStage}
                  </h2>
                  <p className="health-hero__sub">
                    Overall health score for the observed symptoms.
                  </p>
                  <p className="health-hero__source">Source: {report.source}</p>
                </div>
              </section>

              <section className="issue-stack" aria-label="Identified issues">
                {report.issues.map((i) => (
                  <IssueCard key={i.name} issue={i} />
                ))}
              </section>

              <section className="card scouting-card">
                <h2 className="scouting-card__title">7-day scouting plan</h2>
                <ol className="scouting-card__list">
                  {report.scoutingPlan.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ol>
              </section>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
