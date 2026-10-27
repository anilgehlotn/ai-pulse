const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const TOKEN_KEY = "token";

// The token is only ever read from and written to localStorage. Never log it.
export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

// App registers one function to run when the server rejects our token (expired or invalid).
let sessionExpired = () => {};
export function onSessionExpired(callback) {
  sessionExpired = callback;
}

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

// FastAPI sends {"detail": "text"} for our own errors and {"detail": [{loc, msg}, ...]} for
// validation errors (422). Anything else (an HTML error page from a proxy, say) is not JSON at all.
export function errorMessage(status, bodyText) {
  let detail;
  try {
    detail = JSON.parse(bodyText).detail;
  } catch {
    detail = undefined;
  }
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const field = (d.loc || []).filter((part) => part !== "body").join(" ");
        return field ? `${field}: ${d.msg}.` : `${d.msg}.`;
      })
      .join(" ");
  }
  return `The server had a problem (${status}). Please try again.`;
}

export async function api(path, options = {}) {
  const token = getToken();
  let res;
  try {
    res = await fetch(BASE + path, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.headers || {}),
      },
    });
  } catch {
    throw new ApiError("Can't reach the server. Check that the backend is running.", 0);
  }

  const text = await res.text();
  if (!res.ok) {
    // A 401 on a request that carried a token means the session is over.
    // A 401 without one is just a wrong password on the login form.
    if (res.status === 401 && token) {
      clearToken();
      sessionExpired();
    }
    throw new ApiError(errorMessage(res.status, text), res.status);
  }
  return text ? JSON.parse(text) : null;
}
