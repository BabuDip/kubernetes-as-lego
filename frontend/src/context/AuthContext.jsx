import { createContext, useContext, useEffect, useState } from "react";
import { api, ensureCsrf } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      await ensureCsrf();
      try {
        setUser(await api.get("/auth/me/"));
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const login = async (email, password) => {
    const data = await api.post("/auth/login/", { email, password });
    setUser(data);
    return data;
  };

  const signup = async (email, password1, password2) => {
    const data = await api.post("/auth/signup/", { email, password1, password2 });
    setUser(data);
    return data;
  };

  const logout = async () => {
    await api.post("/auth/logout/");
    setUser(null);
  };

  const updateProfile = async (changes) => {
    const data = await api.patch("/auth/me/", changes);
    setUser(data);
    return data;
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout, updateProfile }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
