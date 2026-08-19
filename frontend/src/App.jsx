import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext.jsx";
import { CartProvider } from "./context/CartContext.jsx";
import { NotificationProvider } from "./context/NotificationContext.jsx";
import Nav from "./components/Nav.jsx";
import ToastStack from "./components/ToastStack.jsx";
import TabBar from "./components/TabBar.jsx";
import Auth from "./pages/Auth.jsx";
import Menu from "./pages/Menu.jsx";
import Cart from "./pages/Cart.jsx";
import Checkout from "./pages/Checkout.jsx";
import OrderTracking from "./pages/OrderTracking.jsx";
import OrderHistory from "./pages/OrderHistory.jsx";
import Account from "./pages/Account.jsx";
import ManagerDashboard from "./pages/manager/Dashboard.jsx";
import ManagerCatalogue from "./pages/manager/Catalogue.jsx";

function RequireAuth({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return null;
  return user ? children : <Navigate to="/login" state={{ from: location }} replace />;
}

function RequireManager({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return null;
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  return user.is_staff ? children : <Navigate to="/" replace />;
}

function RequireGuest({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return null;
  return user ? <Navigate to={location.state?.from?.pathname || "/"} replace /> : children;
}

function Shell() {
  const { user } = useAuth();
  return (
    <NotificationProvider user={user}>
      <Nav />
      <ToastStack />
      <Routes>
        <Route path="/" element={<Menu />} />
        <Route
          path="/login"
          element={
            <RequireGuest>
              <Auth />
            </RequireGuest>
          }
        />
        <Route
          path="/signup"
          element={
            <RequireGuest>
              <Auth />
            </RequireGuest>
          }
        />
        <Route path="/cart" element={<Cart />} />
        <Route
          path="/checkout"
          element={
            <RequireAuth>
              <Checkout />
            </RequireAuth>
          }
        />
        <Route
          path="/orders"
          element={
            <RequireAuth>
              <OrderHistory />
            </RequireAuth>
          }
        />
        <Route
          path="/orders/:id"
          element={
            <RequireAuth>
              <OrderTracking />
            </RequireAuth>
          }
        />
        <Route
          path="/account"
          element={
            <RequireAuth>
              <Account />
            </RequireAuth>
          }
        />
        <Route
          path="/manage"
          element={
            <RequireManager>
              <ManagerDashboard />
            </RequireManager>
          }
        />
        <Route
          path="/manage/catalogue"
          element={
            <RequireManager>
              <ManagerCatalogue />
            </RequireManager>
          }
        />
      </Routes>
      <TabBar />
    </NotificationProvider>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <Shell />
      </CartProvider>
    </AuthProvider>
  );
}
