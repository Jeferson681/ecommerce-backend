"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { ApiError } from "@/core/exceptions/ApiError";
import { userService } from "@/modules/user/services/userService";
import type { User } from "@/modules/user/types/user";

type UseUsersState = {
  data: User[] | null;
  isLoading: boolean;
  error: ApiError | null;
};

export function useUsers() {
  const [state, setState] = useState<UseUsersState>({
    data: null,
    isLoading: true,
    error: null,
  });

  const fetchUsers = useCallback(async () => {
    await Promise.resolve();
    setState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const data = await userService.list();
      setState({ data, isLoading: false, error: null });
    } catch (err) {
      setState({ data: null, isLoading: false, error: err as ApiError });
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void fetchUsers();
  }, [fetchUsers]);

  const api = useMemo(
    () => ({
      ...state,
      refetch: fetchUsers,
    }),
    [state, fetchUsers]
  );

  return api;
}
