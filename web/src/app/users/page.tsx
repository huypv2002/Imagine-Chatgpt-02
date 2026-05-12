"use client";

import { LoaderCircle } from "lucide-react";

import { useAuthGuard } from "@/lib/use-auth-guard";

import { UserKeysCard } from "../settings/components/user-keys-card";

export default function UsersPage() {
  const { isCheckingAuth, session } = useAuthGuard(["admin"]);

  if (isCheckingAuth || !session || session.role !== "admin") {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <LoaderCircle className="size-5 animate-spin text-stone-400" />
      </div>
    );
  }

  return (
    <section className="space-y-6">
      <div className="space-y-1">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-500">Users</div>
        <h1 className="text-2xl font-semibold tracking-tight">Quản lý tài khoản đăng nhập</h1>
      </div>
      <UserKeysCard />
    </section>
  );
}
