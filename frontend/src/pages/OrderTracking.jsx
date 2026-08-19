import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { useNotifications } from "../context/NotificationContext.jsx";
import { PICKUP_LABELS } from "../utils/pickup.js";
import LiveDuration from "../components/LiveDuration.jsx";

const STEPS = ["received", "preparing", "ready", "completed"];

export default function OrderTracking() {
  const { id } = useParams();
  const [order, setOrder] = useState(null);
  const notifications = useNotifications();

  const load = () => api.get(`/orders/${id}/`).then(setOrder);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  // Refetch when a websocket event concerns this order, after a reconnect resync, or
  // via the disconnect-only fallback poll — never a blind interval.
  useEffect(() => {
    const event = notifications?.lastEvent;
    if (!event) return;
    const relevant =
      event.type === "connection.resynced" || event.type === "poll.fallback" || event.data?.order_id === id;
    if (relevant) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [notifications?.lastEvent]);

  if (!order) return <div className="page">Loading…</div>;

  const currentIndex = STEPS.indexOf(order.status);

  return (
    <div className="page" style={{ maxWidth: 480 }}>
      <div className="docket">
        <div className="docket-head">
          <span className="big mono">#{order.display_id}</span>
          <span className="stamp">{order.status.toUpperCase()}</span>
        </div>

        <div className="rail">
          {STEPS.map((step, i) => (
            <>
              {i > 0 && <div className={`seg2 ${i <= currentIndex ? "done" : ""}`} />}
              <div
                key={step}
                className={`node ${i < currentIndex ? "done" : ""} ${i === currentIndex ? "live" : ""}`}
              />
            </>
          ))}
        </div>
        <div className="rail-labels">
          {STEPS.map((step, i) => (
            <span key={step} className={i === currentIndex ? "on" : ""}>
              {step}
            </span>
          ))}
        </div>

        <div className="perf" />
        <div className="drow soft">
          <span>Placed</span>
          <span>{new Date(order.created_at).toLocaleString()}</span>
        </div>
        <div className="drow soft">
          <span>Pickup</span>
          <span>{PICKUP_LABELS[order.pickup_preference]}</span>
        </div>
        {order.note && (
          <div className="drow soft">
            <span>Note</span>
            <span>{order.note}</span>
          </div>
        )}
        <div className="drow soft">
          <span>{order.status === "completed" ? "Completed" : "Waiting"}</span>
          {order.status === "completed" ? (
            <span className="mono">{new Date(order.updated_at).toLocaleString()}</span>
          ) : (
            <LiveDuration seconds={order.age_seconds} />
          )}
        </div>

        <div className="perf" />
        {order.items.map((item) => (
          <div key={item.id} className="drow">
            <span>
              {item.quantity} × {item.product_name}
              {item.modifiers_label && (
                <span style={{ color: "var(--slate)" }}> ({item.modifiers_label})</span>
              )}
            </span>
            <span className="mono">${item.subtotal}</span>
          </div>
        ))}
        <div className="drow strong">
          <span>Total</span>
          <span className="mono">${order.total}</span>
        </div>
        {order.status !== "completed" && order.ahead_count > 0 && (
          <div className="drow soft">
            <span>{order.ahead_count} order(s) ahead of you</span>
          </div>
        )}
      </div>
      <div className="tear" />
    </div>
  );
}
