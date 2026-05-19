"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { ApiError } from "@/core/exceptions/ApiError";
import { userService } from "@/modules/user/services/userService";
import type { User } from "@/modules/user/types/user";

type UseUserState = {
  data: User | null;
  isLoading: boolean;
  error: ApiError | null;
};

export function useUser(id: number) {
  const [state, setState] = useState<UseUserState>({
    data: null,
    isLoading: true,
    error: null,
  });

  const fetchUser = useCallback(async () => {
    await Promise.resolve();
    setState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const data = await userService.get(id);
      setState({ data, isLoading: false, error: null });
    } catch (err) {
      setState({ data: null, isLoading: false, error: err as ApiError });
    }
  }, [id]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void fetchUser();
  }, [fetchUser]);

  return useMemo(
    () => ({
      ...state,
      refetch: fetchUser,
    }),
    [state, fetchUser]
  );
}
