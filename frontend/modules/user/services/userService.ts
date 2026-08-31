import { apiFetch } from "@/core/http/apiFetch";

import type { User, UserCreateInput, UserUpdateInput } from "@/modules/user/types/user";

export const userService = {
  list(): Promise<User[]> {
    return apiFetch<User[]>("/users");
  },

  me(): Promise<User> {
    return apiFetch<User>("/users/me");
  },

  get(id: number): Promise<User> {
    return apiFetch<User>(`/users/${id}`);
  },

  create(input: UserCreateInput): Promise<User> {
    return apiFetch<User>("/users", {
      method: "POST",
      body: input,
    });
  },

  update(id: number, input: UserUpdateInput): Promise<User> {
    return apiFetch<User>(`/users/${id}`, {
      method: "PATCH",
      body: input,
    });
  },

  delete(id: number): Promise<void> {
    return apiFetch<void>(`/users/${id}`, {
      method: "DELETE",
    });
  },

  changePassword(id: number, currentPassword: string, newPassword: string): Promise<User> {
    return apiFetch<User>(`/users/${id}/change-password`, {
      method: "PATCH",
      body: { current_password: currentPassword, new_password: newPassword },
    });
  },
};
