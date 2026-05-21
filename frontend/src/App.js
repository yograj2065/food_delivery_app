import React from "react";
import "./App.css";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import ProductList from "./components/ProductList";
import Login from "./components/Login";
import Register from "./components/Register";
import Cart from "./components/Cart";
import Orders from "./components/Orders";

function App() {
  return (
    <Router>
      <div className="App">
        <Navbar />
        
        <div className="hero text-center text-white mb-5">
          <div className="container">
            <h1 className="display-4 fw-bold mb-4">🍽️ Delicious Food Delivered Fast</h1>
            <p className="lead mb-4">Order your favorite meals from top restaurants. Fast delivery guaranteed!</p>
            <a href="/" className="btn btn-warning btn-lg px-5 fs-5">Order Now</a>
          </div>
        </div>

        <Routes>
          <Route path="/" element={<ProductList />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/cart" element={<Cart />} />
          <Route path="/orders" element={<Orders />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
