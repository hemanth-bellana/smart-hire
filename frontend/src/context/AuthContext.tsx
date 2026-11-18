
import {
  useEffect,
  useState,
  type ReactNode,
} from "react";

import { AuthContext } from "./AuthContextValue";

import {
  getCurrentUser,
  loginUser,
  type CurrentUser,
  type LoginRequest,
} from "../api/authApi";

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const validateSession = async () => {
      const token = localStorage.getItem("access_token");

      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const currentUser = await getCurrentUser();
        setUser(currentUser);
      } catch {
        localStorage.removeItem("access_token");
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    void validateSession();
  }, []);

  const login = async (credentials: LoginRequest) => {
    const response = await loginUser(credentials);

    localStorage.setItem(
      "access_token",
      response.access_token,
    );

    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      localStorage.removeItem("access_token");
      setUser(null);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: user !== null,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
