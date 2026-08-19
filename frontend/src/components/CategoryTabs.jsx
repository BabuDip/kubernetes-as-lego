// Shared "All + per-category" tab bar — same component drives the customer Menu
// and the manager Catalogue so category browsing looks and behaves identically.
export default function CategoryTabs({ categories, activeId, onChange }) {
  if (categories.length <= 1) return null;
  return (
    <div className="cat-tabs">
      <button
        type="button"
        className={`cat-tab ${activeId === "all" ? "on" : ""}`}
        onClick={() => onChange("all")}
      >
        All
      </button>
      {categories.map((category) => (
        <button
          key={category.id}
          type="button"
          className={`cat-tab ${category.id === activeId ? "on" : ""}`}
          onClick={() => onChange(category.id)}
        >
          <i className={`bi bi-${category.icon}`} /> {category.name}
        </button>
      ))}
    </div>
  );
}
