import apiClient from "./client";

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export async function loginUser(
  credentials: LoginRequest,
): Promise<TokenResponse> {
  const formData = new URLSearchParams();

  formData.append("username", credentials.username);
  formData.append("password", credentials.password);

  const response = await apiClient.post<TokenResponse>(
    "/auth/login",
    formData,
    {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    },
  );

  return response.data;
}