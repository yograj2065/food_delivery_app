/**
 * src/utils/auth.js
 * ─────────────────
 * Centralised authentication state helpers.
 * All components should use these instead of accessing localStorage directly.
 */

/** Returns true if a token is stored (user is logged in). */
export const isLoggedIn = () => {
  return !!localStorage.getItem("token");
};

/** Returns the stored username or null. */
export const getUsername = () => {
  return localStorage.getItem("username") || null;
};

/** Persists the token and username after successful login/registration. */
export const saveAuth = (token, username) => {
  localStorage.setItem("token", token);
  localStorage.setItem("username", username);
  // Notify Navbar and other listeners that auth state changed
  window.dispatchEvent(new Event("authChanged"));
};

/** Clears all auth data (used on logout). */
export const clearAuth = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("username");
  window.dispatchEvent(new Event("authChanged"));
};
