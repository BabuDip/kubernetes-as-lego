import { useEffect } from "react";

// Shared right-side detail/edit panel — used for the manager's order detail view
// and the catalogue's create/edit product form, so "opening something for detail
// or editing" looks and behaves the same everywhere in the app.
export default function Drawer({ title, subtitle, onClose, children, footer }) {
  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <div className="drawerwrap">
      {/* Click-to-dismiss convenience layer; Escape (above) and the Close button cover keyboard use. */}
      <div className="backdrop" aria-hidden="true" onClick={onClose} />
      <aside className="drawer" role="dialog" aria-modal="true" aria-label={title}>
        <div className="drawer-head">
          <div>
            {subtitle && <div className="eyebrow">{subtitle}</div>}
            <h2 className="display" style={{ fontSize: 19 }}>
              {title}
            </h2>
          </div>
          <button type="button" className="sheet-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
        <div className="drawer-body">{children}</div>
        {footer && (
          <div className="sheet-foot" style={{ marginTop: 0 }}>
            {footer}
          </div>
        )}
      </aside>
    </div>
  );
}
