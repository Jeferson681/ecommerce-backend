"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { userService } from "@/modules/user/services/userService";
import { getUserErrorMessage } from "@/core/exceptions/userMessage";

import { PageHeader } from "@/shared/components/PageHeader";
import { Alert, AlertDescription, AlertTitle } from "@/shared/components/ui/alert";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";
import { Input } from "@/shared/components/ui/input";

export default function SignupPage() {
  const router = useRouter();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSignup(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await userService.create({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim(),
        password,
      });

      router.push("/login?next=/account");
    } catch (err) {
      setError(getUserErrorMessage(err));
      setIsSubmitting(false);
    }
  }

  const canSubmit =
    firstName.trim().length >= 2 &&
    lastName.trim().length >= 2 &&
    email.trim().length > 0 &&
    password.length >= 8 &&
    !isSubmitting;

  return (
    <div className="space-y-4">
      <PageHeader title="Create account" description="Sign up as a customer" />

      {error ? (
        <Alert className="border-red-200">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <Card>
        <CardContent className="p-6">
          <form onSubmit={handleSignup} className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">First name</label>
                <Input value={firstName} onChange={(e) => setFirstName(e.target.value)} />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Last name</label>
                <Input value={lastName} onChange={(e) => setLastName(e.target.value)} />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Email</label>
              <Input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Password</label>
              <Input value={password} onChange={(e) => setPassword(e.target.value)} type="password" />
              <p className="text-xs text-zinc-500">Minimum 8 characters</p>
            </div>

            <Button type="submit" disabled={!canSubmit}>
              {isSubmitting ? "Creating..." : "Create account"}
            </Button>

            <p className="text-sm text-zinc-600">
              Already have an account?{" "}
              <Link href="/login?next=/account" className="underline underline-offset-4">
                Sign in
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
