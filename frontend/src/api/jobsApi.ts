import apiClient from "./client";

export interface Job {
  id: number;
  title: string;
  description: string;
  location: string | null;
  employment_type: string | null;
  created_by: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateJobRequest {
  title: string;
  description: string;
  location?: string;
  employment_type?: string;
}

export async function getJobs(): Promise<Job[]> {
  const response = await apiClient.get<Job[]>("/jobs");

  return response.data;
}

export async function getJob(jobId: number): Promise<Job> {
  const response = await apiClient.get<Job>(`/jobs/${jobId}`);

  return response.data;
}

export async function createJob(
  jobData: CreateJobRequest,
): Promise<Job> {
  const response = await apiClient.post<Job>(
    "/jobs",
    jobData,
  );

  return response.data;
}