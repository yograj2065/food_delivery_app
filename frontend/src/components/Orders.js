import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api";

function Orders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("order/history/")
      .then(res => setOrders(res.data.orders))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="container my-5 text-center">
        <div className="spinner-border text-primary" />
      </div>
    );
  }

  return (
    <div className="container my-5">
      <h2 className="display-5 fw-bold text-center mb-5 text-dark">📋 Order History</h2>

      {orders.length === 0 ? (
        <div className="text-center py-5">
          <i className="fas fa-clipboard-list fa-3x text-muted mb-4"></i>
          <h4 className="text-muted">No orders yet</h4>
          <Link to="/" className="btn btn-primary mt-3">Start Shopping</Link>
        </div>
      ) : (
        <div className="row g-4">
          {orders.map(order => (
            <div className="col-12" key={order.order_id}>
              <div className="card shadow-sm">
                <div className="card-header bg-primary text-white">
                  <div className="d-flex justify-content-between align-items-center">
                    <h5 className="mb-0">Order #{order.order_id}</h5>
                    <span className="badge bg-success fs-6">₹{order.total_price}</span>
                  </div>
                  {order.created_at && (
                    <small className="opacity-75">
                      {new Date(order.created_at).toLocaleString()}
                    </small>
                  )}
                </div>
                <div className="card-body">
                  <div className="row g-3">
                    {order.items.map((item, index) => (
                      <div className="col-md-6" key={index}>
                        <div className="d-flex align-items-center p-3 bg-light rounded">
                          <div className="bg-white rounded-circle p-3 me-3 shadow-sm">
                            <i className="fas fa-utensils text-primary"></i>
                          </div>
                          <div>
                            <h6 className="mb-1">{item.product}</h6>
                            <small className="text-muted">
                              {item.quantity} × ₹{item.price} = ₹{(item.quantity * item.price).toFixed(2)}
                            </small>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Orders;
