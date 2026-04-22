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

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        const s = await runCropSuitabilityAgent(defaultFarmContext());
        if (cancelled) return;
        setSuit(s);
        const focus = s.crops[0]?.name ?? "Maize";
        const [m, h] = await Promise.all([
          fetchMarketForecast(focus),
          runHealthMonitoring(focus, "vegetative", ""),
        ]);
        if (cancelled) return;
        setMarket(m);
        setHealth(h);
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

  const priceDelta =
    market &&
    Math.round(
      ((market.currentPrice - market.seasonalMedian) / market.seasonalMedian) *
        1000,
    ) / 10;

  return (
    <div className="overview">
      <header className="page-head">
        <div>
          <div className="page-head__kicker">Today</div>
          <h1 className="page-head__title">Farm overview</h1>
          <p className="page-head__sub">
            One FarmWise AI agent plus two connected services in one snapshot:
            crop suitability (what to plant), market pricing (when to sell),
            and crop health monitoring (what to scout). Tap any card to open
            its workflow.
          </p>
        </div>
      </header>

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
              : "Run the agent to see recommendations."}
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
              : "Forecast loading…"}
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
              : "Scan loading…"}
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
