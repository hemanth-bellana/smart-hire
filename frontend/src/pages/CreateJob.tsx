import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createJob } from "../api/jobsApi";

function CreateJob() {
  const navigate = useNavigate();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState("");
  const [employmentType, setEmploymentType] = useState("");

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    setError("");

    if (!title.trim()) {
      setError("Job title is required.");
      return;
    }

    if (!description.trim()) {
      setError("Job description is required.");
      return;
    }

    try {
      setIsLoading(true);

      await createJob({
        title: title.trim(),
        description: description.trim(),
        location: location.trim() || undefined,
        employment_type: employmentType.trim() || undefined,
      });

      navigate("/jobs");
    } catch (error) {
      console.error("Failed to create job:", error);
      setError("Unable to create job. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ padding: "40px", maxWidth: "800px" }}>
      <h1>Create Job</h1>

      <p>
        Create a new job opening for your recruitment workflow.
      </p>

      <form onSubmit={handleSubmit}>
        <div style={{ marginTop: "24px" }}>
          <label htmlFor="title">
            <strong>Job Title</strong>
          </label>

          <input
            id="title"
            type="text"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="e.g. AI Developer"
            style={{
              display: "block",
              width: "100%",
              marginTop: "8px",
              padding: "12px",
            }}
          />
        </div>

        <div style={{ marginTop: "24px" }}>
          <label htmlFor="description">
            <strong>Job Description</strong>
          </label>

          <textarea
            id="description"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Describe the role, responsibilities, requirements, and skills..."
            rows={8}
            style={{
              display: "block",
              width: "100%",
              marginTop: "8px",
              padding: "12px",
              resize: "vertical",
            }}
          />
        </div>

        <div style={{ marginTop: "24px" }}>
          <label htmlFor="location">
            <strong>Location</strong>
          </label>

          <input
            id="location"
            type="text"
            value={location}
            onChange={(event) => setLocation(event.target.value)}
            placeholder="e.g. Hyderabad"
            style={{
              display: "block",
              width: "100%",
              marginTop: "8px",
              padding: "12px",
            }}
          />
        </div>

        <div style={{ marginTop: "24px" }}>
          <label htmlFor="employmentType">
            <strong>Employment Type</strong>
          </label>

          <select
            id="employmentType"
            value={employmentType}
            onChange={(event) => setEmploymentType(event.target.value)}
            style={{
              display: "block",
              width: "100%",
              marginTop: "8px",
              padding: "12px",
            }}
          >
            <option value="">Select employment type</option>
            <option value="Full-time">Full-time</option>
            <option value="Part-time">Part-time</option>
            <option value="Contract">Contract</option>
            <option value="Internship">Internship</option>
          </select>
        </div>

        {error && (
          <p style={{ color: "red", marginTop: "20px" }}>
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={isLoading}
          style={{
            marginTop: "30px",
            padding: "12px 24px",
            cursor: isLoading ? "not-allowed" : "pointer",
          }}
        >
          {isLoading ? "Creating..." : "Create Job"}
        </button>
      </form>
    </div>
  );
}

export default CreateJob;