// Single source of truth for how a signed-in user is displayed across the app.
export function displayName(user) {
  if (!user) return "";
  return user.name || user.email.split("@")[0];
}

export function roleLabel(user) {
  return user?.is_staff ? "Cafe Manager" : "Customer";
}
