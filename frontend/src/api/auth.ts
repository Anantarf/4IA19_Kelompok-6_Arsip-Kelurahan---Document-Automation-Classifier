import api from './axios';

export type UserRole = 'admin' | 'staf';

export type AuthResponse = {
  access_token: string;
  token_type: string;
  role: UserRole;
  username: string;
};

export async function loginUser(username: string, password: string): Promise<AuthResponse> {
  const params = new URLSearchParams();
  params.append('username', username);
  params.append('password', password);
  // Content-Type: application/x-www-form-urlencoded is set automatically by axios when using URLSearchParams
  const { data } = await api.post<AuthResponse>('/auth/token', params);
  return data;
}

export async function registerUser(username: string, password: string): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/auth/register', { username, password });
  return data;
}
