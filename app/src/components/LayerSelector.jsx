function LayerSelector({ layers, selectedLayer, onLayerChange }) {
  return (
    <div className="layer-selector">
      <label htmlFor="layer-select">Map layer</label>

      <select
        id="layer-select"
        value={selectedLayer || ""}
        onChange={(event) => onLayerChange(event.target.value)}
      >
        {layers.map((layer) => (
          <option key={layer.id} value={layer.id}>
            {layer.label}
          </option>
        ))}
      </select>
    </div>
  );
}

export default LayerSelector;