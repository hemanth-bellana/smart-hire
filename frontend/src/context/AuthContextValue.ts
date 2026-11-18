
import { createContext } from "react";
import type { CurrentUser, LoginRequest } from "../api/authApi";

export interface AuthContextType {
  user: CurrentUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<
  AuthContextType | undefined
>(undefined);
