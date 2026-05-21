/**
 * src/components/Register.js
 * ──────────────────────────
 * 2-step registration flow:
 *
 *  Step 1 — User fills in username, email, password
 *            → POST /api/register/
 *            → Backend creates inactive user and sends OTP email
 *
 *  Step 2 — User enters the 6-digit OTP from their email
 *            → POST /api/verify-register/
 *            → Backend activates account and returns auth token
 *            → User is automatically logged in and redirected home
 */

import React, { useState, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api";
import { saveAuth } from "../utils/auth";

function Register() {
  const navigate = useNavigate();

  // ── Step tracking ─────────────────────────────────────────
  // "form"  → show registration form
  // "otp"   → show OTP verification input
  const [step, setStep] = useState("form");

  // ── Form state ────────────────────────────────────────────
  const [username, setUsername] = useState("");
  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");

  // ── OTP state ─────────────────────────────────────────────
  // 6 individual digit inputs for a polished UX
  const [otpDigits, setOtpDigits] = useState(["", "", "", "", "", ""]);
  const otpRefs = useRef([...Array(6)].map(() => React.createRef()));

  // ── UI state ──────────────────────────────────────────────
  const [loading,      setLoading]      = useState(false);
  const [error,        setError]        = useState("");
  const [resendTimer,  setResendTimer]  = useState(0); // countdown seconds

  // ─────────────────────────────────────────────────────────
  // Step 1: Submit registration form
  // ─────────────────────────────────────────────────────────
  const handleRegister = async () => {
    setError("");

    if (!username.trim() || !email.trim() || !password) {
      setError("All fields are required.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setLoading(true);
    try {
      await api.post("register/", { username, email, password });
      // Move to OTP step and start resend cooldown
      setStep("otp");
      startResendTimer();
    } catch (err) {
      setError(err.response?.data?.error || "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // ─────────────────────────────────────────────────────────
  // Step 2: Submit OTP
  // ─────────────────────────────────────────────────────────
  const handleVerifyOtp = async () => {
    setError("");
    const otp = otpDigits.join("");

    if (otp.length !== 6) {
      setError("Please enter the complete 6-digit OTP.");
      return;
    }

    setLoading(true);
    try {
      const res = await api.post("verify-register/", { email, otp });
      // Save token → user is now logged in
      saveAuth(res.data.token, res.data.username);
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.error || "OTP verification failed.");
      // Clear OTP inputs on failure so user can re-enter
      setOtpDigits(["", "", "", "", "", ""]);
      otpRefs.current[0]?.current?.focus();
    } finally {
      setLoading(false);
    }
  };

  // ─────────────────────────────────────────────────────────
  // Resend OTP
  // ─────────────────────────────────────────────────────────
  const handleResend = async () => {
    setError("");
    try {
      await api.post("resend-otp/", { email, purpose: "register" });
      setOtpDigits(["", "", "", "", "", ""]);
      startResendTimer();
    } catch (err) {
      setError(err.response?.data?.error || "Failed to resend OTP.");
    }
  };

  // 60-second countdown before allowing resend
  const startResendTimer = () => {
    setResendTimer(60);
    const interval = setInterval(() => {
      setResendTimer((prev) => {
        if (prev <= 1) { clearInterval(interval); return 0; }
        return prev - 1;
      });
    }, 1000);
  };

  // ─────────────────────────────────────────────────────────
  // OTP digit input handler — auto-advance focus
  // ─────────────────────────────────────────────────────────
  const handleOtpChange = (index, value) => {
    // Only allow single digits
    if (!/^\d?$/.test(value)) return;

    const updated = [...otpDigits];
    updated[index] = value;
    setOtpDigits(updated);

    // Auto-advance to next input
    if (value && index < 5) {
      otpRefs.current[index + 1]?.current?.focus();
    }
  };

  const handleOtpKeyDown = (index, e) => {
    // On backspace with empty field, go back to previous input
    if (e.key === "Backspace" && !otpDigits[index] && index > 0) {
      otpRefs.current[index - 1]?.current?.focus();
    }
  };

  // ─────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────
  return (
    <div className="container my-5">
      <div className="row justify-content-center">
        <div className="col-md-6 col-lg-5">
          <div className="card shadow-lg border-0">
            <div className="card-body p-5">

              {/* ── Step indicator ── */}
              <div className="d-flex justify-content-center mb-4 gap-2">
                <span className={`badge rounded-pill px-3 py-2 ${step === "form" ? "bg-primary" : "bg-success"}`}>
                  1 Details
                </span>
                <span className="text-muted align-self-center">→</span>
                <span className={`badge rounded-pill px-3 py-2 ${step === "otp" ? "bg-primary" : "bg-secondary"}`}>
                  2 Verify OTP
                </span>
              </div>

              {/* ── Error alert ── */}
              {error && (
                <div className="alert alert-danger py-2 small" role="alert">
                  {error}
                </div>
              )}

              {/* ════════════════════════════════════════════
                  STEP 1 — Registration Form
              ════════════════════════════════════════════ */}
              {step === "form" && (
                <>
                  <div className="text-center mb-4">
                    <h2 className="fw-bold text-dark">Create Account</h2>
                    <p className="text-muted small">We'll send an OTP to verify your email</p>
                  </div>

                  <div className="mb-3">
                    <label className="form-label fw-semibold">Username</label>
                    <input
                      className="form-control form-control-lg"
                      placeholder="Choose a username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleRegister()}
                    />
                  </div>

                  <div className="mb-3">
                    <label className="form-label fw-semibold">Email Address</label>
                    <input
                      type="email"
                      className="form-control form-control-lg"
                      placeholder="your@email.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleRegister()}
                    />
                  </div>

                  <div className="mb-4">
                    <label className="form-label fw-semibold">Password</label>
                    <input
                      type="password"
                      className="form-control form-control-lg"
                      placeholder="Min. 8 characters"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleRegister()}
                    />
                  </div>

                  <button
                    className="btn btn-primary w-100 btn-lg mb-3"
                    onClick={handleRegister}
                    disabled={loading}
                  >
                    {loading ? (
                      <><span className="spinner-border spinner-border-sm me-2" />Sending OTP...</>
                    ) : (
                      "Create Account →"
                    )}
                  </button>

                  <div className="text-center">
                    <p className="text-muted small mb-0">
                      Already have an account?{" "}
                      <Link to="/login" className="fw-bold text-primary text-decoration-none">
                        Sign in
                      </Link>
                    </p>
                  </div>
                </>
              )}

              {/* ════════════════════════════════════════════
                  STEP 2 — OTP Verification
              ════════════════════════════════════════════ */}
              {step === "otp" && (
                <>
                  <div className="text-center mb-4">
                    <div className="display-4 mb-2">📧</div>
                    <h2 className="fw-bold text-dark">Check Your Email</h2>
                    <p className="text-muted small">
                      We sent a 6-digit OTP to <strong>{email}</strong>
                    </p>
                  </div>

                  {/* 6-box OTP input */}
                  <div className="d-flex justify-content-center gap-2 mb-4">
                    {otpDigits.map((digit, i) => (
                      <input
                        key={i}
                        ref={otpRefs.current[i]}
                        type="text"
                        inputMode="numeric"
                        maxLength={1}
                        className="form-control text-center fw-bold fs-4"
                        style={{ width: "48px", height: "56px" }}
                        value={digit}
                        onChange={(e) => handleOtpChange(i, e.target.value)}
                        onKeyDown={(e) => handleOtpKeyDown(i, e)}
                      />
                    ))}
                  </div>

                  <button
                    className="btn btn-success w-100 btn-lg mb-3"
                    onClick={handleVerifyOtp}
                    disabled={loading || otpDigits.join("").length !== 6}
                  >
                    {loading ? (
                      <><span className="spinner-border spinner-border-sm me-2" />Verifying...</>
                    ) : (
                      "✓ Verify & Activate Account"
                    )}
                  </button>

                  {/* Resend OTP */}
                  <div className="text-center">
                    {resendTimer > 0 ? (
                      <p className="text-muted small">
                        Resend OTP in <strong>{resendTimer}s</strong>
                      </p>
                    ) : (
                      <button
                        className="btn btn-link btn-sm text-decoration-none"
                        onClick={handleResend}
                      >
                        Didn't receive it? Resend OTP
                      </button>
                    )}
                  </div>

                  {/* Back link */}
                  <div className="text-center mt-2">
                    <button
                      className="btn btn-link btn-sm text-muted text-decoration-none"
                      onClick={() => { setStep("form"); setError(""); }}
                    >
                      ← Change email address
                    </button>
                  </div>
                </>
              )}

            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Register;
