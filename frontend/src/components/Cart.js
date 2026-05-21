import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { isLoggedIn } from "../utils/auth";
import api from "../api";

function Cart() {
  const [cart, setCart] = useState([]);
  const navigate = useNavigate();

  const fetchCart = () => {
    api.get("cart/")
      .then(res => setCart(res.data.cart))
      .catch(err => {
        console.error(err);
        setCart([]);
      });
  };

  useEffect(() => {
    if (!isLoggedIn()) {
      navigate("/login");
      return;
    }

    fetchCart();
    const listener = () => fetchCart();
    window.addEventListener("cartUpdated", listener);
    return () => window.removeEventListener("cartUpdated", listener);
  }, [navigate]);

  const removeItem = (id) => {
    api.delete(`cart/remove/${id}/`)
      .then(() => fetchCart())
      .catch(err => console.error(err));
  };

  const placeOrder = () => {
    api.post("order/place/", {})
      .then(res => {
        alert(res.data.message);
        window.location.reload();
      })
      .catch(err => console.error(err));
  };

  return (
    <div className="container my-5">
      <h2 className="display-5 fw-bold text-center mb-5 text-dark">🛒 Your Cart</h2>

      {cart.length === 0 ? (
        <div className="text-center py-5">
          <i className="fas fa-shopping-cart fa-3x text-muted mb-4"></i>
          <h4 className="text-muted">Your cart is empty</h4>
          <Link to="/" className="btn btn-primary btn-lg">Continue Shopping</Link>
        </div>
      ) : (
        <>
          <div className="row g-4">
            {cart.map(item => {
              return (
                <div className="col-12" key={item.id}>
                  <div className="card shadow-sm">
                    <div className="row g-0">
                      <div className="col-md-2">
                        <div className="card-img-placeholder rounded-end bg-light d-flex align-items-center justify-content-center" style={{height: '100px'}}>
                          <i className="fas fa-utensils fa-2x text-muted"></i>
                        </div>
                      </div>
                      <div className="col-md-8 p-4">
                        <h5 className="mb-2">{item.product_name || item.product}</h5>
                        <div className="d-flex justify-content-between">
                          <span className="text-muted">₹{item.price}</span>
                          <span className="badge bg-primary">x{item.quantity}</span>
                        </div>
                      </div>
                      <div className="col-md-2 d-flex align-items-center justify-content-center border-start">
                        <button 
                          className="btn btn-outline-danger btn-sm"
                          onClick={() => removeItem(item.id)}
                        >
                          <i className="fas fa-trash"></i>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="row mt-5">
            <div className="col-md-8"></div>
            <div className="col-md-4">
              <div className="card shadow-lg">
                <div className="card-body">
                  <h4 className="card-title mb-3">Order Summary</h4>
                  <div className="d-flex justify-content-between mb-3">
                    <span>Total Items: {cart.length}</span>
                    <span>{cart.reduce((sum, item) => sum + item.quantity, 0)} items</span>
                  </div>
                  <hr />
                  <div className="d-flex justify-content-between fs-4 fw-bold text-success mb-4">
                    <span>Total:</span>
                    <span>₹{cart.reduce((sum, item) => sum + (parseFloat(item.price) * item.quantity), 0).toFixed(2)}</span>
                  </div>
                  <button className="btn btn-success w-100 btn-lg" onClick={placeOrder}>
                    <i className="fas fa-credit-card me-2"></i> Checkout Now
                  </button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default Cart;