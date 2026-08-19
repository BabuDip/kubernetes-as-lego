import { useEffect, useMemo, useState } from "react";

// Bottom sheet for customising a product before adding it to the cart: modifier
// groups (milk/size/strength/serve) come from the server (GET /modifier-groups/)
// so the frontend never hardcodes prices — the server re-validates and re-prices
// everything again at checkout regardless.
export default function ItemSheet({ product, groups, onClose, onAdd }) {
  const [selections, setSelections] = useState(() => {
    const initial = {};
    for (const key of product.modifier_groups) {
      if (groups[key]) initial[key] = groups[key].default;
    }
    return initial;
  });
  const [quantity, setQuantity] = useState(1);
  const [added, setAdded] = useState(false);

  const { unitPrice, label } = useMemo(() => {
    let extra = 0;
    const labels = [];
    for (const key of product.modifier_groups) {
      const group = groups[key];
      if (!group) continue;
      const chosen = selections[key] ?? group.default;
      const option = group.options[chosen];
      if (!option) continue;
      extra += Number(option.price);
      if (chosen !== group.default) labels.push(option.label);
    }
    return { unitPrice: Number(product.price) + extra, label: labels.join(" · ") };
  }, [selections, product, groups]);

  const choose = (groupKey, optionId) => setSelections((prev) => ({ ...prev, [groupKey]: optionId }));

  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <div className="sheetwrap">
      {/* Click-to-dismiss convenience layer; Escape (above) and the Close button cover keyboard use. */}
      <div className="backdrop" aria-hidden="true" onClick={onClose} />
      <div className="sheet" role="dialog" aria-modal="true" aria-label={product.name}>
        <div className="sheet-head">
          <h3>{product.name}</h3>
          <button type="button" className="sheet-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
        {product.description && <p className="sheet-desc">{product.description}</p>}

        {product.modifier_groups.map((groupKey) => {
          const group = groups[groupKey];
          if (!group) return null;
          return (
            <div key={groupKey} className="group">
              <div className="group-label">{group.label}</div>
              <div className="opts">
                {Object.entries(group.options).map(([optionId, option]) => (
                  <button
                    key={optionId}
                    type="button"
                    className={`opt ${selections[groupKey] === optionId ? "on" : ""}`}
                    onClick={() => choose(groupKey, optionId)}
                  >
                    {option.label}
                    {Number(option.price) > 0 && ` +$${Number(option.price).toFixed(2)}`}
                  </button>
                ))}
              </div>
            </div>
          );
        })}

        <div className="sheet-foot">
          <div className="stepper">
            <button type="button" onClick={() => setQuantity((q) => Math.max(1, q - 1))}>
              −
            </button>
            <span className="mono">{quantity}</span>
            <button type="button" onClick={() => setQuantity((q) => q + 1)}>
              +
            </button>
          </div>
          <button
            type="button"
            className={`btn lg ${added ? "success" : "primary"}`}
            disabled={added}
            onClick={() => {
              onAdd(product, quantity, selections, label, unitPrice);
              setAdded(true);
              setTimeout(onClose, 500);
            }}
          >
            {added ? "Added ✓" : `Add · $${(unitPrice * quantity).toFixed(2)}`}
          </button>
        </div>
      </div>
    </div>
  );
}
