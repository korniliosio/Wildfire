import { useEffect, useMemo, useState } from "react";
import MapView from "./components/MapView";
import LayerSelector from "./components/LayerSelector";
import { toPng } from "html-to-image";
import { publicPath } from "./utils/paths";


function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${Math.round(value * 100)}%`;
}

function App() {
    const [metadata, setMetadata] = useState(null);
    const [dates, setDates] = useState([]);
    const [selectedLayer, setSelectedLayer] = useState(null);
    const [selectedDateIndex, setSelectedDateIndex] = useState(0);
    const [error, setError] = useState(null);

    // Display states
    const [showViirs, setShowViirs] = useState(true);
    const [showLabels, setShowLabels] = useState(true);

    // Layer info states
    const [showLayerInfo, setShowLayerInfo] = useState(false);

    // Daily summary states
    const [dailyBundle, setDailyBundle] = useState(null);
    const [showDailySummary, setShowDailySummary] = useState(false);

    async function handleExportMapFigure() {
      const mapElement = document.getElementById("map-capture-source");
      if (!mapElement) return;

      try {
        const mapDataUrl = await toPng(mapElement, {
          cacheBust: true,
          pixelRatio: 2,
          backgroundColor: "#ffffff",
        });

        const link = document.createElement("a");
        link.download = `wildfire-${selectedLayer}-${selectedDate}.png`;
        link.href = mapDataUrl;
        link.click();
      } catch (err) {
        console.error("Failed to export map figure:", err);
      }
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

    useEffect(() => {
      async function loadDailyBundle() {
        if (!selectedDate) {
          setDailyBundle(null);
          return;
        }

        try {
          const response = await fetch(
            publicPath(`data/bundles/${selectedDate}.json`)
          );

          if (!response.ok) {
            setDailyBundle(null);
            return;
          }

          const data = await response.json();
          setDailyBundle(Array.isArray(data) ? data : []);
        } catch (err) {
          console.warn(`Could not load daily summary for ${selectedDate}`, err);
          setDailyBundle(null);
        }
      }

      loadDailyBundle();
    }, [selectedDate]);

    const dailySummary = useMemo(() => {
      if (!dailyBundle || !dailyBundle.length) return null;

      const risks = dailyBundle
        .map((row) => row.p_fire_tomorrow)
        .filter((value) => typeof value === "number" && !Number.isNaN(value));

      if (!risks.length) return null;

      const meanRisk =
        risks.reduce((sum, value) => sum + value, 0) / risks.length;

      const maxRisk = Math.max(...risks);

      const highRiskCells = dailyBundle.filter(
        (row) => row.p_fire_tomorrow >= 0.8
      ).length;

      const observedFireCells = dailyBundle.filter(
        (row) => row.fire === 1
      ).length;

      return {
        meanRisk,
        maxRisk,
        highRiskCells,
        observedFireCells,
        totalCells: dailyBundle.length,
      };
    }, [dailyBundle]);

  return (
    
    <div className="app-shell">
      <aside className="left-sidebar">
        <div className="brand-card">
          <div className="brand-icon">
            <img src="./fire.png" alt="Fire icon" className="brand-image" />
          </div>
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
        {selectedLayerMeta && (
          <div className="layer-summary">
            <p className="layer-description">
              {selectedLayerMeta.description || "No description available."}
            </p>

            <div className="layer-unit-row">
              Unit: <strong>{selectedLayerMeta.unit || "—"}</strong>
            </div>

            <button
              className="accordion-header"
              onClick={() => setShowLayerInfo((v) => !v)}
            >
              <span>Layer information</span>
              <span>{showDailySummary ? "−" : "+"}</span>
            </button>

            
            {showLayerInfo && (
              <div className="layer-info-expanded">
                <div>
                  <span>Type</span>
                  <strong>{selectedLayerMeta.temporal ? "Temporal" : "Static"}</strong>
                </div>

                <div>
                  <span>Source</span>
                  <strong>
                    {selectedLayerMeta.data_source || selectedLayerMeta.source || "—"}
                  </strong>
                </div>

                <div>
                  <span>Range</span>
                  <strong>
                    {selectedLayerMeta.domain
                      ? `${selectedLayerMeta.domain[0]} – ${selectedLayerMeta.domain[1]}`
                      : "—"}
                  </strong>
                </div>

                {selectedLayerMeta.interpretation && (
                  <div className="layer-interpretation">
                    {selectedLayerMeta.interpretation}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
        </section>

        <section className="control-card">
          <button
            className="accordion-header"
            onClick={() => setShowDailySummary((value) => !value)}
          >
            <span>Daily Summary</span>
            <span>{showDailySummary ? "−" : "+"}</span>
          </button>

          {showDailySummary && dailySummary && (
            <div className="daily-summary-body">
              <div className="summary-date">{selectedDate}</div>

              <div className="daily-summary-grid">
                <div>
                  <span>Mean Risk</span>
                  <strong>{formatPercent(dailySummary.meanRisk)}</strong>
                </div>

                <div>
                  <span>Max Risk</span>
                  <strong>{formatPercent(dailySummary.maxRisk)}</strong>
                </div>

                <div>
                  <span>High Risk</span>
                  <strong>{dailySummary.highRiskCells}</strong>
                </div>

                <div>
                  <span>Fires Today</span>
                  <strong>{dailySummary.observedFireCells}</strong>
                </div>
              </div>

              <div className="summary-note">
                Total cells: <strong>{dailySummary.totalCells}</strong>
              </div>
            </div>
          )}

          {showDailySummary && !dailySummary && (
            <div className="summary-note">Loading daily summary…</div>
          )}
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

      <section className="sidebar-footer-actions">
        <button className="export-utility-button" onClick={handleExportMapFigure}>
          Export PNG
        </button>
      </section>

      </aside>

      <main className="main-stage">

        <MapView
          selectedLayer={selectedLayer}
          selectedDate={selectedDate}
          metadata={metadata}
          showViirs={showViirs}
          showLabels={showLabels}
          dates={dates}
          selectedDateIndex={selectedDateIndex}
          onDateIndexChange={setSelectedDateIndex}

        />
        
      </main>
    </div>
  );
}

export default App;