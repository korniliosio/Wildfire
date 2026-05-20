import { useEffect, useMemo, useState } from "react";
import MapView from "./components/MapView";
import TimeControls from "./components/TimeControls";
import LayerSelector from "./components/LayerSelector";
import { toPng } from "html-to-image";
import { publicPath } from "./utils/paths";

  function App() {
    const [metadata, setMetadata] = useState(null);
    const [dates, setDates] = useState([]);
    const [selectedLayer, setSelectedLayer] = useState(null);
    const [selectedDateIndex, setSelectedDateIndex] = useState(0);
    const [error, setError] = useState(null);
    const [showViirs, setShowViirs] = useState(true);
    const [showLabels, setShowLabels] = useState(true);

    async function handleExportMapFigure() {
      const mapElement = document.getElementById("map-capture-source");
      if (!mapElement) return;

      const mapDataUrl = await toPng(mapElement, {
        cacheBust: true,
        pixelRatio: 2,
        backgroundColor: "#ffffff",
      });

      const mapImage = new Image();
      mapImage.src = mapDataUrl;

      mapImage.onload = () => {
        const headerHeight = 110;

        const finalCanvas = document.createElement("canvas");
        finalCanvas.width = mapImage.width;
        finalCanvas.height = mapImage.height + headerHeight;

        const ctx = finalCanvas.getContext("2d");

        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, finalCanvas.width, finalCanvas.height);

        ctx.fillStyle = "#111827";
        ctx.font = "bold 34px Arial";
        ctx.fillText("Wildfire Risk Explorer", 32, 42);

        ctx.fillStyle = "#64748b";
        ctx.font = "bold 19px Arial";
        ctx.fillText(
          `Date: ${selectedDate} · Layer: ${selectedLayerMeta?.label || selectedLayer}`,
          32,
          76
        );

        ctx.drawImage(mapImage, 0, headerHeight);

        const link = document.createElement("a");
        link.download = `wildfire-${selectedLayer}-${selectedDate}.png`;
        link.href = finalCanvas.toDataURL("image/png");
        link.click();
      };
    }
  useEffect(() => {
    async function loadAppConfig() {
      try {
        const [metadataResponse, datesResponse] = await Promise.all([
          fetch(publicPath("data/metadata.json")),
          fetch(publicPath("data/dates.json"))
        ]);

        if (!metadataResponse.ok) {
          throw new Error(`Failed to load metadata.json: ${metadataResponse.status}`);
        }

        if (!datesResponse.ok) {
          throw new Error(`Failed to load dates.json: ${datesResponse.status}`);
        }

        const metadataData = await metadataResponse.json();
        const datesData = await datesResponse.json();

        setMetadata(metadataData);
        setDates(datesData);
        setSelectedLayer(metadataData.app.default_layer);

        const defaultIndex = datesData.indexOf(metadataData.app.default_date);
        setSelectedDateIndex(defaultIndex >= 0 ? defaultIndex : 0);
      } catch (err) {
        console.error(err);
        setError(err.message);
      }
    }

    loadAppConfig();
  }, []);

  const selectedDate = useMemo(() => {
    if (!dates.length) return null;
    return dates[selectedDateIndex] || null;
  }, [dates, selectedDateIndex]);

  const selectedLayerMeta =
    metadata?.layers?.find((layer) => layer.id === selectedLayer) || null;

  return (
    
    <div className="app-shell">
      <aside className="left-sidebar">
        <div className="brand-card">
          <div className="brand-icon">🔥</div>
          <div>
            <h1>Wildfire Risk Explorer</h1>
            <p>Next-day fire occurrence risk across Greece</p>
          </div>
        </div>

        {error && <div className="error-card">{error}</div>}

        <section className="control-card">
          <div className="section-kicker">Visualization</div>

          {metadata?.layers && (
            <LayerSelector
              layers={metadata.layers}
              selectedLayer={selectedLayer}
              onLayerChange={setSelectedLayer}
            />
          )}

           <div>
              <span>Unit: </span>
              <strong>{selectedLayerMeta?.unit || "—"}</strong>
          </div>
        </section>

        <section className="control-card">
          <div className="section-kicker">Timeline</div>

          <TimeControls
            dates={dates}
            selectedDateIndex={selectedDateIndex}
            onDateIndexChange={setSelectedDateIndex}
          />
        </section>
        <section className="control-card">

        <div className="section-kicker">Observed Fires</div>

        <label className="toggle-row">
          <input
            type="checkbox"
            checked={showViirs}
            onChange={(e) => setShowViirs(e.target.checked)}
          />
          <span>Show VIIRS detections</span>
        </label>
      </section>

      <section className="control-card">
      <div className="section-kicker">Labels</div>
      <label className="toggle-row">
        <input
          type="checkbox"
          checked={showLabels}
          onChange={(e) => setShowLabels(e.target.checked)}
        />
        <span>Show place labels</span>
      </label>
      </section>

      </aside>

      <main className="main-stage">
        <div className="top-bar">
          <div>
            <div className="top-bar-title">
              {selectedLayerMeta?.label || "Map Layer"}
            </div>
            <div className="top-bar-subtitle">
              {selectedDate
                ? `Showing spatial values for ${selectedDate}`
                : "Loading date range"}
            </div>
          </div>

          <button className="export-button" onClick={handleExportMapFigure}>
              Export PNG
          </button>
        </div>

        <MapView
          selectedLayer={selectedLayer}
          selectedDate={selectedDate}
          metadata={metadata}
          showViirs={showViirs}
          showLabels={showLabels}
        />

        
      </main>
    </div>
  );
}

export default App;