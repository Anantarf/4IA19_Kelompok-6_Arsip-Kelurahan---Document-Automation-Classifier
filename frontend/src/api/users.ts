import api from './axios';

export type UserItem = {
  id: number;
  username: string;
  role: 'admin' | 'staf';
};

export type CreateUserPayload = {
  username: string;
  password: string;
  role?: 'admin' | 'staf';
};

export async function listUsers(): Promise<UserItem[]> {
  const { data } = await api.get<UserItem[]>('/auth/users');
  return data;
}

export async function createUser(payload: CreateUserPayload): Promise<UserItem> {
  const { data } = await api.post<UserItem>('/auth/users', payload);
  return data;
}

export async function deleteUser(userId: number): Promise<void> {
  await api.delete(`/auth/users/${userId}`);
}

export async function resetUserPassword(userId: number, password: string): Promise<void> {
  await api.post(`/auth/users/${userId}/reset-password`, { password });
}
