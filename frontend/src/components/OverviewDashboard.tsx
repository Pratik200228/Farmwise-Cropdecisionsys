import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  fetchMarketForecast,
  runCropSuitabilityAgent,
  runHealthMonitoring,
} from "../lib/insightsApi";
import sunriseFieldTheme from "../assets/sunrise-field-theme.jpg";
import { defaultFarmContext } from "../types/farm";
import type {
  HealthReport,
  MarketReport,
  SuitabilityReport,
} from "../types/insights";

type Nav = "advisor" | "suitability" | "market" | "health";

type Props = {
  onNavigate?: (nav: Nav) => void;
};

export function OverviewDashboard({ onNavigate }: Props) {
  const [suit, setSuit] = useState<SuitabilityReport | null>(null);
  const [market, setMarket] = useState<MarketReport | null>(null);
  const [health, setHealth] = useState<HealthReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const s = await runCropSuitabilityAgent(defaultFarmContext());
        if (cancelled) return;
        setSuit(s);
        const focus = s.crops[0]?.name ?? "Maize";
        const settled = await Promise.allSettled([
          fetchMarketForecast(focus),
          runHealthMonitoring(focus, "vegetative", ""),
        ]);
        if (cancelled) return;
        const problems: string[] = [];

        if (settled[0].status === "fulfilled") {
          setMarket(settled[0].value);
        } else {
          setMarket(null);
          problems.push("Market signals are temporarily unavailable.");
        }

        if (settled[1].status === "fulfilled") {
          setHealth(settled[1].value);
        } else {
          setHealth(null);
          problems.push("Crop health monitoring is temporarily unavailable.");
        }

        if (problems.length > 0) {
          setError(problems.join(" "));
        }
      } catch (e) {
        if (!cancelled) {
          setSuit(null);
          setMarket(null);
          setHealth(null);
          setError(
            e instanceof Error
              ? e.message
              : "Could not load the FarmWise home dashboard.",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const barData =
    suit?.crops.slice(0, 5).map((c) => ({ crop: c.name, score: c.score })) ?? [];
  const focusCrop = suit?.crops[0] ?? null;
  const forecastPoints = market?.trend.filter((t) => t.forecast) ?? [];
  const forecastPeak =
    forecastPoints.length > 0
      ? Math.max(...forecastPoints.map((point) => point.price))
      : null;
  const leadIssue = health?.issues[0]?.name ?? "Routine field scouting";

  const priceDelta =
    market &&
    Math.round(
      ((market.currentPrice - market.seasonalMedian) / market.seasonalMedian) *
        1000,
    ) / 10;

  const heroStats = [
    {
      label: "Best crop fit",
      value: focusCrop ? focusCrop.name : "Loading",
      detail: focusCrop
        ? `${focusCrop.score}/100 suitability score`
        : "Waiting for the first analysis",
      tone: "suit",
    },
    {
      label: "Market peak",
      value: market && forecastPeak ? `${forecastPeak}` : "Loading",
      detail: market
        ? `Projected in ${market.unit}`
        : "Forecast service is syncing",
      tone: "market",
    },
    {
      label: "Health watch",
      value: health ? health.overallSeverity : "Loading",
      detail: health
        ? leadIssue
        : "Scanning for early field issues",
      tone: "health",
    },
  ] as const;

  return (
    <div className="overview">
      <header className="page-head">
        <div>
          <div className="page-head__kicker">Sunrise dashboard</div>
          <h1 className="page-head__title">Farm overview</h1>
          <p className="page-head__sub">
            A calmer, field-first home base for FarmWise. The dashboard now
            opens with the same sunrise rhythm as your reference image while
            keeping planting, selling, and scouting decisions close at hand.
          </p>
        </div>
      </header>

      <section className="overview-hero card">
        <div className="overview-hero__content">
          <div className="overview-hero__eyebrow">Dawn briefing</div>
          <h2 className="overview-hero__title">
            Start each farming day with a clearer read on what to plant, watch,
            and sell.
          </h2>
          <p className="overview-hero__sub">
            FarmWise blends one crop-suitability AI workflow with market and
            crop-health services, wrapped in a softer sunrise palette grounded
            in field imagery instead of a generic dashboard skin.
          </p>

          <div className="overview-hero__chips" aria-label="Home highlights">
            <span className="overview-hero__chip">Crop-fit ranking</span>
            <span className="overview-hero__chip">Market timing windows</span>
            <span className="overview-hero__chip">Field health monitoring</span>
          </div>

          <div className="overview-hero__actions">
            <button
              type="button"
              className="btn btn--primary"
              onClick={() => onNavigate?.("suitability")}
            >
              Open crop suitability
            </button>
            <button
              type="button"
              className="btn btn--ghost"
              onClick={() => onNavigate?.("advisor")}
            >
              Ask FarmWise
            </button>
          </div>

          <div className="overview-hero__stats">
            {heroStats.map((item) => (
              <div
                key={item.label}
                className={`overview-hero__stat overview-hero__stat--${item.tone}`}
              >
                <div className="overview-hero__stat-label">{item.label}</div>
                <div className="overview-hero__stat-value">{item.value}</div>
                <div className="overview-hero__stat-detail">{item.detail}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="overview-hero__visual">
          <img
            className="overview-hero__image"
            src={sunriseFieldTheme}
            alt="Sunrise over crop rows"
          />
          <div className="overview-hero__caption">
            Warm sunrise light, open field lines, and a calmer visual rhythm for
            the FarmWise home page.
          </div>
        </div>
      </section>

      {error ? (
        <div className="overview-banner" role="status">
          <strong>Heads up:</strong> {error}
        </div>
      ) : null}

      {loading && !suit ? (
        <div className="card suit-running" aria-busy>
          <div className="suit-running__spinner" aria-hidden />
          <div>
            <strong>Loading the latest snapshot…</strong>
            <p>Running suitability analysis and pulling market and health data.</p>
          </div>
        </div>
      ) : null}

      <div className="overview-grid">
        <button
          type="button"
          className="card overview-card overview-card--suit"
          onClick={() => onNavigate?.("suitability")}
        >
          <div className="overview-card__kicker">AI agent · Suitability</div>
          <div className="overview-card__big">
            {suit?.crops[0]?.name ?? "—"}
          </div>
          <div className="overview-card__score">
            {suit?.crops[0]?.score ?? "—"}/100
          </div>
          <p className="overview-card__note">
            {suit
              ? `Confidence ${Math.round(
                  (suit.crops[0]?.confidence ?? 0) * 100,
                )}% · ${suit.crops.length} crops ranked`
              : "Run the crop-fit engine to see recommendations."}
          </p>
          <span className="overview-card__arrow" aria-hidden>
            →
          </span>
        </button>

        <button
          type="button"
          className="card overview-card overview-card--market"
          onClick={() => onNavigate?.("market")}
        >
          <div className="overview-card__kicker">API service · Market</div>
          <div className="overview-card__big">
            {market ? `${market.currentPrice}` : "—"}
            <span className="overview-card__unit">
              {market ? ` ${market.unit}` : ""}
            </span>
          </div>
          <div
            className={`overview-card__score overview-card__score--${
              priceDelta && priceDelta > 0 ? "up" : priceDelta && priceDelta < 0 ? "down" : "flat"
            }`}
          >
            {market
              ? `${priceDelta && priceDelta > 0 ? "+" : ""}${priceDelta}% vs median`
              : "—"}
          </div>
          <p className="overview-card__note">
            {market
              ? `${market.crop} · next peak ≈ ${Math.max(
                  ...market.trend.filter((t) => t.forecast).map((t) => t.price),
                )}`
              : "Waiting for price direction…"}
          </p>
          <span className="overview-card__arrow" aria-hidden>
            →
          </span>
        </button>

        <button
          type="button"
          className="card overview-card overview-card--health"
          onClick={() => onNavigate?.("health")}
        >
          <div className="overview-card__kicker">API service · Health</div>
          <div className="overview-card__big">
            {health ? `${health.healthScore}` : "—"}
            <span className="overview-card__unit">/100</span>
          </div>
          <div
            className={`overview-card__score overview-card__score--sev-${health?.overallSeverity ?? "flat"}`}
          >
            {health ? health.overallSeverity : "—"}
          </div>
          <p className="overview-card__note">
            {health
              ? `${health.crop} · ${health.issues.length} issue${
                  health.issues.length === 1 ? "" : "s"
                } identified`
              : "Waiting for field health signals…"}
          </p>
          <span className="overview-card__arrow" aria-hidden>
            →
          </span>
        </button>

        <section className="card overview-chart">
          <div className="overview-chart__head">
            <h2 className="overview-chart__title">Top 5 suitability scores</h2>
            <button
              type="button"
              className="btn btn--ghost btn--sm"
              onClick={() => onNavigate?.("suitability")}
            >
              Open agent
            </button>
          </div>
          <div className="overview-chart__plot">
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={barData} layout="vertical" margin={{ left: 8, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--stroke)" />
                <XAxis type="number" domain={[0, 100]} tick={{ fill: "var(--muted)" }} />
                <YAxis
                  type="category"
                  dataKey="crop"
                  width={72}
                  tick={{ fill: "var(--muted)", fontSize: 12 }}
                />
                <Tooltip
                  contentStyle={{
                    background: "var(--surface-2)",
                    border: "1px solid var(--stroke)",
                    borderRadius: 8,
                  }}
                />
                <Bar
                  dataKey="score"
                  fill="var(--accent)"
                  radius={[0, 6, 6, 0]}
                  name="Score"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="card overview-advice">
          <h2 className="overview-advice__title">Action items this week</h2>
          <ul className="overview-advice__list">
            {suit ? (
              <li>
                <strong>Plant:</strong> {suit.crops[0]?.name} —{" "}
                {suit.crops[0]?.plantingWindow}
              </li>
            ) : null}
            {market ? (
              <li>
                <strong>Market:</strong> {market.windows[0]?.label} —{" "}
                {market.windows[0]?.reason}
              </li>
            ) : null}
            {health ? (
              <li>
                <strong>Scout:</strong> {health.scoutingPlan[0]}
              </li>
            ) : null}
            {!loading && !suit ? (
              <li>No recommendations yet — run the agent.</li>
            ) : null}
          </ul>
        </section>
      </div>
    </div>
  );
}
