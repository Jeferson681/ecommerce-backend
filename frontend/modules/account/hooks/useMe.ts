"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { ApiError } from "@/core/exceptions/ApiError";
import { userService } from "@/modules/user/services/userService";
import type { User } from "@/modules/user/types/user";

type UseMeState = {
  data: User | null;
  isLoading: boolean;
  error: ApiError | null;
};

export function useMe() {
  const [state, setState] = useState<UseMeState>({
    data: null,
    isLoading: true,
    error: null,
  });

  const fetchMe = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const data = await userService.me();
      setState({ data, isLoading: false, error: null });
    } catch (err) {
      setState({ data: null, isLoading: false, error: err as ApiError });
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void fetchMe();
  }, [fetchMe]);

  return useMemo(
    () => ({
      ...state,
      refetch: fetchMe,
    }),
    [state, fetchMe]
  );
}
