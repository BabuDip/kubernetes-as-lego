import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../../api/client";
import { PICKUP_LABELS, PICKUP_TONE } from "../../utils/pickup.js";
import { useAuth } from "../../context/AuthContext.jsx";
import { useNotifications } from "../../context/NotificationContext.jsx";
import { timeOfDayGreeting } from "../../utils/greeting.js";
import { displayName } from "../../utils/user.js";
import LiveDuration, { formatDuration } from "../../components/LiveDuration.jsx";
import Drawer from "../../components/Drawer.jsx";

const COLUMN_LABELS = {
  received: "Received",
  preparing: "Preparing",
  ready: "Ready",
  completed: "Completed",
};
const NEXT_LABEL = { received: "Start Preparing", preparing: "Mark Ready", ready: "Complete" };
const STEPS = ["received", "preparing", "ready", "completed"];

function ageClass(order) {
  if (order.age_level === "late") return "age-late";
  if (order.age_level === "warn") return "age-warn";
  return "age-ok";
}

// Isolated so its per-second tick doesn't re-render the whole board.
function LiveClock() {
  const { user } = useAuth();
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div>
      <div className="eyebrow">
        {timeOfDayGreeting(now)}, {user ? displayName(user) : "Manager"} ·{" "}
        {now.toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" })}
      </div>
      <h1 className="display">
        Service Board{" "}
        <span className="mono clocknow">
          {now.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}
        </span>
      </h1>
    </div>
  );
}

export default function ManagerDashboard() {
  const [stats, setStats] = useState(null);
  const [board, setBoard] = useState({});
  const [selected, setSelected] = useState(null);
  const [freshIds, setFreshIds] = useState(() => new Set());
  const [demoMode, setDemoMode] = useState(false);
  const notifications = useNotifications();
  const [searchParams, setSearchParams] = useSearchParams();
  const boardRef = useRef(board);

  const load = () => {
    api.get("/orders/stats/").then(setStats);
    api.get("/orders/board/").then(setBoard);
  };

  useEffect(() => {
    load();
  }, []);

  // No polling: the board is driven entirely by order.created / order.status_changed
  // events over the websocket (plus a one-off resync/fallback nudge when it drops).
  useEffect(() => {
    if (notifications?.lastEvent) load();
  }, [notifications?.lastEvent]);

  // Flash a freshly-arrived order's card for a few seconds so it's impossible to miss.
  useEffect(() => {
    const event = notifications?.lastEvent;
    const orderId = event?.data?.order_id;
    if (event?.type !== "order.created" || !orderId) return undefined;
    // Reacting to a websocket event, not deriving state from props/state.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setFreshIds((prev) => new Set(prev).add(orderId));
    const timer = setTimeout(() => {
      setFreshIds((prev) => {
        const next = new Set(prev);
        next.delete(orderId);
        return next;
      });
    }, 3200);
    return () => clearTimeout(timer);
  }, [notifications?.lastEvent]);

  // Clicking a toast can deep-link straight to an order's detail via ?order=.
  useEffect(() => {
    const orderId = searchParams.get("order");
    if (!orderId) return;
    const found = Object.values(board)
      .flat()
      .find((o) => o.id === orderId);
    if (found) {
      // Reacting to a URL param on mount/change, not deriving state from props/state.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSelected(found);
      setSearchParams({}, { replace: true });
    }
  }, [board, searchParams, setSearchParams]);

  const advance = async (orderId) => {
    await api.post(`/orders/${orderId}/advance/`, {});
    load();
    setSelected((current) => (current?.id === orderId ? null : current));
  };

  useEffect(() => {
    boardRef.current = board;
  }, [board]);

  // Demo mode: purely client-side — no backend flag or bot user, just this tab
  // repeatedly calling the same /advance/ endpoint a manager's click would, working
  // the board oldest-first so it reads like a person triaging the queue rather than
  // a fixed script. Depending only on demoMode (not board/advance) keeps the pacing
  // steady instead of restarting the timer on every websocket-driven board refresh.
  useEffect(() => {
    if (!demoMode) return undefined;
    let timer;
    const tick = async () => {
      const eligible = ["received", "preparing", "ready"].flatMap((status) => boardRef.current[status] || []);
      if (eligible.length > 0) {
        const target = [...eligible].sort((a, b) => b.age_seconds - a.age_seconds)[0];
        try {
          await advance(target.id);
        } catch {
          // Order likely already moved on (e.g. a real manager also clicked it) — retry next tick.
        }
      }
      timer = setTimeout(tick, 6000 + Math.random() * 5000);
    };
    timer = setTimeout(tick, 3000 + Math.random() * 3000);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [demoMode]);

  return (
    <div className="page">
      <div className="mtop">
        <LiveClock />
        <div className="demo-toggle">
          {demoMode && (
            <span className="demo-toggle-live">
              <span className="demo-toggle-dot" />
              Auto-triaging
            </span>
          )}
          <span>Demo Mode</span>
          <button
            type="button"
            role="switch"
            aria-checked={demoMode}
            className="demo-toggle-switch"
            onClick={() => setDemoMode((on) => !on)}
          >
            <span className="sr-only">Toggle demo mode</span>
          </button>
        </div>
      </div>

      {stats && (
        <div className="stats">
          <div className="stat">
            <div className="stat-label">Orders Today</div>
            <div className="stat-value mono">{stats.orders_today}</div>
          </div>
          <div className={`stat ${stats.pending > 5 ? "tone-crema" : ""}`}>
            <div className="stat-label">In The Queue</div>
            <div className="stat-value mono">{stats.pending}</div>
            <div className="stat-sub">
              {stats.oldest_wait_seconds != null ? (
                <>
                  oldest waiting <LiveDuration seconds={stats.oldest_wait_seconds} />
                </>
              ) : (
                "all clear"
              )}
            </div>
          </div>
          <div className={`stat ${stats.ready > 2 ? "tone-pine" : ""}`}>
            <div className="stat-label">Waiting At Counter</div>
            <div className="stat-value mono">{stats.ready}</div>
            <div className="stat-sub">{stats.ready > 0 ? "hand these over" : "nothing sitting"}</div>
          </div>
          <div className="stat">
            <div className="stat-label">Avg Make Time</div>
            <div className="stat-value mono">{formatDuration(stats.avg_make_seconds)}</div>
            <div className="stat-sub">today&apos;s completed orders</div>
          </div>
          <div className="stat">
            <div className="stat-label">Revenue Today</div>
            <div className="stat-value mono">${stats.revenue_today}</div>
            <div className="stat-sub">{stats.taken_today} taken · card only</div>
          </div>
        </div>
      )}

      <div className="board">
        {Object.entries(COLUMN_LABELS).map(([status, label]) => (
          <div key={status} className="col">
            <div className={`col-head col-head-${status}`}>
              <span>{label}</span>
              <span className="mono">{(board[status] || []).length}</span>
            </div>
            <div className="col-body">
              {(board[status] || []).map((order) => (
                <div key={order.id} className={`ocard ${freshIds.has(order.id) ? "ocard-flash" : ""}`}>
                  <div className={`age-bar ${ageClass(order)}`} />
                  <button type="button" className="ocard-body ocard-hit" onClick={() => setSelected(order)}>
                    <div className="ocard-top">
                      <span className="mono" style={{ fontWeight: 600 }}>
                        #{order.display_id}
                      </span>
                      <span className={`wait-pill ${ageClass(order)}`}>
                        <LiveDuration seconds={order.age_seconds} frozen={status === "completed"} />
                      </span>
                    </div>
                    <div className="ocard-who">
                      <span className="ocard-who-name">{order.customer_name || "Customer"}</span>
                      <span className={`pickup-badge ${PICKUP_TONE[order.pickup_preference]}`}>
                        {PICKUP_LABELS[order.pickup_preference]}
                      </span>
                    </div>
                    <ul className="ocard-items">
                      {order.items.map((item) => (
                        <li key={item.id}>
                          {item.quantity} × {item.product_name}
                          {item.modifiers_label && (
                            <span style={{ fontWeight: 400, color: "var(--slate)" }}>
                              {" "}
                              ({item.modifiers_label})
                            </span>
                          )}
                        </li>
                      ))}
                    </ul>
                    {order.note && <div className="ocard-note">{order.note}</div>}
                  </button>
                  {NEXT_LABEL[status] && (
                    <button type="button" className="ocard-cta" onClick={() => advance(order.id)}>
                      {NEXT_LABEL[status]} →
                    </button>
                  )}
                </div>
              ))}
              {(board[status] || []).length === 0 && (
                <p style={{ fontSize: 11.5, color: "var(--slate)", textAlign: "center" }}>Nothing here.</p>
              )}
            </div>
          </div>
        ))}
      </div>

      {selected && (
        <Drawer
          title={`#${selected.display_id}`}
          subtitle={`${selected.customer_name || "Customer"} · ${PICKUP_LABELS[selected.pickup_preference]}`}
          onClose={() => setSelected(null)}
          footer={
            NEXT_LABEL[selected.status] && (
              <button type="button" className="btn primary lg" onClick={() => advance(selected.id)}>
                {NEXT_LABEL[selected.status]} →
              </button>
            )
          }
        >
          <div className="docket flat">
            {selected.items.map((item) => (
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
            {selected.note && (
              <div className="drow soft">
                <span>Note</span>
                <span>{selected.note}</span>
              </div>
            )}
            <div className="perf" />
            <div className="drow strong">
              <span>Total</span>
              <span className="mono">${selected.total}</span>
            </div>
            <div className="drow soft">
              <span>Placed</span>
              <span>{new Date(selected.created_at).toLocaleString()}</span>
            </div>
            <div className="drow soft">
              <span>{selected.status === "completed" ? "Completed" : "Waiting"}</span>
              {selected.status === "completed" ? (
                <span className="mono">{new Date(selected.updated_at).toLocaleString()}</span>
              ) : (
                <LiveDuration seconds={selected.age_seconds} />
              )}
            </div>
          </div>

          <div className="rail" style={{ marginTop: 24 }}>
            {STEPS.map((step, i) => (
              <>
                {i > 0 && (
                  <div className={`seg2 ${selected.status_steps[i].state !== "pending" ? "done" : ""}`} />
                )}
                <div
                  key={step}
                  className={`node ${selected.status_steps[i].state === "done" ? "done" : ""} ${selected.status_steps[i].state === "current" ? "live" : ""}`}
                />
              </>
            ))}
          </div>
          <div className="rail-labels">
            {STEPS.map((step, i) => (
              <span key={step} className={selected.status_steps[i].state !== "pending" ? "on" : ""}>
                {COLUMN_LABELS[step]}
              </span>
            ))}
          </div>
        </Drawer>
      )}
    </div>
  );
}
