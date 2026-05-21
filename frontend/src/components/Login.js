/**
 * src/components/Login.js
 * ───────────────────────
 * 2-step login flow:
 *
 *  Step 1 — User enters username + password
 *            → POST /api/login/
 *            → Backend validates credentials and sends OTP to registered email
 *
 *  Step 2 — User enters the 6-digit OTP
 *            → POST /api/login/verify/
 *            → Backend validates OTP and returns auth token
 *            → Token stored in localStorage, user redirected home
 */

import React, { useState, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api";
import { saveAuth } from "../utils/auth";

function Login() {
  const navigate = useNavigate();

  // ── Step tracking ─────────────────────────────────────────
  // "credentials" → show username/password form
  // "otp"         → show OTP verification input
  const [step, setStep] = useState("credentials");

  // ── Credentials state ─────────────────────────────────────
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  // ── OTP state ─────────────────────────────────────────────
  const [otpDigits,   setOtpDigits]   = useState(["", "", "", "", "", ""]);
  const [emailForOtp, setEmailForOtp] = useState(""); // returned by Step 1 API
  const otpRefs = useRef([...Array(6)].map(() => React.createRef()));

  // ── UI state ──────────────────────────────────────────────
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState("");
  const [resendTimer, setResendTimer] = useState(0);

  // ─────────────────────────────────────────────────────────
  // Step 1: Validate credentials → send OTP
  // ─────────────────────────────────────────────────────────
  const handleLogin = async () => {
    setError("");

    if (!username.trim() || !password) {
      setError("Username and password are required.");
      return;
    }

    setLoading(true);
    try {
      const res = await api.post("login/", { username, password });
      // Backend returns the email so we can use it in Step 2
      setEmailForOtp(res.data.email);
      setStep("otp");
      startResendTimer();
    } catch (err) {
      setError(err.response?.data?.error || "Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  // ─────────────────────────────────────────────────────────
  // Step 2: Verify OTP → get token
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
      const res = await api.post("login/verify/", {
        email: emailForOtp,
        otp,
      });
      // Persist token and username, then go home
      saveAuth(res.data.token, res.data.username);
      window.dispatchEvent(new Event("cartUpdated"));
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.error || "OTP verification failed.");
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
      await api.post("resend-otp/", { email: emailForOtp, purpose: "login" });
      setOtpDigits(["", "", "", "", "", ""]);
      startResendTimer();
    } catch (err) {
      setError(err.response?.data?.error || "Failed to resend OTP.");
    }
  };

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
  // OTP digit input handler
  // ─────────────────────────────────────────────────────────
  const handleOtpChange = (index, value) => {
    if (!/^\d?$/.test(value)) return;
    const updated = [...otpDigits];
    updated[index] = value;
    setOtpDigits(updated);
    if (value && index < 5) {
      otpRefs.current[index + 1]?.current?.focus();
    }
  };

  const handleOtpKeyDown = (index, e) => {
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
                <span className={`badge rounded-pill px-3 py-2 ${step === "credentials" ? "bg-primary" : "bg-success"}`}>
                  1 Credentials
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
                  STEP 1 — Credentials
              ════════════════════════════════════════════ */}
              {step === "credentials" && (
                <>
                  <div className="text-center mb-4">
                    <h2 className="fw-bold text-dark">Welcome Back</h2>
                    <p className="text-muted small">Sign in with OTP verification</p>
                  </div>

                  <div className="mb-3">
                    <label className="form-label fw-semibold">Username</label>
                    <input
                      className="form-control form-control-lg"
                      placeholder="Enter your username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleLogin()}
                    />
                  </div>

                  <div className="mb-4">
                    <label className="form-label fw-semibold">Password</label>
                    <input
                      type="password"
                      className="form-control form-control-lg"
                      placeholder="Enter your password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleLogin()}
                    />
                  </div>

                  <button
                    className="btn btn-dark w-100 btn-lg mb-3"
                    onClick={handleLogin}
                    disabled={loading}
                  >
                    {loading ? (
                      <><span className="spinner-border spinner-border-sm me-2" />Sending OTP...</>
                    ) : (
                      "Sign In →"
                    )}
                  </button>

                  <div className="text-center">
                    <p className="text-muted small mb-0">
                      Don't have an account?{" "}
                      <Link to="/register" className="fw-bold text-primary text-decoration-none">
                        Register here
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
                    <div className="display-4 mb-2">🔑</div>
                    <h2 className="fw-bold text-dark">Enter OTP</h2>
                    <p className="text-muted small">
                      A 6-digit code was sent to your registered email
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
                      "✓ Verify & Login"
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
                      onClick={() => { setStep("credentials"); setError(""); setOtpDigits(["","","","","",""]); }}
                    >
                      ← Back to login
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

export default Login;
