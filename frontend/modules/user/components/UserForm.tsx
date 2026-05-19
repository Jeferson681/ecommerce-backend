"use client";

import { useMemo, useState } from "react";

import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Alert, AlertDescription, AlertTitle } from "@/shared/components/ui/alert";

import type { User, UserCreateInput, UserUpdateInput } from "@/modules/user/types/user";

type UserFormProps =
  | {
      mode: "create";
      initial?: never;
      onSubmit: (input: UserCreateInput) => Promise<void>;
      submitLabel?: string;
    }
  | {
      mode: "edit";
      initial?: Partial<User>;
      onSubmit: (input: UserUpdateInput) => Promise<void>;
      submitLabel?: string;
    };

export function UserForm({ mode, initial, onSubmit, submitLabel }: UserFormProps) {
  const [firstName, setFirstName] = useState(initial?.first_name ?? "");
  const [lastName, setLastName] = useState(initial?.last_name ?? "");
  const [email, setEmail] = useState(initial?.email ?? "");
  const [password, setPassword] = useState("");
  const [isActive, setIsActive] = useState(initial?.is_active ?? true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = useMemo(() => {
    const base = firstName.trim().length > 0 && lastName.trim().length > 0 && email.trim().length > 0;
    const passOk = mode === "edit" ? true : password.trim().length >= 8;
    return base && passOk && !isSubmitting;
  }, [firstName, lastName, email, password, mode, isSubmitting]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const common = {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim(),
      };

      if (mode === "create") {
        const payload: UserCreateInput = {
          ...common,
          password: password.trim(),
        };
        await onSubmit(payload);
      } else {
        const payload: UserUpdateInput = {
          ...common,
          is_active: isActive,
        };
        await onSubmit(payload);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected error");
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error ? (
        <Alert className="border-red-200">
          <AlertTitle>Request failed</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <label className="text-sm font-medium">First name</label>
          <Input value={firstName} onChange={(e) => setFirstName(e.target.value)} placeholder="Jeferson" />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Last name</label>
          <Input value={lastName} onChange={(e) => setLastName(e.target.value)} placeholder="Silva" />
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">Email</label>
        <Input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="user@example.com" />
      </div>

      {mode === "create" ? (
        <div className="space-y-2">
          <label className="text-sm font-medium">Password</label>
          <Input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="min 8 characters"
            type="password"
          />
        </div>
      ) : null}

      {mode === "edit" ? (
        <div className="flex items-center gap-2">
          <input
            id="is_active"
            type="checkbox"
            className="h-4 w-4"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
          />
          <label htmlFor="is_active" className="text-sm">
            Active
          </label>
        </div>
      ) : null}

      <div className="flex items-center gap-2">
        <Button type="submit" disabled={!canSubmit}>
          {submitLabel ?? (mode === "create" ? "Create user" : "Save changes")}
        </Button>
        <Button type="button" variant="outline" disabled={isSubmitting} onClick={() => history.back()}>
          Cancel
        </Button>
      </div>

      <p className="text-xs text-zinc-500">Fields match the backend schemas (`UserCreate`/`UserUpdate`).</p>
    </form>
  );
}
