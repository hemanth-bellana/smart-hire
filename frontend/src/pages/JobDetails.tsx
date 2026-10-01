import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";

import { getJob, type Job } from "../api/jobsApi";

function JobDetails() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();

  const [job, setJob] = useState<Job | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadJob() {
      if (!jobId) {
        setError("Job ID is missing.");
        setIsLoading(false);
        return;
      }

      try {
        const data = await getJob(Number(jobId));
        setJob(data);
      } catch (error) {
        console.error("Failed to load job:", error);
        setError("Unable to load job details.");
      } finally {
        setIsLoading(false);
      }
    }

    loadJob();
  }, [jobId]);

  if (isLoading) {
    return <p style={{ padding: "40px" }}>Loading job details...</p>;
  }

  if (error) {
    return (
      <div style={{ padding: "40px" }}>
        <p>{error}</p>

        <button onClick={() => navigate("/jobs")}>
          Back to Jobs
        </button>
      </div>
    );
  }

  if (!job) {
    return (
      <div style={{ padding: "40px" }}>
        <p>Job not found.</p>

        <button onClick={() => navigate("/jobs")}>
          Back to Jobs
        </button>
      </div>
    );
  }

  return (
    <div style={{ padding: "40px", maxWidth: "900px", margin: "0 auto" }}>
      <button onClick={() => navigate("/jobs")}>
        ← Back to Jobs
      </button>

      <div
        style={{
          marginTop: "30px",
          border: "1px solid #ddd",
          borderRadius: "12px",
          padding: "30px",
        }}
      >
        <h1>{job.title}</h1>

        <p style={{ marginTop: "20px" }}>
          {job.description}
        </p>

        <div style={{ marginTop: "25px" }}>
          {job.location && (
            <p>
              <strong>Location:</strong> {job.location}
            </p>
          )}

          {job.employment_type && (
            <p>
              <strong>Employment Type:</strong>{" "}
              {job.employment_type}
            </p>
          )}

          <p>
            <strong>Status:</strong>{" "}
            {job.is_active ? "Active" : "Inactive"}
          </p>

          <p>
            <strong>Created:</strong>{" "}
            {new Date(job.created_at).toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  );
}

export default JobDetails;