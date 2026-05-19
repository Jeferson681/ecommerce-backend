"use client";

import Link from "next/link";

import { Button } from "@/shared/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/components/ui/table";

import type { User } from "@/modules/user/types/user";

type UserTableProps = {
  users: User[];
  onDelete: (user: User) => void;
};

export function UserTable({ users, onDelete }: UserTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[80px]">ID</TableHead>
          <TableHead>Name</TableHead>
          <TableHead>Email</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="w-[220px] text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {users.map((u) => (
          <TableRow key={u.id}>
            <TableCell className="font-mono text-xs text-zinc-600">{u.id}</TableCell>
            <TableCell className="font-medium">{u.first_name} {u.last_name}</TableCell>
            <TableCell className="text-zinc-700">{u.email}</TableCell>
            <TableCell>
              <span className={u.is_active ? "text-green-700" : "text-zinc-500"}>
                {u.is_active ? "Active" : "Inactive"}
              </span>
            </TableCell>
            <TableCell className="text-right">
              <div className="inline-flex items-center gap-2">
                <Button asChild variant="outline" size="sm">
                  <Link href={`/users/${u.id}`}>View</Link>
                </Button>
                <Button asChild variant="secondary" size="sm">
                  <Link href={`/users/${u.id}/edit`}>Edit</Link>
                </Button>
                <Button variant="destructive" size="sm" onClick={() => onDelete(u)}>
                  Delete
                </Button>
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
