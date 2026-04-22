import type { Environment } from "../types/farm";

type Props = {
  value: Environment;
  onChange: (next: Environment) => void;
};

type Slider = {
  key: keyof Environment;
  label: string;
  unit: string;
  min: number;
  max: number;
  step: number;
  help: string;
};

const SLIDERS: Slider[] = [
  {
    key: "temperatureC",
    label: "Avg. temperature",
    unit: "°C",
    min: -5,
    max: 45,
    step: 0.5,
    help: "Daytime average during the growing window.",
  },
  {
    key: "humidityPct",
    label: "Relative humidity",
    unit: "%",
    min: 0,
    max: 100,
    step: 1,
    help: "Field-level humidity — high values raise disease pressure.",
  },
  {
    key: "windKph",
    label: "Wind speed",
    unit: "km/h",
    min: 0,
    max: 60,
    step: 1,
    help: "Steady wind stresses tall crops like maize.",
  },
  {
    key: "rainfallMm",
    label: "Expected rainfall",
    unit: "mm",
    min: 0,
    max: 800,
    step: 5,
    help: "Total rainfall expected this cycle.",
  },
  {
    key: "soilPh",
    label: "Soil pH",
    unit: "",
    min: 3.5,
    max: 9,
    step: 0.1,
    help: "Most staples prefer 6.0–7.5.",
  },
  {
    key: "soilMoisturePct",
    label: "Soil moisture",
    unit: "%",
    min: 0,
    max: 100,
    step: 1,
    help: "Volumetric moisture in the root zone.",
  },
];

export function EnvironmentForm({ value, onChange }: Props) {
  const patch = (k: keyof Environment, v: number) =>
    onChange({ ...value, [k]: v });

  return (
    <div className="env-form">
      <div className="env-form__header">
        <h2 className="env-form__title">Environmental inputs</h2>
        <p className="env-form__sub">
          The Crop Suitability AI agent scores crops against these values. Drag
          the sliders or type a number.
        </p>
      </div>

      <div className="env-form__grid">
        {SLIDERS.map((s) => (
          <label key={s.key} className="env-slider">
            <div className="env-slider__top">
              <span className="env-slider__label">{s.label}</span>
              <span className="env-slider__value">
                {value[s.key]}
                {s.unit ? ` ${s.unit}` : ""}
              </span>
            </div>
            <input
              type="range"
              className="env-slider__range"
              min={s.min}
              max={s.max}
              step={s.step}
              value={value[s.key]}
              onChange={(e) => patch(s.key, Number.parseFloat(e.target.value))}
            />
            <div className="env-slider__help">{s.help}</div>
          </label>
        ))}
      </div>
    </div>
  );
}
