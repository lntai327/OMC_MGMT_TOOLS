import { useState, useEffect } from 'react';
import { authService } from '../services/auth.service';

export function useAuthViewModel() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(authService.isAuthenticated());
  const [currentUser, setCurrentUser] = useState<{ username: string; role: string } | null>(
    authService.getCurrentUser()
  );
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const login = async (username: string, password: string): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      const token = await authService.login(username, password);
      setIsAuthenticated(true);
      setCurrentUser({ username: token.username, role: token.role });
      return true;
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Đăng nhập thất bại. Vui lòng kiểm tra lại tài khoản.';
      setError(msg);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    authService.logout();
    setIsAuthenticated(false);
    setCurrentUser(null);
  };

  return {
    isAuthenticated,
    currentUser,
    loading,
    error,
    login,
    logout,
    isAdmin: currentUser?.role === 'admin',
    isOperator: currentUser?.role === 'admin' || currentUser?.role === 'operator',
  };
}

