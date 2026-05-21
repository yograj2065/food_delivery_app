/**
 * src/components/Navbar.js
 * ────────────────────────
 * Auth-aware navigation bar.
 *
 * - Shows Login / Register links when logged out
 * - Shows username + Logout button when logged in
 * - Listens to the custom "authChanged" event so it updates
 *   immediately after login/logout without a page reload
 */

import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api";
import { isLoggedIn, getUsername, clearAuth } from "../utils/auth";

function Navbar() {
  const navigate = useNavigate();
  const [loggedIn,  setLoggedIn]  = useState(isLoggedIn());
  const [username,  setUsername]  = useState(getUsername());

  // Re-check auth state whenever login/logout events fire
  useEffect(() => {
    const syncAuth = () => {
      setLoggedIn(isLoggedIn());
      setUsername(getUsername());
    };
    window.addEventListener("authChanged",  syncAuth);
    window.addEventListener("cartUpdated",  syncAuth); // legacy event
    return () => {
      window.removeEventListener("authChanged", syncAuth);
      window.removeEventListener("cartUpdated", syncAuth);
    };
  }, []);

  const handleLogout = async () => {
    try {
      // Tell the backend to delete the token
      await api.post("logout/");
    } catch {
      // Even if the request fails, clear local state
    } finally {
      clearAuth();
      navigate("/login");
    }
  };

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark px-4 py-3">
      {/* Brand */}
      <Link className="navbar-brand fw-bold fs-4" to="/">
        🍽️ FoodApp
      </Link>

      {/* Toggler for mobile */}
      <button
        className="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarContent"
      >
        <span className="navbar-toggler-icon" />
      </button>

      <div className="collapse navbar-collapse" id="navbarContent">
        {/* Left links */}
        <ul className="navbar-nav me-auto">
          <li className="nav-item">
            <Link className="nav-link" to="/">Home</Link>
          </li>
          {loggedIn && (
            <>
              <li className="nav-item">
                <Link className="nav-link" to="/cart">🛒 Cart</Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="/orders">📋 Orders</Link>
              </li>
            </>
          )}
        </ul>

        {/* Right auth section */}
        <ul className="navbar-nav ms-auto align-items-center gap-2">
          {loggedIn ? (
            <>
              <li className="nav-item">
                <span className="navbar-text text-light">
                  👤 <strong>{username}</strong>
                </span>
              </li>
              <li className="nav-item">
                <button
                  className="btn btn-outline-light btn-sm"
                  onClick={handleLogout}
                >
                  Logout
                </button>
              </li>
            </>
          ) : (
            <>
              <li className="nav-item">
                <Link className="nav-link" to="/login">Login</Link>
              </li>
              <li className="nav-item">
                <Link className="btn btn-warning btn-sm px-3" to="/register">
                  Register
                </Link>
              </li>
            </>
          )}
        </ul>
      </div>
    </nav>
  );
}

export default Navbar;
