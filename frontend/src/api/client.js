const BASE = "/api";

// Fetches a fresh token from GET /api/auth/csrf/'s response body on every
// unsafe request and echoes it back as the X-CSRFToken header — Django's
// documented AJAX-friendly alternative to reading the csrftoken cookie
// directly (config.settings.base's CSRF_COOKIE_HTTPONLY is Django's own
// default, False, so the cookie is readable too, but this project doesn't
// rely on that):
// https://docs.djangoproject.com/en/dev/ref/csrf/#ajax
// Deliberately not cached — Django can rotate the token per response (e.g.
// after login, per CSRF_COOKIE_AGE/rotation), so a stale cached value can
// silently stop matching and fail every subsequent request.
async function fetchCsrfToken() {
  const response = await fetch(`${BASE}/auth/csrf/`, { credentials: "same-origin" });
  const data = await response.json();
  return data.csrfToken;
}

async function request(path, { method = "GET", body } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (method !== "GET") {
    headers["X-CSRFToken"] = await fetchCsrfToken();
  }
  const response = await fetch(`${BASE}${path}`, {
    method,
    headers,
    credentials: "same-origin",
    body: body ? JSON.stringify(body) : undefined,
  });
  if (response.status === 204) return null;
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const error = new Error(data?.detail || "Request failed");
    error.data = data;
    error.status = response.status;
    throw error;
  }
  return data;
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: "POST", body }),
  put: (path, body) => request(path, { method: "PUT", body }),
  patch: (path, body) => request(path, { method: "PATCH", body }),
  del: (path) => request(path, { method: "DELETE" }),
};

export async function ensureCsrf() {
  await fetchCsrfToken();
}
