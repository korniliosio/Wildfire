import { useEffect, useMemo, useState } from "react";

function TimeControls({ dates, selectedDateIndex, onDateIndexChange }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(500);

  const hasDates = dates && dates.length > 0;

  const selectedDate = useMemo(() => {
    if (!hasDates) return "";
    return dates[selectedDateIndex];
  }, [dates, selectedDateIndex, hasDates]);

  useEffect(() => {
    if (!isPlaying || !hasDates) return;

    const intervalId = setInterval(() => {
      onDateIndexChange((currentIndex) =>
        currentIndex >= dates.length - 1 ? 0 : currentIndex + 1
      );
    }, playbackSpeed);

    return () => clearInterval(intervalId);
  }, [isPlaying, hasDates, dates.length, playbackSpeed, onDateIndexChange]);

  function handleDateChange(event) {
    const index = dates.indexOf(event.target.value);
    if (index >= 0) onDateIndexChange(index);
  }

  return (
    <div className="time-controls">
      <div className="timeline-date-bar">
        <button
          className="timeline-arrow"
          onClick={() => onDateIndexChange(Math.max(0, selectedDateIndex - 1))}
          disabled={!hasDates}
          title="Previous day"
        >
          ◀
        </button>

        <input
          className="timeline-date-input"
          type="date"
          value={selectedDate || ""}
          onChange={handleDateChange}
          min={dates[0]}
          max={dates[dates.length - 1]}
          disabled={!hasDates}
        />

        <button
          className="timeline-arrow"
          onClick={() =>
            onDateIndexChange(Math.min(dates.length - 1, selectedDateIndex + 1))
          }
          disabled={!hasDates}
          title="Next day"
        >
          ▶
        </button>
      </div>

      <div className="timeline-play-row">
        <button
          className="timeline-icon-button"
          onClick={() => setIsPlaying((v) => !v)}
          disabled={!hasDates}
          title={isPlaying ? "Pause" : "Play"}
        >
          {isPlaying ? "⏸" : "▶"}
        </button>

        <div className="speed-segment">
          <button
            className={playbackSpeed === 1000 ? "active" : ""}
            onClick={() => setPlaybackSpeed(1000)}
            title="Slow"
          >
            1×
          </button>
          <button
            className={playbackSpeed === 500 ? "active" : ""}
            onClick={() => setPlaybackSpeed(500)}
            title="Normal"
          >
            2×
          </button>
          <button
            className={playbackSpeed === 200 ? "active" : ""}
            onClick={() => setPlaybackSpeed(200)}
            title="Fast"
          >
            4×
          </button>
        </div>
      </div>

      <input
        className="time-slider"
        type="range"
        min={0}
        max={hasDates ? dates.length - 1 : 0}
        value={selectedDateIndex}
        onChange={(e) => onDateIndexChange(Number(e.target.value))}
        disabled={!hasDates}
      />
    </div>
  );
}

export default TimeControls;