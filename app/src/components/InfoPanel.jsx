function formatValue(value) {
  if (value == null || Number.isNaN(value)) return "No data";
  if (typeof value === "number") return value.toFixed(4);
  return String(value);
}

function InfoPanel({ selectedCell, selectedLayerMeta, selectedDate }) {
  if (!selectedCell) {
    return (
      <div className="info-panel">
        <div className="info-panel-title">Cell Information</div>
        <div className="info-panel-empty">Click a cell to inspect its values.</div>
      </div>
    );
  }

  return (
    <div className="info-panel">
      <div className="info-panel-title">Cell Information</div>

      <div className="info-row">
        <span className="info-label">Cell ID</span>
        <span className="info-value">{selectedCell.cell_id}</span>
      </div>

      <div className="info-row">
        <span className="info-label">Date</span>
        <span className="info-value">{selectedDate}</span>
      </div>

      <div className="info-row">
        <span className="info-label">Active Layer</span>
        <span className="info-value">{selectedLayerMeta?.label || "Unknown"}</span>
      </div>

      <div className="info-row">
        <span className="info-label">Active Value</span>
        <span className="info-value">{formatValue(selectedCell.activeValue)}</span>
      </div>

      <hr />

      <div className="info-row">
        <span className="info-label">Predicted Fire Risk</span>
        <span className="info-value">{formatValue(selectedCell.p_fire_tomorrow)}</span>
      </div>

      <div className="info-row">
        <span className="info-label">Fire Tomorrow</span>
        <span className="info-value">{formatValue(selectedCell.fire_tomorrow)}</span>
      </div>

      <div className="info-row">
        <span className="info-label">Fire Today</span>
        <span className="info-value">{formatValue(selectedCell.fire)}</span>
      </div>

      <hr />

      <div className="info-row">
        <span className="info-label">Slope</span>
        <span className="info-value">{formatValue(selectedCell.slope_mean)}</span>
      </div>

      <div className="info-row">
        <span className="info-label">Elevation</span>
        <span className="info-value">{formatValue(selectedCell.elev_mean)}</span>
      </div>

      <div className="info-row">
        <span className="info-label">Agriculture Fraction</span>
        <span className="info-value">{formatValue(selectedCell.fuel_agriculture_frac)}</span>
      </div>

      <div className="info-row">
        <span className="info-label">Urban Fraction</span>
        <span className="info-value">{formatValue(selectedCell.fuel_urban_frac)}</span>
      </div>

      <div className="info-row">
        <span className="info-label">Shrub Fraction</span>
        <span className="info-value">{formatValue(selectedCell.fuel_shrub_frac)}</span>
      </div>

      <div className="info-row">
        <span className="info-label">Grass Fraction</span>
        <span className="info-value">{formatValue(selectedCell.fuel_grass_frac)}</span>
      </div>

      <hr />

      <div className="info-row">
        <span className="info-label">Min RH</span>
        <span className="info-value">{formatValue(selectedCell.rh_daily_min)}</span>
      </div>

      <div className="info-row">
        <span className="info-label">Max Temp</span>
        <span className="info-value">{formatValue(selectedCell.temp_daily_max_C)}</span>
      </div>

      <div className="info-row">
        <span className="info-label">Max Wind</span>
        <span className="info-value">{formatValue(selectedCell.wind_daily_max)}</span>
      </div>
    </div>
  );
}

export default InfoPanel;