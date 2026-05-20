import { useEffect, useMemo, useState } from "react";
import L from "leaflet";
import { MapContainer, TileLayer, GeoJSON, CircleMarker, Tooltip, useMap } from "react-leaflet";import Legend from "./Legend";
import InfoPanel from "./InfoPanel";
import { Pane } from "react-leaflet";
import { getInterpolator } from "./palettes";



function FitBounds({ geojson }) {
  const map = useMap();

  useEffect(() => {
    if (!geojson) return;

    const layer = L.geoJSON(geojson);
    const bounds = layer.getBounds();

    if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [20, 20] });
    }
  }, [geojson, map]);

  return null;
}

function getColorForValue(value, layerMeta) {
  if (
    value === undefined ||
    value === null ||
    Number.isNaN(value)
  ) {
    return "#d1d5db";
  }

  const [min, max] = layerMeta?.domain || [0, 1];

  const t = Math.max(
    0,
    Math.min(1, (value - min) / (max - min || 1))
  );

  const interpolator = getInterpolator(layerMeta?.palette);
  return interpolator(t);
}

function MapView({ selectedLayer, selectedDate, metadata, showViirs, showLabels, exportMode = false }) {  
  const [gridData, setGridData] = useState(null);
  const [bundleData, setBundleData] = useState(null);
  const [staticData, setStaticData] = useState(null);
  const [selectedCell, setSelectedCell] = useState(null);
  const [error, setError] = useState(null);
  const [viirsData, setViirsData] = useState([]);

  const selectedLayerMeta =
    metadata?.layers?.find((layer) => layer.id === selectedLayer) || null;

  useEffect(() => {
    async function loadGrid() {
      try {
        const response = await fetch("/data/grid.geojson");
        if (!response.ok) {
          throw new Error(`Failed to load grid.geojson: ${response.status}`);
        }

        const data = await response.json();
        setGridData(data);
      } catch (err) {
        console.error(err);
        setError(err.message);
      }
    }

    loadGrid();
  }, []);

  useEffect(() => {
    async function loadStaticData() {
      try {
        const response = await fetch("/data/static_data.json");
        if (!response.ok) {
          throw new Error(`Failed to load static_data.json: ${response.status}`);
        }

        const data = await response.json();
        setStaticData(data);
      } catch (err) {
        console.error(err);
        setError(err.message);
      }
    }

    loadStaticData();
  }, []);

  useEffect(() => {
    async function loadBundle() {
      if (!selectedDate) return;

      try {
        const response = await fetch(`/data/bundles/${selectedDate}.json`);
        if (!response.ok) {
          throw new Error(
            `Failed to load bundle for ${selectedDate}: ${response.status}`
          );
        }

        const data = await response.json();
        setBundleData(data);
      } catch (err) {
        console.error(err);
        setError(err.message);
      }
    }

    loadBundle();
  }, [selectedDate]);

  useEffect(() => {
    async function loadViirs() {
      if (!selectedDate || !showViirs) {
        setViirsData([]);
        return;
      }

      try {
        const response = await fetch(`/data/viirs/${selectedDate}.json`);

        if (response.status === 404) {
          setViirsData([]);
          return;
        }

        const contentType = response.headers.get("content-type") || "";
        if (!response.ok || !contentType.includes("application/json")) {
          if (!response.ok) {
            console.error(
              `Failed to load VIIRS for ${selectedDate}: ${response.status}`
            );
          }
          setViirsData([]);
          return;
        }

        const data = await response.json();
        setViirsData(data);
      } catch (err) {
        console.error(err);
        setViirsData([]);
      }
    }

    loadViirs();
  }, [selectedDate, showViirs]);


  const staticLookup = useMemo(() => {
    if (!staticData) return new Map();

    const lookup = new Map();
    for (const row of staticData) {
      lookup.set(row.cell_id, row);
    }
    return lookup;
  }, [staticData]);

  const dynamicLookup = useMemo(() => {
    if (!bundleData) return new Map();

    const lookup = new Map();
    for (const row of bundleData) {
      lookup.set(row.cell_id, row);
    }
    return lookup;
  }, [bundleData]);

  function getLayerValue(cellId) {
    if (!selectedLayerMeta) return null;

    if (selectedLayerMeta.source === "static") {
      return staticLookup.get(cellId)?.[selectedLayer];
    }

    if (selectedLayerMeta.source === "dynamic") {
      return dynamicLookup.get(cellId)?.[selectedLayer];
    }

    return null;
  }

  function buildSelectedCell(cellId) {
    const staticRow = staticLookup.get(cellId) || {};
    const dynamicRow = dynamicLookup.get(cellId) || {};
    const activeValue = getLayerValue(cellId);

    return {
      cell_id: cellId,
      activeValue,
      ...staticRow,
      ...dynamicRow,
    };
  }

  useEffect(() => {
    if (!selectedCell) return;
    if (selectedCell.cell_id === undefined || selectedCell.cell_id === null) return;
    if (!staticLookup.size) return;
    if (!dynamicLookup.size) return;

    setSelectedCell(buildSelectedCell(selectedCell.cell_id));
  }, [selectedDate, selectedLayer, staticLookup, dynamicLookup]);

  function styleFeature(feature) {
  const cellId = feature?.properties?.cell_id;
  const value = getLayerValue(cellId);

  const dynamicRow = dynamicLookup.get(cellId);
  const hasObservedFire = dynamicRow?.fire === 1;

  return {
    color: hasObservedFire ? "#111827" : "#555",
    weight: hasObservedFire ? 2.5 : 0.4,
    fillColor: getColorForValue(value, selectedLayerMeta),
    fillOpacity: 0.75,
  };
  }


 function formatTooltipValue(value) {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return "No data";
  }

  if (typeof value === "number") {
    return value.toFixed(4);
  }

  return String(value);
}

function onEachFeature(feature, layer) {
  const cellId = feature?.properties?.cell_id;

  layer.on({
    click: () => {
      setSelectedCell(buildSelectedCell(cellId));
    },

    mouseover: () => {
      const selected = buildSelectedCell(cellId);

      layer.setStyle({
        weight: 1.5,
        color: "#000",
      });

      layer.bindTooltip(
        `
          <strong>Cell ${cellId}</strong><br/>
          ${selectedLayerMeta?.label || "Value"}: ${formatTooltipValue(selected.activeValue)}<br/>
          Risk: ${formatTooltipValue(selected.p_fire_tomorrow)}
        `,
        {
          sticky: true,
          direction: "top",
          opacity: 0.95,
          pane: "hoverTooltip",
        }
      );

      layer.openTooltip();
    },

    mouseout: () => {
      layer.closeTooltip();

      layer.setStyle(styleFeature(feature));
    },
  });
}
  const isLoading =
    !gridData || !staticData || (!bundleData && selectedLayerMeta?.source === "dynamic");

  return (
    <div className="map-layout">
      <div className="map-panel">
        <div id="map-capture-source" className="map-wrapper">
          {error && <div className="status error">Error: {error}</div>}
          {isLoading && !error && <div className="status">Loading map data…</div>}

          <MapContainer
            center={[39.0, 22.0]}
            zoom={6}
            scrollWheelZoom={true}
            zoomAnimation={false}
            fadeAnimation={false}
            markerZoomAnimation={false}
            className="map-container"
          >
            <TileLayer
              attribution="Tiles &copy; Esri — Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              crossOrigin="anonymous"
            />

            {gridData && !isLoading && (
              <GeoJSON
                key={`${selectedLayer}-${selectedDate}-${staticData?.length || 0}-${bundleData?.length || 0}`}
                data={gridData}
                style={styleFeature}
                onEachFeature={onEachFeature}
              />
            )}

            {showViirs &&
              viirsData.map((fire, index) => (
                <CircleMarker
                  key={`${selectedDate}-${index}`}
                  center={[fire.lat, fire.lon]}
                  radius={5}
                  pathOptions={{
                    color: "#0b26ad",
                    fillColor: "#2d12fa",
                    fillOpacity: 0.9,
                    weight: 1.5,
                  }}
                >
                  <Tooltip>
                    <strong>VIIRS fire detection</strong>
                    <br />
                    Cell: {fire.cell_id ?? "Unknown"}
                    <br />
                    Confidence: {fire.confidence}
                  </Tooltip>
                </CircleMarker>
              ))}
            <Pane
                name="hoverTooltip"
                style={{
                  zIndex: 900,
                  pointerEvents: "none",
                }}
            />
            <Pane name="labels" style={{ zIndex: 650, pointerEvents: "none" }}>
              {showLabels && (
                <TileLayer
                  attribution="&copy; CARTO, &copy; OpenStreetMap contributors"
                  url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png"
                  crossOrigin="anonymous"
                />
              )}
            </Pane>
          </MapContainer>

          <Legend layerMeta={selectedLayerMeta} />
        </div>
      </div>

      {!exportMode && (
        <div className="side-panel">
          <InfoPanel
            selectedCell={selectedCell}
            selectedLayerMeta={selectedLayerMeta}
            selectedDate={selectedDate}
          />
        </div>
      )}
    </div>
  );
}

export default MapView;