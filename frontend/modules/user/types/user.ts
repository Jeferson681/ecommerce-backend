export type User = {
  id: number;
  created_at: string;
  updated_at: string;
  first_name: string;
  last_name: string;
  email: string;
  role: string;
  is_active: boolean;
};

export type UserCreateInput = {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
};

export type UserUpdateInput = {
  first_name?: string;
  last_name?: string;
  email?: string;
  is_active?: boolean;
};
