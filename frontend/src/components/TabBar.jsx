import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useCart } from "../context/CartContext.jsx";
import { useNotifications } from "../context/NotificationContext.jsx";

const TABS = [
  { to: "/", label: "Menu", icon: "cup-hot-fill", match: (p) => p === "/" },
  { to: "/cart", label: "Cart", icon: "bag-check-fill", match: (p) => p === "/cart" || p === "/checkout" },
  { to: "/orders", label: "My Orders", icon: "receipt", match: (p) => p.startsWith("/orders") },
];

// Mobile-first primary nav for customers, cart included so there's a single
// bottom bar rather than a separate floating pill competing for space.
export default function TabBar() {
  const { count } = useCart();
  const notifications = useNotifications();
  const location = useLocation();
  const [unseenOrders, setUnseenOrders] = useState(0);
  const lastSeenEventId = useRef(null);

  // Flash the Orders tab when one of the customer's orders updates while they're
  // looking at something else — the toast alone is easy to miss if it's not visible.
  useEffect(() => {
    const event = notifications?.lastEvent;
    if (!event || event.id === lastSeenEventId.current || !event.data?.order_id) return;
    lastSeenEventId.current = event.id;
    if (!location.pathname.startsWith("/orders")) {
      // Reacting to a websocket event, not deriving state from props/state.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setUnseenOrders((n) => n + 1);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [notifications?.lastEvent]);

  useEffect(() => {
    if (location.pathname.startsWith("/orders")) {
      // Reacting to route changes, not deriving state from props/state.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setUnseenOrders(0);
    }
  }, [location.pathname]);

  if (location.pathname.startsWith("/manage")) return null;

  return (
    <nav className="tabbar">
      {TABS.map((tab) => (
        <Link key={tab.to} to={tab.to} className={`tab ${tab.match(location.pathname) ? "on" : ""}`}>
          <span className="tab-icon">
            <i className={`bi bi-${tab.icon}`} />
            {tab.to === "/cart" && count > 0 && <span className="tab-badge mono">{count}</span>}
            {tab.to === "/orders" && unseenOrders > 0 && (
              <span className="tab-badge tab-badge-pulse mono">{unseenOrders}</span>
            )}
          </span>
          <span>{tab.label}</span>
        </Link>
      ))}
    </nav>
  );
}
