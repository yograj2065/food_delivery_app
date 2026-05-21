import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { isLoggedIn } from "../utils/auth";
import api from "../api";

function ProductList() {
  const [products, setProducts] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    api.get("products/")
      .then((res) => setProducts(res.data))
      .catch((err) => console.log(err));
  }, []);

  const addToCart = (id) => {
    if (!isLoggedIn()) {
      navigate("/login");
      return;
    }

    api.post("cart/add/", {
      product_id: id,
      quantity: 1
    })
    .then(() => {
      alert("Added to cart");
      window.dispatchEvent(new Event("cartUpdated"));
    })
    .catch((err) => {
      console.error(err);
      alert(err.response?.data?.error || "Failed to add to cart");
    });
  };

  return (
    <div className="container my-5">
      <div className="row mb-4">
        <div className="col-12">
          <h2 className="display-5 fw-bold text-center mb-5 text-dark">
            🍕 Featured Products
          </h2>
        </div>
      </div>
      
      <div className="row g-4">
        {products.map((product) => (
          <div className="col-lg-3 col-md-4 col-sm-6" key={product.id}>
            <div className="card h-100">
              {product.image && (
                <img 
                  src={product.image} 
                  className="card-img-top"
                  alt={product.name}
                />
              )}
              <div className="card-body d-flex flex-column">
                <h5 className="card-title fw-bold">{product.name}</h5>
                <p className="card-text flex-grow-1 text-muted">{product.description}</p>
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <span className="h4 text-success fw-bold">₹{product.price}</span>
                </div>
                <button 
                  className="btn btn-primary w-100"
                  onClick={() => addToCart(product.id)}
                >
                  Add to Cart 🛒
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ProductList;
