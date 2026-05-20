import { getInterpolator } from "./palettes";

function formatLegendValue(value, format) {
  if (format === "percent") {
    return `${(value * 100).toFixed(0)}%`;
  }

  if (Math.abs(value) >= 100) return value.toFixed(0);
  if (Math.abs(value) >= 10) return value.toFixed(1);

  return value.toFixed(2);
}

function Legend({ layerMeta }) {
  if (!layerMeta) return null;

  const [min, max] = layerMeta.domain || [0, 1];

  const interpolator = getInterpolator(layerMeta.palette);

  const steps = 7;

  const legendSteps = Array.from({ length: steps }, (_, index) => {
    const t = index / (steps - 1);

    return {
      color: interpolator(t),
    };
  });

  return (
    <div className="legend">
      <div className="legend-title">
        {layerMeta.label}
      </div>

      <div className="legend-unit">
        {layerMeta.unit}
      </div>

      <div className="legend-gradient">
        {legendSteps.map((step, index) => (
          <div
            key={index}
            className="legend-gradient-block"
            style={{
              backgroundColor: step.color,
            }}
          />
        ))}
      </div>

      <div className="legend-scale">
        <span>
          {formatLegendValue(min, layerMeta.format)}
        </span>

        <span>
          {formatLegendValue(max, layerMeta.format)}
        </span>
      </div>
    </div>
  );
}

export default Legend;