import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

// One page for both flows — a tab switch, not a navigation, feels lighter than two
// disconnected forms, and avoids duplicating this layout/error-handling twice.
export default function Auth() {
  const { login, signup } = useAuth();
  const location = useLocation();
  const isRegister = location.pathname === "/signup";
  const returnTo = location.state?.from?.pathname;

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      // Login/signup update the user in context; RequireGuest reacts to that and
      // redirects to wherever this page was reached from (or "/" by default).
      if (isRegister) await signup(email, password, password2);
      else await login(email, password);
    } catch (err) {
      setError(
        isRegister
          ? Object.values(err.data || {})
              .flat()
              .join(" ") || "Sign up failed."
          : err.data?.detail || "Sign in failed.",
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="form-card">
      {returnTo && (
        <p style={{ marginTop: 0, color: "var(--slate)", fontSize: 13 }}>
          Sign in to bring your existing profile, or register to track this order.
        </p>
      )}
      <div className="auth-tabs">
        <Link to="/login" className={`auth-tab ${isRegister ? "" : "on"}`}>
          Sign In
        </Link>
        <Link to="/signup" className={`auth-tab ${isRegister ? "on" : ""}`}>
          Register
        </Link>
      </div>

      {error && <div className="form-error">{error}</div>}

      <form onSubmit={onSubmit}>
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
        <div className="field">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            className="input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {isRegister && (
          <div className="field">
            <label htmlFor="password2">Confirm password</label>
            <input
              id="password2"
              className="input"
              type="password"
              value={password2}
              onChange={(e) => setPassword2(e.target.value)}
              required
            />
          </div>
        )}
        <button type="submit" className="btn primary lg" disabled={busy}>
          {busy ? (isRegister ? "Signing up…" : "Signing in…") : isRegister ? "Create Account" : "Sign In"}
        </button>
      </form>
    </div>
  );
}
