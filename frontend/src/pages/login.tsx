import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../App.css";

function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  return (
    <div className="app">
      <div className="login-container">
        <div className="login-card">
          {/* Brand */}
          <div className="brand">
            <div className="brand-icon">S</div>

            <div>
              <h1>SmartHire</h1>
              <p>AI-Powered Recruitment</p>
            </div>
          </div>

          {/* Login Header */}
          <div className="login-header">
            <h2>Welcome back</h2>
            <p>Sign in to your HR portal</p>
          </div>

          {/* Login Form */}
          <form
            className="login-form"
            onSubmit={(event) => {
              event.preventDefault();

              if (!email.trim()) {
                setError("Please enter your work email.");
                return;
              }

              const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

              if (!emailPattern.test(email)) {
                setError("Please enter a valid email address.");
                return;
              }

              if (!password.trim()) {
                setError("Please enter your password.");
                return;
              }

              setError("");
              setIsLoading(true);

              navigate("/dashboard");
            }}
          >
            {/* Email */}
            <div className="form-group">
              <label htmlFor="email">Work Email</label>

              <input
                id="email"
                type="email"
                placeholder="hr@company.com"
                value={email}
                onChange={(event) => {
                  setEmail(event.target.value);
                  setError("");
                }}
              />
            </div>

            {/* Error Message */}
            {error && (
              <p
                className="error-message"
                style={{
                  color: "red",
                  marginTop: "-10px",
                  marginBottom: "10px",
                  fontSize: "14px",
                }}
              >
                {error}
              </p>
            )}

            {/* Password */}
            <div className="form-group">
              <div className="password-label">
                <label htmlFor="password">Password</label>

                <button type="button" className="forgot-password">
                  Forgot password?
                </button>
              </div>

              <input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(event) => {
                  setPassword(event.target.value);
                  setError("");
                }}
              />
            </div>

            {/* Sign In */}
            <button
              type="submit"
              className="login-button"
              disabled={isLoading}
            >
              {isLoading ? "Signing in..." : "Sign In"}
            </button>
          </form>

          {/* Register */}
          <div className="login-footer">
            <p>
              Don't have an account?{" "}
              <button type="button" className="register-link">
                Create an account
              </button>
            </p>
          </div>
        </div>

        {/* Right Side Information */}
        <div className="login-info">
          <div className="info-content">
            <span className="eyebrow">SMART RECRUITMENT</span>

            <h2>
              Find the right
              <br />
              candidates faster.
            </h2>

            <p>
              Upload a job description and resumes. SmartHire analyzes
              candidate profiles and helps HR teams identify relevant
              candidates with explainable AI-powered matching.
            </p>

            <div className="feature-list">
              <div className="feature">
                <span>✓</span>
                <p>AI-powered resume matching</p>
              </div>

              <div className="feature">
                <span>✓</span>
                <p>Explainable candidate scoring</p>
              </div>

              <div className="feature">
                <span>✓</span>
                <p>HR-controlled email communication</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;