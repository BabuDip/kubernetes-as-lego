import { useEffect, useState } from "react";
import { api } from "../../api/client";
import CategoryTabs from "../../components/CategoryTabs.jsx";
import Drawer from "../../components/Drawer.jsx";

const blankForm = { name: "", description: "", price: "", category: "", modifier_groups: [] };

function validateForm(form) {
  const errors = {};
  if (!form.name.trim()) {
    errors.name = "Name is required.";
  }
  if (!form.category) {
    errors.category = "Choose a category.";
  }
  if (form.price === "" || form.price == null) {
    errors.price = "Price is required.";
  } else if (Number.isNaN(Number(form.price)) || Number(form.price) <= 0) {
    errors.price = "Enter a price greater than $0.";
  }
  return errors;
}

export default function ManagerCatalogue() {
  const [categories, setCategories] = useState([]);
  const [modifierGroups, setModifierGroups] = useState({});
  const [activeCategoryId, setActiveCategoryId] = useState("all");
  const [editingId, setEditingId] = useState(null); // product id being edited, or "new"
  const [form, setForm] = useState(blankForm);
  const [error, setError] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});

  const load = () => api.get("/categories/").then(setCategories);

  useEffect(() => {
    load();
    api.get("/modifier-groups/").then(setModifierGroups);
  }, []);

  const shownCategories =
    activeCategoryId === "all" ? categories : categories.filter((c) => c.id === activeCategoryId);
  const activeCategory = categories.find((c) => c.id === activeCategoryId);

  const toggleAvailable = async (product) => {
    await api.patch(`/products/${product.id}/`, { is_available: !product.is_available });
    load();
  };

  const startCreate = () => {
    setForm({ ...blankForm, category: (activeCategory || categories[0])?.slug || "" });
    setEditingId("new");
    setError(null);
    setFieldErrors({});
  };

  const startEdit = (product) => {
    setForm({
      name: product.name,
      description: product.description,
      price: product.price,
      category: product.category,
      modifier_groups: product.modifier_groups,
    });
    setEditingId(product.id);
    setError(null);
    setFieldErrors({});
  };

  const cancelEdit = () => {
    setEditingId(null);
    setForm(blankForm);
    setError(null);
    setFieldErrors({});
  };

  const updateField = (patch) => {
    setForm((f) => ({ ...f, ...patch }));
    setFieldErrors((prev) => {
      const next = { ...prev };
      for (const key of Object.keys(patch)) delete next[key];
      return next;
    });
  };

  const toggleModifierGroup = (key) => {
    setForm((f) => ({
      ...f,
      modifier_groups: f.modifier_groups.includes(key)
        ? f.modifier_groups.filter((k) => k !== key)
        : [...f.modifier_groups, key],
    }));
  };

  const save = async () => {
    const errors = validateForm(form);
    setFieldErrors(errors);
    setError(null);
    if (Object.keys(errors).length > 0) return;

    try {
      if (editingId === "new") {
        await api.post("/products/", form);
      } else {
        await api.patch(`/products/${editingId}/`, form);
      }
      cancelEdit();
      load();
    } catch (err) {
      setFieldErrors((prev) => ({
        ...prev,
        ...Object.fromEntries(
          Object.entries(err.data || {})
            .filter(([key]) => key in form)
            .map(([key, messages]) => [key, Array.isArray(messages) ? messages[0] : messages]),
        ),
      }));
      setError(err.data?.detail || "Could not save item — check the highlighted fields.");
    }
  };

  return (
    <div className="page">
      <div className="hero">
        <h1 className="display">Catalogue</h1>
        <button type="button" className="btn primary" onClick={startCreate}>
          + New Item
        </button>
      </div>

      <CategoryTabs categories={categories} activeId={activeCategoryId} onChange={setActiveCategoryId} />

      {shownCategories.map((category) => (
        <section key={category.id} style={{ marginBottom: 20 }}>
          <div className="eyebrow" style={{ marginBottom: 8 }}>
            {category.name}
          </div>
          {category.products.map((product) => (
            <div key={product.id} className={`cart-line ${product.is_available ? "" : "sold-out"}`}>
              <div className="cart-line-main">
                <div style={{ fontWeight: 600 }}>{product.name}</div>
                <div style={{ fontSize: 11.5, color: "var(--slate)" }}>{product.description}</div>
                {product.modifier_groups.length > 0 && (
                  <div style={{ fontSize: 11, color: "var(--pine)" }}>
                    {product.modifier_groups.join(", ")}
                  </div>
                )}
              </div>
              <span className="mono">${product.price}</span>
              <button type="button" className="btn ghost" onClick={() => startEdit(product)}>
                Edit
              </button>
              <button type="button" className="btn ghost" onClick={() => toggleAvailable(product)}>
                {product.is_available ? "Mark sold out" : "Mark available"}
              </button>
            </div>
          ))}
        </section>
      ))}

      {editingId && (
        <Drawer
          title={editingId === "new" ? "New Item" : "Edit Item"}
          subtitle={categories.find((c) => c.slug === form.category)?.name}
          onClose={cancelEdit}
          footer={
            <button type="button" className="btn primary lg" onClick={save}>
              {editingId === "new" ? "Add item" : "Save changes"}
            </button>
          }
        >
          {error && <div className="form-error">{error}</div>}
          <fieldset className="field">
            <legend>Category</legend>
            <div className="opts">
              {categories.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  className={`opt ${form.category === c.slug ? "on" : ""}`}
                  onClick={() => updateField({ category: c.slug })}
                >
                  {c.name}
                </button>
              ))}
            </div>
            {fieldErrors.category && <p className="field-warning">{fieldErrors.category}</p>}
          </fieldset>
          <div className="field">
            <label htmlFor="product-name">Name</label>
            <input
              id="product-name"
              className="input"
              required
              aria-invalid={Boolean(fieldErrors.name)}
              value={form.name}
              onChange={(e) => updateField({ name: e.target.value })}
            />
            {fieldErrors.name && <p className="field-warning">{fieldErrors.name}</p>}
          </div>
          <div className="field">
            <label htmlFor="product-description">Description</label>
            <input
              id="product-description"
              className="input"
              value={form.description}
              onChange={(e) => updateField({ description: e.target.value })}
            />
          </div>
          <div className="field">
            <label htmlFor="product-price">Price</label>
            <input
              id="product-price"
              className="input"
              type="number"
              step="0.01"
              min="0"
              required
              aria-invalid={Boolean(fieldErrors.price)}
              value={form.price}
              onChange={(e) => updateField({ price: e.target.value })}
            />
            {fieldErrors.price && <p className="field-warning">{fieldErrors.price}</p>}
          </div>
          <fieldset className="field">
            <legend>Options customers can choose</legend>
            <table className="modtable">
              <thead>
                <tr>
                  <th>Group</th>
                  <th>Choices &amp; markup</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(modifierGroups).map(([key, group]) => (
                  <tr key={key}>
                    <td className="modtable-group">
                      <button
                        type="button"
                        className={`opt ${form.modifier_groups.includes(key) ? "on" : ""}`}
                        onClick={() => toggleModifierGroup(key)}
                      >
                        {group.label}
                      </button>
                    </td>
                    <td className="modtable-choices">
                      {Object.values(group.options).map((option) => (
                        <span key={option.label} className="modchoice">
                          {option.label}
                          {Number(option.price) > 0 && (
                            <em className="mono"> +${Number(option.price).toFixed(2)}</em>
                          )}
                        </span>
                      ))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </fieldset>
        </Drawer>
      )}
    </div>
  );
}
