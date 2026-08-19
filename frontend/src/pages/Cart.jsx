import { Link, useNavigate } from "react-router-dom";
import { useCart } from "../context/CartContext.jsx";

export default function Cart() {
  const { lines, adjust, remove, total } = useCart();
  const navigate = useNavigate();

  if (lines.length === 0) {
    return (
      <div className="page" style={{ maxWidth: 560 }}>
        <h1 className="display" style={{ marginBottom: 16 }}>
          Your Cart
        </h1>
        <div className="empty-state">
          <span className="empty-state-icon">
            <i className="bi bi-bag" />
          </span>
          <h2>Your cart is empty</h2>
          <p>Add something from the menu and it&apos;ll show up here, ready for checkout.</p>
          <Link to="/" className="btn primary">
            Browse the Menu
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="page" style={{ maxWidth: 560 }}>
      <h1 className="display" style={{ marginBottom: 16 }}>
        Your Cart
      </h1>
      {lines.map((line) => (
        <div key={line.key} className="cart-line">
          <div className="cart-line-main">
            <div style={{ fontWeight: 600 }}>{line.product.name}</div>
            {line.modifiersLabel && <div className="cart-line-mods">{line.modifiersLabel}</div>}
            <div className="mono" style={{ fontSize: 11.5, color: "var(--slate)" }}>
              ${line.unitPrice.toFixed(2)} each
            </div>
          </div>
          <div className="stepper">
            <button type="button" onClick={() => adjust(line.key, -1)}>
              −
            </button>
            <span className="mono">{line.quantity}</span>
            <button type="button" onClick={() => adjust(line.key, 1)}>
              +
            </button>
          </div>
          <div className="cart-line-price mono">${(line.unitPrice * line.quantity).toFixed(2)}</div>
          <button type="button" className="btn ghost" onClick={() => remove(line.key)}>
            Remove
          </button>
        </div>
      ))}
      <div className="totals">
        <span>Total</span>
        <span className="mono">${total.toFixed(2)}</span>
      </div>
      <button
        type="button"
        className="btn primary lg"
        style={{ marginTop: 16 }}
        onClick={() => navigate("/checkout")}
      >
        Proceed to Checkout
      </button>
    </div>
  );
}
