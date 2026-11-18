
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";
function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        padding: "40px",
        background: "#f5f7fb",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "16px",
        }}
      >
        <h1>SmartHire Dashboard</h1>

        <button
          onClick={handleLogout}
          style={{
            padding: "10px 20px",
            background: "#dc3545",
            color: "white",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
          }}
        >
          Logout
        </button>
      </div>

      <p>
        Welcome to the HR dashboard. This is where HR will manage jobs,
        resumes, candidates, and recruitment workflows.
      </p>

      <p>
        Logged in as: <strong>{user?.email}</strong>
      </p>
    </div>
  );
}

export default Dashboard;
