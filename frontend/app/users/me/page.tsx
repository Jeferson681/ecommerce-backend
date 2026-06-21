"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { userService } from "@/modules/user/services/userService";
import { getUserErrorMessage } from "@/core/exceptions/userMessage";

import { PageHeader } from "@/shared/components/PageHeader";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";
import { Input } from "@/shared/components/ui/input";

export default function MyProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<{ id: number; first_name: string; last_name: string; email: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    userService.me()
      .then((data) => {
        setProfile(data);
        setFirstName(data.first_name);
        setLastName(data.last_name);
      })
      .catch((err) => setError(getUserErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!profile) return;
    setSaving(true);
    setSaveError(null);
    try {
      const updated = await userService.update(profile.id, { first_name: firstName.trim(), last_name: lastName.trim() });
      setProfile(updated);
      setEditing(false);
    } catch (err) {
      setSaveError(getUserErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="text-sm text-zinc-600">Loading...</div>;
  if (error) return <div className="rounded-sm border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">{error}</div>;
  if (!profile) return <div className="text-sm text-zinc-600">Profile not found.</div>;

  return (
    <div className="space-y-4">
      <PageHeader title="My Profile" description="Manage your personal information" />

      <Card>
        <CardContent className="p-6">
          {editing ? (
            <form onSubmit={handleSave} className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">First name</label>
                <Input value={firstName} onChange={(e) => setFirstName(e.target.value)} />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Last name</label>
                <Input value={lastName} onChange={(e) => setLastName(e.target.value)} />
              </div>
              {saveError && <p className="text-sm text-red-600">{saveError}</p>}
              <div className="flex gap-2">
                <Button type="submit" disabled={saving}>{saving ? "Saving..." : "Save"}</Button>
                <Button type="button" variant="outline" onClick={() => setEditing(false)}>Cancel</Button>
              </div>
            </form>
          ) : (
            <div className="space-y-4">
              <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <dt className="text-xs text-zinc-500">First name</dt>
                  <dd className="text-sm font-medium">{profile.first_name}</dd>
                </div>
                <div>
                  <dt className="text-xs text-zinc-500">Last name</dt>
                  <dd className="text-sm font-medium">{profile.last_name}</dd>
                </div>
                <div>
                  <dt className="text-xs text-zinc-500">Email</dt>
                  <dd className="text-sm">{profile.email}</dd>
                </div>
              </dl>
              <Button onClick={() => setEditing(true)}>Edit profile</Button>
            </div>
          )}
        </CardContent>
      </Card>

      <Button asChild variant="outline">
        <Link href="/account">Back to account</Link>
      </Button>
    </div>
  );
}
