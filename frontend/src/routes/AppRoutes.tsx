import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import Login from "../pages/Login";
import Dashboard from "../pages/Dashboard";
import Jobs from "../pages/Jobs";
import JobDetails from "../pages/JobDetails";
import CreateJob from "../pages/CreateJob";

function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={<Login />}
        />

        <Route
          path="/dashboard"
          element={<Dashboard />}
        />

        <Route
          path="/jobs/create"
          element={<CreateJob />}
        />

        <Route
          path="/jobs"
          element={<Jobs />}
        />
        <Route
  path="/jobs/:jobId"
  element={<JobDetails />}
/>
        <Route
          path="*"
          element={
            <Navigate
              to="/login"
              replace
            />
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default AppRoutes;