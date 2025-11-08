/**
 * Authenticated API helper
 * Automatically adds Authorization header to all API calls
 */

export function getAuthHeaders() {
  const token = localStorage.getItem('token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

export async function authenticatedFetch(url, options = {}) {
  const headers = {
    ...getAuthHeaders(),
    ...(options.headers || {})
  };

  return fetch(url, {
    ...options,
    headers
  });
}
