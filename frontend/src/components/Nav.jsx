import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { displayName, roleLabel } from "../utils/user.js";

export default function Nav() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const inManage = location.pathname.startsWith("/manage");
  const [menuOpen, setMenuOpen] = useState(false);
  const [menuPathname, setMenuPathname] = useState(location.pathname);
  const menuRef = useRef(null);

  // Close the dropdown on navigation — adjusting state during render, not in an
  // effect, since it only needs to happen when the route actually changes.
  if (location.pathname !== menuPathname) {
    setMenuPathname(location.pathname);
    setMenuOpen(false);
  }

  useEffect(() => {
    if (!menuOpen) return undefined;
    const onOutsideClick = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) setMenuOpen(false);
    };
    document.addEventListener("mousedown", onOutsideClick);
    return () => document.removeEventListener("mousedown", onOutsideClick);
  }, [menuOpen]);

  const signOut = async () => {
    await logout();
    navigate("/");
  };

  return (
    <nav className="topbar">
      <div className="topbar-inner">
        <Link to="/" className="topbar-brand">
          <span className="mark">Q</span> QLess Cafe
        </Link>

        {user ? (
          <div className="profile-menu" ref={menuRef}>
            <button
              type="button"
              className="nav-user"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((open) => !open)}
            >
              <span className="nav-user-avatar">{displayName(user).charAt(0).toUpperCase()}</span>
              <span className="nav-user-text">
                <span className="nav-user-name">{displayName(user)}</span>
                <span className="nav-user-role">{roleLabel(user)}</span>
              </span>
              <i className={`bi bi-chevron-down profile-caret ${menuOpen ? "open" : ""}`} />
            </button>

            {menuOpen && (
              <div className="profile-dropdown">
                {user.is_staff && inManage && (
                  <>
                    <Link
                      className={`dropdown-item ${location.pathname === "/manage" ? "active" : ""}`}
                      to="/manage"
                    >
                      <i className="bi bi-kanban" /> Service Board
                    </Link>
                    <Link
                      className={`dropdown-item ${location.pathname === "/manage/catalogue" ? "active" : ""}`}
                      to="/manage/catalogue"
                    >
                      <i className="bi bi-egg-fried" /> Catalogue
                    </Link>
                    <Link className="dropdown-item" to="/">
                      <i className="bi bi-arrow-left" /> Back to Menu
                    </Link>
                    <div className="dropdown-sep" />
                  </>
                )}
                {user.is_staff && !inManage && (
                  <>
                    <Link className="dropdown-item" to="/manage">
                      <i className="bi bi-speedometer2" /> Manage
                    </Link>
                    <div className="dropdown-sep" />
                  </>
                )}
                <Link className="dropdown-item" to="/account">
                  <i className="bi bi-person-circle" /> Account
                </Link>
                <button type="button" className="dropdown-item" onClick={signOut}>
                  <i className="bi bi-box-arrow-right" /> Sign Out
                </button>
              </div>
            )}
          </div>
        ) : (
          <Link className="nav-link" to="/login">
            Sign In or Register
          </Link>
        )}
      </div>
    </nav>
  );
}
