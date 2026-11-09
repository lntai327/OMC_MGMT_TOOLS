export interface Token {
  access_token: string;
  token_type: string;
  role: string;
  username: string;
}

export interface User {
  id: number;
  username: string;
  role: 'admin' | 'operator' | 'viewer';
  is_active: boolean;
}

