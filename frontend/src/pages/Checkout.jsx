import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useCart } from "../context/CartContext.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { PICKUP_LABELS } from "../utils/pickup.js";

export default function Checkout() {
  const { lines, total, clear } = useCart();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [pickup, setPickup] = useState("asap");
  const [note, setNote] = useState("");
  const [paying, setPaying] = useState(false);
  const [error, setError] = useState(null);

  // Only bounce back to /cart if it's empty before checkout even starts —
  // not mid-payment, when clear() legitimately empties it after a successful order.
  useEffect(() => {
    if (lines.length === 0 && !paying) {
      navigate("/cart");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lines.length]);

  if (lines.length === 0) return null;

  const onPay = async () => {
    setPaying(true);
    setError(null);
    try {
      const order = await api.post("/orders/", {
        items: lines.map((l) => ({
          product_id: l.product.id,
          quantity: l.quantity,
          modifiers: l.modifiers,
        })),
        pickup_preference: pickup,
        note,
      });
      // Navigate away from /checkout first — clearing the cart re-renders this page,
      // and its empty-cart guard would otherwise redirect to /cart before we get there.
      navigate(`/orders/${order.id}`, { state: { justPlaced: true } });
      clear();
    } catch (err) {
      setError(err.data?.detail || "Payment simulation failed — please try again.");
    } finally {
      setPaying(false);
    }
  };

  return (
    <div className="page" style={{ maxWidth: 640 }}>
      <h1 className="display" style={{ marginBottom: 16 }}>
        Checkout
      </h1>
      {error && <div className="form-error">{error}</div>}

      <fieldset className="field">
        <legend>Pickup time</legend>
        <div className="chips">
          {Object.entries(PICKUP_LABELS).map(([value, label]) => (
            <button
              key={value}
              type="button"
              className={`chip ${pickup === value ? "on" : ""}`}
              onClick={() => setPickup(value)}
            >
              {label}
            </button>
          ))}
        </div>
      </fieldset>

      <div className="field">
        <label htmlFor="note">Note for the barista (optional)</label>
        <input
          id="note"
          className="input"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="e.g. no sugar, extra hot"
        />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 20 }}>
        <div>
          <div className="eyebrow" style={{ marginBottom: 8 }}>
            Order Summary
          </div>
          {lines.map((l) => (
            <div key={l.key} className="drow">
              <span>
                {l.quantity} × {l.product.name}
                {l.modifiersLabel && <span style={{ color: "var(--slate)" }}> ({l.modifiersLabel})</span>}
              </span>
              <span className="mono">${(l.unitPrice * l.quantity).toFixed(2)}</span>
            </div>
          ))}
          <div className="drow strong">
            <span>Total</span>
            <span className="mono">${total.toFixed(2)}</span>
          </div>
        </div>

        <div>
          <div className="eyebrow" style={{ marginBottom: 8 }}>
            Payment
          </div>
          <div className="paycard">
            <div className="paycard-top">
              <span>VISA</span>
              <span className="demotag">DEMO</span>
            </div>
            <div className="pan mono">4242 4242 4242 4242</div>
            <div className="paycard-bot mono">
              <span>{user?.name || "Cardholder"}</span>
              <span>12/34</span>
              <span>CVC 123</span>
            </div>
          </div>
          <p style={{ fontSize: 11.5, color: "var(--slate)", marginTop: 8 }}>
            Simulated for this demo — no real charge occurs.
          </p>
          <button type="button" className="btn success lg" disabled={paying} onClick={onPay}>
            {paying ? "Processing…" : `Pay $${total.toFixed(2)} & Place Order`}
          </button>
        </div>
      </div>
    </div>
  );
}
