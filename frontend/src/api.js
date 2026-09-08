const backendUrl = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

/** Default UI fetch budget for large MySQL ledger reads (5 minutes). */
export const API_TIMEOUT_MS = 300000;

export async function fetchWithTimeout(url, options = {}, timeout = API_TIMEOUT_MS) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function apiGet(path, timeout = API_TIMEOUT_MS) {
  let response;
  try {
    response = await fetchWithTimeout(`${backendUrl}${path}`, {}, timeout);
  } catch (error) {
    if (error?.name === "AbortError") {
      throw new Error("Request timed out while loading data. Please retry.");
    }
    throw error;
  }
  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`);
  }
  return response.json();
}

export { backendUrl };
