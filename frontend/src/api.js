/**
 * src/api.js
 * ──────────
 * Central Axios instance for all API calls.
 *
 * Features:
 *  - Automatically attaches the DRF auth token from localStorage
 *    to every request via the Authorization header
 *  - On 401 responses, clears the stored token and redirects to /login
 *    (prevents the user from being stuck in a broken auth state)
 */

import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api/",
  headers: {
    "Content-Type": "application/json",
  },
});

// ── Request interceptor: inject token ────────────────────────
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response interceptor: handle 401 globally ────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token is invalid or expired — clear it and redirect to login
      localStorage.removeItem("token");
      localStorage.removeItem("username");
      // Only redirect if not already on the login page
      if (!window.location.pathname.includes("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
