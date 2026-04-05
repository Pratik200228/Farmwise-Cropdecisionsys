import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const suitability = [
  { crop: "Maize", score: 88 },
  { crop: "Wheat", score: 72 },
  { crop: "Lentil", score: 79 },
  { crop: "Tomato", score: 65 },
  { crop: "Potato", score: 91 },
];

const marketPreview = [
  { week: "W1", price: 42 },
  { week: "W2", price: 44 },
  { week: "W3", price: 41 },
  { week: "W4", price: 47 },
];

export function DashboardPanel() {
  return (
    <div className="dashboard">
      <header className="dashboard__head">
        <h1 className="dashboard__title">Operations dashboard</h1>
        <p className="dashboard__sub">
          Sample charts — connect Recharts to your FastAPI suitability and USDA
          endpoints when ready.
        </p>
      </header>

      <div className="dashboard__grid">
        <section className="card chart-card">
          <h2 className="chart-card__title">Crop suitability (demo scores)</h2>
          <div className="chart-card__plot">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart
                data={suitability}
                layout="vertical"
                margin={{ left: 8, right: 16 }}
              >
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

        <section className="card chart-card">
          <h2 className="chart-card__title">Price trend (placeholder)</h2>
          <div className="chart-card__plot">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={marketPreview}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--stroke)" />
                <XAxis dataKey="week" tick={{ fill: "var(--muted)" }} />
                <YAxis tick={{ fill: "var(--muted)" }} />
                <Tooltip
                  contentStyle={{
                    background: "var(--surface-2)",
                    border: "1px solid var(--stroke)",
                    borderRadius: 8,
                  }}
                />
                <Bar
                  dataKey="price"
                  fill="var(--accent-2)"
                  radius={[6, 6, 0, 0]}
                  name="Index"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>
    </div>
  );
}
