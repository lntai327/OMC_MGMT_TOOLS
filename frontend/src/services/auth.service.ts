import { apiClient } from './api.client';
import { Token, User } from '../models/auth.types';

export const authService = {
  async login(username: string, password: string): Promise<Token> {
    const response = await apiClient.post<Token>('/auth/login/json', {
      username,
      password,
    });
    const token = response.data;
    localStorage.setItem('omc_access_token', token.access_token);
    localStorage.setItem('omc_username', token.username);
    localStorage.setItem('omc_role', token.role);
    return token;
  },

  async getMe(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  logout(): void {
    localStorage.removeItem('omc_access_token');
    localStorage.removeItem('omc_username');
    localStorage.removeItem('omc_role');
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('omc_access_token');
  },

  getCurrentUser(): { username: string; role: string } | null {
    const username = localStorage.getItem('omc_username');
    const role = localStorage.getItem('omc_role');
    if (!username) return null;
    return { username, role: role || 'operator' };
  },
};

