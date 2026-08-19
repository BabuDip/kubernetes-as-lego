import { useEffect, useState } from "react";

export function formatDuration(totalSeconds) {
  if (totalSeconds == null) return "—";
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.floor(totalSeconds % 60);
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

// Ticks locally from a server-supplied base so wait/elapsed times stay live
// without ever polling — only this small span re-renders each second.
export default function LiveDuration({ seconds, frozen = false, className = "mono" }) {
  const [prevSeconds, setPrevSeconds] = useState(seconds);
  const [elapsed, setElapsed] = useState(seconds);

  // Reset the running total when the server sends a new base value for this span.
  if (seconds !== prevSeconds) {
    setPrevSeconds(seconds);
    setElapsed(seconds);
  }

  useEffect(() => {
    if (frozen || seconds == null) return undefined;
    const timer = setInterval(() => setElapsed((current) => (current ?? seconds) + 1), 1000);
    return () => clearInterval(timer);
  }, [seconds, frozen]);

  return <span className={className}>{formatDuration(elapsed)}</span>;
}
