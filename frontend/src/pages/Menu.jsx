import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext.jsx";
import { useCart } from "../context/CartContext.jsx";
import ItemSheet from "../components/ItemSheet.jsx";
import CategoryTabs from "../components/CategoryTabs.jsx";
import { timeOfDayGreeting } from "../utils/greeting.js";
import { displayName } from "../utils/user.js";

export default function Menu() {
  const { user } = useAuth();
  const { add } = useCart();
  const [categories, setCategories] = useState([]);
  const [modifierGroups, setModifierGroups] = useState({});
  const [activeCategoryId, setActiveCategoryId] = useState("all");
  const [openProduct, setOpenProduct] = useState(null);

  useEffect(() => {
    api.get("/categories/").then(setCategories);
    api.get("/modifier-groups/").then(setModifierGroups);
  }, []);

  const shownCategories =
    activeCategoryId === "all" ? categories : categories.filter((c) => c.id === activeCategoryId);

  return (
    <div className="page">
      <div className="hero">
        <div>
          <h1 className="display">{user ? `${timeOfDayGreeting()}, ${displayName(user)}` : "QLess Cafe"}</h1>
          {!user && <p>Order ahead, skip the queue. Ready when you arrive.</p>}
        </div>
      </div>

      <CategoryTabs categories={categories} activeId={activeCategoryId} onChange={setActiveCategoryId} />

      {shownCategories.map((category) => (
        <section key={category.id}>
          {activeCategoryId === "all" && (
            <div className="section-head">
              <span className="eyebrow">{category.name}</span>
              <i />
            </div>
          )}
          <div className="grid">
            {category.products
              .filter((p) => p.is_available)
              .map((product) => (
                <div
                  key={product.id}
                  className="product-card tap"
                  role="button"
                  tabIndex={0}
                  onClick={() => setOpenProduct(product)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") setOpenProduct(product);
                  }}
                >
                  <div className={`glyph g-${category.tint}`}>
                    <i className={`bi bi-${category.icon}`} />
                  </div>
                  <h3>{product.name}</h3>
                  <p>{product.description}</p>
                  <div className="product-row-bottom">
                    <span className="mono">${product.price}</span>
                    <span className="btn primary">Add</span>
                  </div>
                </div>
              ))}
          </div>
        </section>
      ))}

      {openProduct && (
        <ItemSheet
          product={openProduct}
          groups={modifierGroups}
          onClose={() => setOpenProduct(null)}
          onAdd={(product, quantity, selections, label, unitPrice) =>
            add(product, quantity, selections, label, unitPrice)
          }
        />
      )}
    </div>
  );
}
