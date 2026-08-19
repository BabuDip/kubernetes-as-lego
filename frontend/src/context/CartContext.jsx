import { createContext, useContext, useEffect, useMemo, useState } from "react";

const CartContext = createContext(null);
const STORAGE_KEY = "qless_cart";

function load() {
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
    // Normalise lines saved by an older cart shape (pre-modifiers) that lacked key/unitPrice.
    return stored.map((l) => ({
      key: l.key ?? lineKey(l.product.id, l.modifiers ?? {}),
      product: l.product,
      quantity: l.quantity,
      modifiers: l.modifiers ?? {},
      modifiersLabel: l.modifiersLabel ?? "",
      unitPrice: l.unitPrice ?? Number(l.product.price),
    }));
  } catch {
    return [];
  }
}

// Same product with different modifier selections (e.g. oat vs. full-cream flat white)
// are separate cart lines, so the key must fold in the chosen options.
function lineKey(productId, modifiers = {}) {
  const parts = Object.keys(modifiers)
    .sort()
    .map((k) => `${k}:${modifiers[k]}`);
  return parts.length ? `${productId}|${parts.join(",")}` : productId;
}

export function CartProvider({ children }) {
  const [lines, setLines] = useState(load);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(lines));
  }, [lines]);

  const add = (product, quantity = 1, modifiers = {}, modifiersLabel = "", unitPrice) => {
    const key = lineKey(product.id, modifiers);
    setLines((prev) => {
      const existing = prev.find((l) => l.key === key);
      if (existing) {
        return prev.map((l) => (l.key === key ? { ...l, quantity: l.quantity + quantity } : l));
      }
      return [
        ...prev,
        { key, product, quantity, modifiers, modifiersLabel, unitPrice: unitPrice ?? Number(product.price) },
      ];
    });
  };

  const adjust = (key, delta) => {
    setLines((prev) =>
      prev
        .map((l) => (l.key === key ? { ...l, quantity: l.quantity + delta } : l))
        .filter((l) => l.quantity > 0),
    );
  };

  const remove = (key) => {
    setLines((prev) => prev.filter((l) => l.key !== key));
  };

  const clear = () => setLines([]);

  const total = useMemo(() => lines.reduce((sum, l) => sum + l.unitPrice * l.quantity, 0), [lines]);
  const count = useMemo(() => lines.reduce((sum, l) => sum + l.quantity, 0), [lines]);

  return (
    <CartContext.Provider value={{ lines, add, adjust, remove, clear, total, count }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  return useContext(CartContext);
}
