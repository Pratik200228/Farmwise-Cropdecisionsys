import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchMarketForecast, supportedMarketCrops } from "../lib/insightsApi";
import type { MarketReport, SellingWindow } from "../types/insights";
import { AgentBadge } from "./AgentBadge";
import { RichText } from "./RichText";

function confidenceLabel(c: SellingWindow["confidence"]): string {
  return c === "high" ? "High confidence" : c === "medium" ? "Medium" : "Low";
}

function deltaLabel(current: number, reference: number): { text: string; tone: string } {
  const pct = ((current - reference) / reference) * 100;
  const rounded = Math.round(pct * 10) / 10;
  if (Math.abs(rounded) < 0.5) return { text: "~flat vs median", tone: "flat" };
  const sign = rounded > 0 ? "+" : "";
  return {
    text: `${sign}${rounded}% vs median`,
    tone: rounded > 0 ? "up" : "down",
  };
}

export function MarketPricesPanel() {
  const crops = supportedMarketCrops();
  const [crop, setCrop] = useState(crops[0]);
  const [report, setReport] = useState<MarketReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchMarketForecast(crop)
      .then((r) => {
        if (!cancelled) setReport(r);
      })
      .catch((e) => {
        if (!cancelled)
          setError(e instanceof Error ? e.message : "Market request failed");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [crop]);

  const delta = report
    ? deltaLabel(report.currentPrice, report.seasonalMedian)
    : null;

  return (
    <div className="market-page">
      <header className="page-head">
        <div>
          <div className="page-head__kicker">Farm Intelligence</div>
          <h1 className="page-head__title">Market Forecaster</h1>
          <p className="page-head__sub">
            Correlates historical crop pricing data with seasonal trends to recommend optimal sell windows.
          </p>
          <AgentBadge
            accent="market"
            name="Yield Economics"
            type="Predictive Pricing"
            role="Maximizes expected profit by ranking sell windows against a seasonal median."
          />
        </div>

        <label className="crop-select">
          <span className="crop-select__label">Crop</span>
          <select
            className="crop-select__input"
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
      </header>

      {error ? <p className="panel-error">{error}</p> : null}

      {report ? (
        <div className="market-grid">
          <section className="card kpi kpi--primary">
            <span className="kpi__label">Current price</span>
            <span className="kpi__value">
              {report.currentPrice}
              <span className="kpi__unit"> {report.unit}</span>
            </span>
            {delta ? (
              <span className={`kpi__delta kpi__delta--${delta.tone}`}>
                {delta.text}
              </span>
            ) : null}
          </section>

          <section className="card kpi">
            <span className="kpi__label">Seasonal median</span>
            <span className="kpi__value">
              {report.seasonalMedian}
              <span className="kpi__unit"> {report.unit}</span>
            </span>
            <span className="kpi__hint">Reference baseline</span>
          </section>

          <section className="card kpi">
            <span className="kpi__label">Forecast peak</span>
            <span className="kpi__value">
              {Math.max(
                ...report.trend.filter((t) => t.forecast).map((t) => t.price),
              )}
              <span className="kpi__unit"> {report.unit}</span>
            </span>
            <span className="kpi__hint">Next 3 weeks</span>
          </section>

          <section className="card market-chart">
            <div className="market-chart__head">
              <h2 className="market-chart__title">8-week price trend</h2>
              <div className="market-chart__legend" aria-hidden>
                <span className="legend-dot legend-dot--hist" /> Historical
                <span className="legend-dot legend-dot--fore" /> Forecast
              </div>
            </div>
            <div className="market-chart__plot">
              <ResponsiveContainer width="100%" height={260}>
                <LineChart
                  data={report.trend}
                  margin={{ top: 10, right: 20, bottom: 0, left: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--stroke)" />
                  <XAxis
                    dataKey="label"
                    tick={{ fill: "var(--muted)", fontSize: 12 }}
                  />
                  <YAxis
                    tick={{ fill: "var(--muted)", fontSize: 12 }}
                    domain={["dataMin - 3", "dataMax + 3"]}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "var(--surface-2)",
                      border: "1px solid var(--stroke)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                    formatter={(v) => [`${v} ${report.unit}`, "Price"]}
                  />
                  <ReferenceLine
                    y={report.seasonalMedian}
                    stroke="var(--accent-2)"
                    strokeDasharray="4 4"
                    label={{
                      value: "Median",
                      position: "right",
                      fill: "var(--accent-2)",
                      fontSize: 11,
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="price"
                    stroke="var(--accent)"
                    strokeWidth={2.5}
                    dot={{ fill: "var(--accent)", stroke: "var(--accent)", r: 3 }}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="card market-summary">
            <h2 className="market-summary__title">What this means</h2>
            <RichText text={report.summary} />
          </section>

          <section className="card market-windows">
            <h2 className="market-windows__title">Suggested selling windows</h2>
            <ul className="market-windows__list">
              {report.windows.map((w) => (
                <li
                  key={w.label}
                  className={`market-window market-window--${w.confidence}`}
                >
                  <div className="market-window__top">
                    <span className="market-window__label">{w.label}</span>
                    <span className={`confidence-pill confidence-pill--${w.confidence}`}>
                      {confidenceLabel(w.confidence)}
                    </span>
                  </div>
                  <div className="market-window__when">{w.window}</div>
                  <div className="market-window__reason">{w.reason}</div>
                </li>
              ))}
            </ul>
          </section>
        </div>
      ) : null}

      {loading && !report ? (
        <div className="card suit-running" aria-busy>
          <div className="suit-running__spinner" aria-hidden />
          <div>
            <strong>Fetching forecast…</strong>
            <p>Pulling historical prices and running the forecaster.</p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
