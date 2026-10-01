import { useEffect, useState } from "react";
import { getJobs, type Job } from "../api/jobsApi";

function Jobs() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadJobs() {
      try {
        const data = await getJobs();
        setJobs(data);
      } catch (error) {
        console.error("Failed to load jobs:", error);
        setError("Unable to load jobs.");
      } finally {
        setIsLoading(false);
      }
    }

    loadJobs();
  }, []);

  if (isLoading) {
    return <p>Loading jobs...</p>;
  }

  if (error) {
    return <p>{error}</p>;
  }

  return (
    <div style={{ padding: "40px" }}>
      <h1>Jobs</h1>

      {jobs.length === 0 ? (
        <p>No jobs found.</p>
      ) : (
        <div>
          {jobs.map((job) => (
            <div
              key={job.id}
              style={{
                border: "1px solid #ddd",
                borderRadius: "8px",
                padding: "20px",
                marginTop: "20px",
              }}
            >
              <h2>{job.title}</h2>

              <p>{job.description}</p>

              {job.location && (
                <p>
                  <strong>Location:</strong> {job.location}
                </p>
              )}

              {job.employment_type && (
                <p>
                  <strong>Employment:</strong> {job.employment_type}
                </p>
              )}

              <p>
                <strong>Status:</strong>{" "}
                {job.is_active ? "Active" : "Inactive"}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Jobs;