import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useNotifications } from "../context/NotificationContext.jsx";

export default function OrderHistory() {
  const [orders, setOrders] = useState([]);
  const notifications = useNotifications();

  const load = () => api.get("/orders/").then(setOrders);

  useEffect(() => {
    load();
  }, []);

  // Live-refresh on any status push for one of my orders, or after a reconnect resync.
  useEffect(() => {
    if (notifications?.lastEvent) load();
  }, [notifications?.lastEvent]);

  return (
    <div className="page" style={{ maxWidth: 560 }}>
      <h1 className="display" style={{ marginBottom: 16 }}>
        My Orders
      </h1>
      {orders.length === 0 && (
        <div className="empty-state">
          <span className="empty-state-icon">
            <i className="bi bi-receipt" />
          </span>
          <h2>No orders yet</h2>
          <p>Once you place an order, you&apos;ll be able to track it here.</p>
          <Link to="/" className="btn primary">
            Browse the Menu
          </Link>
        </div>
      )}
      {orders.map((order) => (
        <Link
          key={order.id}
          to={`/orders/${order.id}`}
          className="cart-line"
          style={{ textDecoration: "none", color: "inherit" }}
        >
          <div className="cart-line-main">
            <span className="mono">#{order.display_id}</span>
            <div style={{ fontSize: 11.5, color: "var(--slate)" }}>
              {new Date(order.created_at).toLocaleString()}
            </div>
          </div>
          <span className="stamp">{order.status}</span>
          <span className="mono">${order.total}</span>
        </Link>
      ))}
    </div>
  );
}
