import { useNavigate } from "react-router-dom";
import { useNotifications } from "../context/NotificationContext.jsx";
import { useAuth } from "../context/AuthContext.jsx";

export default function ToastStack() {
  const ctx = useNotifications();
  const { user } = useAuth();
  const navigate = useNavigate();
  if (!ctx || ctx.toasts.length === 0) return null;

  const openDetail = (t) => {
    if (t.orderId) {
      navigate(user?.is_staff ? `/manage?order=${t.orderId}` : `/orders/${t.orderId}`);
    }
    ctx.dismiss(t.groupKey);
  };

  return (
    <div className="toasts">
      {ctx.toasts.map((t) => (
        <div key={t.groupKey} className="toast">
          <button type="button" className="toast-body" onClick={() => openDetail(t)}>
            <i className="bi bi-bell-fill" />
            <span className="toast-message">{t.message}</span>
          </button>
          <button
            type="button"
            className="toast-close"
            aria-label="Dismiss"
            onClick={(e) => {
              e.stopPropagation();
              ctx.dismiss(t.groupKey);
            }}
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
