import React from 'react';
import { Link } from 'react-router-dom';

function Navbar() {
  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark px-4 shadow-lg">
      <div className="container-fluid">
        <Link className="navbar-brand fw-bold fs-3 text-warning" to="/">
          🍔 FoodApp
        </Link>
        
        <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span className="navbar-toggler-icon"></span>
        </button>
        
        <div className="collapse navbar-collapse" id="navbarNav">
          <ul className="navbar-nav ms-auto">
            <li className="nav-item mx-2">
              <Link className="nav-link btn btn-outline-light px-4 rounded-pill" to="/">Home</Link>
            </li>
            <li className="nav-item mx-2">
              <Link className="nav-link btn btn-warning px-4 rounded-pill fw-bold" to="/cart">
                Cart 🛒
              </Link>
            </li>
            <li className="nav-item ms-2">
              <Link className="nav-link btn btn-outline-light px-4 rounded-pill" to="/orders">Orders</Link>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;

