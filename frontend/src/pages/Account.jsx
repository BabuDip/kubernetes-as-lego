import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext.jsx";
import { timeOfDayGreeting } from "../utils/greeting.js";
import { displayName, roleLabel } from "../utils/user.js";

// Most-ordered item across past orders, by total quantity — a quick "usual order".
function usualOrder(orders) {
  const counts = new Map();
  for (const order of orders) {
    for (const item of order.items) {
      counts.set(item.product_name, (counts.get(item.product_name) || 0) + item.quantity);
    }
  }
  if (counts.size === 0) return null;
  return [...counts.entries()].sort((a, b) => b[1] - a[1])[0][0];
}

export default function Account() {
  const { user, updateProfile } = useAuth();
  const [name, setName] = useState(user.name);
  const [email, setEmail] = useState(user.email);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [busy, setBusy] = useState(false);
  const [orders, setOrders] = useState(null);

  // Order history is scoped to "my orders" server-side, so this is only meaningful
  // for customers — a manager's /orders/ list is the whole cafe's, not just theirs.
  useEffect(() => {
    if (!user.is_staff) api.get("/orders/").then(setOrders);
  }, [user.is_staff]);

  const dirty = name !== user.name || email !== user.email;
  const memberSince = new Date(user.date_joined).toLocaleDateString(undefined, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  const onSubmit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setSuccess(false);
    try {
      await updateProfile({ name, email });
      setSuccess(true);
    } catch (err) {
      setError(err.data?.email?.[0] || err.data?.detail || "Could not save changes.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page" style={{ maxWidth: 480 }}>
      <h1 className="display" style={{ marginBottom: 4 }}>
        {timeOfDayGreeting()}, {displayName(user)}
      </h1>
      <p style={{ color: "var(--slate)", marginTop: 0, marginBottom: 20 }}>
        {roleLabel(user)} · Member since {memberSince}
      </p>

      {error && <div className="form-error">{error}</div>}
      {success && !dirty && (
        <div className="form-error" style={{ background: "var(--pine-s)", color: "var(--pine)" }}>
          Profile updated.
        </div>
      )}

      <form onSubmit={onSubmit}>
        <div className="field">
          <label htmlFor="name">Full name</label>
          <input
            id="name"
            className="input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Your name"
          />
        </div>
        <div className="field">
          <label htmlFor="email">Email address</label>
          <input
            id="email"
            className="input"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <button type="submit" className="btn primary lg" disabled={busy || !dirty}>
          {busy ? "Saving…" : "Save Changes"}
        </button>
      </form>

      {!user.is_staff && (
        <>
          <div className="eyebrow" style={{ marginTop: 28, marginBottom: 8 }}>
            Preferences
          </div>
          <div className="stats" style={{ gridTemplateColumns: "repeat(2, 1fr)" }}>
            <div className="stat">
              <div className="stat-label">Orders Placed</div>
              <div className="stat-value mono">{orders ? orders.length : "—"}</div>
              <div className="stat-sub">all time</div>
            </div>
            <div className="stat">
              <div className="stat-label">Usual Order</div>
              <div className="stat-value" style={{ fontSize: 16 }}>
                {orders ? usualOrder(orders) || "—" : "—"}
              </div>
              <div className="stat-sub">most ordered item</div>
            </div>
          </div>
        </>
      )}

      <div className="eyebrow" style={{ marginTop: 28, marginBottom: 8 }}>
        Payment
      </div>
      <div className="paycard">
        <div className="paycard-top">
          <span>VISA</span>
          <span className="demotag">DEMO</span>
        </div>
        <div className="pan mono">•••• •••• •••• 4242</div>
        <div className="paycard-bot mono">
          <span>{displayName(user) || "Cardholder"}</span>
          <span>12/34</span>
        </div>
      </div>
      <p style={{ fontSize: 11.5, color: "var(--slate)", marginTop: 8 }}>
        Simulated for this demo — payment details aren&apos;t editable here.
      </p>
    </div>
  );
}
