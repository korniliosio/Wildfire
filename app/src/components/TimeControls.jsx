import { useEffect, useMemo, useState, useRef } from "react";
import {SlArrowLeft, SlArrowRight} from "react-icons/sl";
import { FaPlay , FaPause } from "react-icons/fa";
import { MdCalendarMonth } from "react-icons/md";
function TimeControls({ dates, selectedDateIndex, onDateIndexChange }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(500);
  const dateInputRef = useRef(null);
  const hasDates = dates && dates.length > 0;

  const selectedDate = useMemo(() => {
    if (!hasDates) return "";
    return dates[selectedDateIndex];
  }, [dates, selectedDateIndex, hasDates]);

  useEffect(() => {
    if (!isPlaying || !hasDates) return;

    const intervalId = setInterval(() => {
      onDateIndexChange((currentIndex) => {
        if (currentIndex >= dates.length - 1) return 0;
        return currentIndex + 1;
      });
    }, playbackSpeed);

    return () => clearInterval(intervalId);
  }, [isPlaying, hasDates, dates.length, playbackSpeed, onDateIndexChange]);

  function goPrevious() {
    if (!hasDates) return;
    onDateIndexChange(Math.max(0, selectedDateIndex - 1));
  }

  function goNext() {
    if (!hasDates) return;
    onDateIndexChange(Math.min(dates.length - 1, selectedDateIndex + 1));
  }

  function handleCalendarChange(event) {
    const index = dates.indexOf(event.target.value);
    if (index >= 0) onDateIndexChange(index);
  }


  function openDatePicker() {
    if (!dateInputRef.current) return;

    if (dateInputRef.current.showPicker) {
      dateInputRef.current.showPicker();
    } else {
      dateInputRef.current.click();
    }
  }

  return (
    <div className="timeline-dock">
      <div className="timeline-dock-main">
          <div className="timeline-date-pill" onClick={openDatePicker} >
            <span>{selectedDate || "No date"}</span>

            <MdCalendarMonth className="timeline-calendar-icon" />

            <input
              ref={dateInputRef}
              type="date"
              value={selectedDate || ""}
              onChange={handleCalendarChange}
              min={dates[0]}
              max={dates[dates.length - 1]}
              className="timeline-hidden-date"
            />
          </div>

        <input
          className="timeline-range"
          type="range"
          min={0}
          max={hasDates ? dates.length - 1 : 0}
          value={selectedDateIndex}
          onChange={(e) => onDateIndexChange(Number(e.target.value))}
          disabled={!hasDates}
        />

        <div className="timeline-actions">
          <button onClick={goPrevious} disabled={!hasDates} title="Previous day">
            <SlArrowLeft />
          </button>

          <button onClick={goNext} disabled={!hasDates} title="Next day">
            <SlArrowRight />
          </button>

          <button
            className="timeline-play"
            onClick={() => setIsPlaying((v) => !v)}
            disabled={!hasDates}
          >
            {isPlaying ? (
              <>
                <FaPause className="timeline-pause-icon" />
                <span>Pause</span>
              </>
            ) : (
              <>
              <FaPlay className="timeline-play-icon" />
              <span>Play</span>
              </>
            )}
          </button>

          <select
            className="timeline-speed"
            value={playbackSpeed}
            onChange={(e) => setPlaybackSpeed(Number(e.target.value))}
            title="Playback speed"
          >
            <option value={1200}>0.5×</option>
            <option value={800}>1×</option>
            <option value={500}>2×</option>
            <option value={250}>4×</option>
            <option value={120}>8×</option>
          </select>
        </div>
      </div>
    </div>
  );
}

export default TimeControls;