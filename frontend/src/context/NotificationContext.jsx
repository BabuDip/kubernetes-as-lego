import { createContext, useContext, useEffect, useRef, useState } from "react";

const NotificationContext = createContext(null);
const MAX_BACKOFF_MS = 15000;
const TOAST_LIFETIME_MS = 7000;
// Real-time updates always come from the socket; this is purely a safety net for
// extended outages (e.g. a network that blocks websockets outright).
const FALLBACK_POLL_MS = 30000;

export function NotificationProvider({ user, children }) {
  const [toasts, setToasts] = useState([]);
  const [lastEvent, setLastEvent] = useState(null);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef(null);
  const toastTimersRef = useRef(new Map());

  const pushToast = (envelope) => {
    const orderId = envelope.data?.order_id;
    // Group by order so a second update for the same order replaces (not stacks on)
    // the first, resetting its lifetime instead of cluttering the stack.
    const groupKey = orderId || envelope.id;
    const existingTimer = toastTimersRef.current.get(groupKey);
    if (existingTimer) clearTimeout(existingTimer);

    setToasts((prev) => [
      ...prev.filter((t) => t.groupKey !== groupKey),
      { id: envelope.id, groupKey, orderId, message: envelope.data?.message || envelope.type },
    ]);

    const timer = setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.groupKey !== groupKey));
      toastTimersRef.current.delete(groupKey);
    }, TOAST_LIFETIME_MS);
    toastTimersRef.current.set(groupKey, timer);
  };

  useEffect(() => {
    if (!user) return undefined;

    let reconnectTimer;
    let retries = 0;
    let closedByUs = false;

    const connect = () => {
      const protocol = window.location.protocol === "https:" ? "wss" : "ws";
      const socket = new WebSocket(`${protocol}://${window.location.host}/ws/notifications/`);
      socketRef.current = socket;

      socket.onopen = () => {
        const reconnected = retries > 0;
        retries = 0;
        setConnected(true);
        // A dropped connection may have missed events — resync once instead of ever polling.
        if (reconnected) {
          setLastEvent({ type: "connection.resynced", id: crypto.randomUUID(), data: {} });
        }
      };

      socket.onmessage = (event) => {
        const envelope = JSON.parse(event.data);
        setLastEvent(envelope);
        pushToast(envelope);
      };

      socket.onclose = () => {
        setConnected(false);
        if (closedByUs) return;
        const delay = Math.min(1000 * 2 ** retries, MAX_BACKOFF_MS);
        retries += 1;
        reconnectTimer = setTimeout(connect, delay);
      };
    };

    connect();

    return () => {
      closedByUs = true;
      clearTimeout(reconnectTimer);
      socketRef.current?.close();
    };
  }, [user]);

  // Fallback safety net: only nudges consumers to refetch while the socket is down.
  useEffect(() => {
    if (!user) return undefined;
    const interval = setInterval(() => {
      if (!connected) {
        setLastEvent({ type: "poll.fallback", id: crypto.randomUUID(), data: {} });
      }
    }, FALLBACK_POLL_MS);
    return () => clearInterval(interval);
  }, [user, connected]);

  const dismiss = (groupKey) => {
    const timer = toastTimersRef.current.get(groupKey);
    if (timer) clearTimeout(timer);
    toastTimersRef.current.delete(groupKey);
    setToasts((prev) => prev.filter((t) => t.groupKey !== groupKey));
  };

  return (
    <NotificationContext.Provider value={{ toasts, dismiss, lastEvent, connected }}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  return useContext(NotificationContext);
}
