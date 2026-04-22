import type { FarmContext, FarmGoal } from "../types/farm";

const goals: { value: FarmGoal; label: string }[] = [
  { value: "yield", label: "Yield" },
  { value: "profit", label: "Profit" },
  { value: "sustainability", label: "Sustainability" },
  { value: "mixed", label: "Balanced" },
];

type Props = {
  value: FarmContext;
  onChange: (next: FarmContext) => void;
};

export function FarmContextForm({ value, onChange }: Props) {
  const patch = (partial: Partial<FarmContext>) =>
    onChange({ ...value, ...partial });

  return (
    <div className="farm-context">
      <h2 className="farm-context__title">Farm context</h2>
      <p className="farm-context__hint">
        The advisor sends this JSON with every chat request so the model stays
        grounded in your operation.
      </p>

      <label className="field">
        <span className="field__label">Region / district</span>
        <input
          className="field__input"
          type="text"
          placeholder="e.g. Western Terai, Nepal"
          value={value.region}
          onChange={(e) => patch({ region: e.target.value })}
          autoComplete="address-level1"
        />
      </label>

      <label className="field">
        <span className="field__label">Soil type</span>
        <select
          className="field__input"
          value={value.soilType}
          onChange={(e) => patch({ soilType: e.target.value })}
        >
          <option value="loam">Loam</option>
          <option value="clay">Clay</option>
          <option value="sandy">Sandy</option>
          <option value="silt">Silt</option>
          <option value="black">Black / vertisol</option>
        </select>
      </label>

      <label className="field">
        <span className="field__label">Farm size (acres)</span>
        <input
          className="field__input"
          type="number"
          min={0}
          step={0.1}
          value={value.farmSizeAcres}
          onChange={(e) =>
            patch({ farmSizeAcres: Number.parseFloat(e.target.value) || 0 })
          }
        />
      </label>

      <fieldset className="field field--inline">
        <legend className="field__label">Primary goal</legend>
        <div className="chip-row">
          {goals.map((g) => (
            <button
              key={g.value}
              type="button"
              className={`chip ${value.primaryGoal === g.value ? "chip--on" : ""}`}
              onClick={() => patch({ primaryGoal: g.value })}
            >
              {g.label}
            </button>
          ))}
        </div>
      </fieldset>

      <label className="field">
        <span className="field__label">Season</span>
        <input
          className="field__input"
          type="text"
          placeholder="kharif / rabi / dry season"
          value={value.season}
          onChange={(e) => patch({ season: e.target.value })}
        />
      </label>

      <label className="field">
        <span className="field__label">Notes for the model</span>
        <textarea
          className="field__input field__input--area"
          rows={3}
          placeholder="Rotation history, water source, main crops…"
          value={value.notes}
          onChange={(e) => patch({ notes: e.target.value })}
        />
      </label>
    </div>
  );
}
