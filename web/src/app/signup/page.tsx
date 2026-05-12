"use client";

import Link from "next/link";
import { useState } from "react";
import { Coffee, LoaderCircle, UserRoundPlus } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import webConfig from "@/constants/common-env";
import { registerUser } from "@/lib/api";

export default function SignupPage() {
  const [name, setName] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [createdKey, setCreatedKey] = useState("");

  const handleRegister = async () => {
    setIsSubmitting(true);
    try {
      const data = await registerUser({
        name: name.trim(),
        invite_code: inviteCode.trim(),
      });
      setCreatedKey(data.key);
      toast.success("账号已创建");
    } catch (error) {
      const message = error instanceof Error ? error.message : "注册失败";
      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="grid min-h-[calc(100vh-1rem)] w-full place-items-center px-4 py-6">
      <Card className="w-full max-w-[560px] rounded-[30px] border-white/80 bg-white/95 shadow-[0_28px_90px_rgba(28,25,23,0.10)]">
        <CardContent className="space-y-6 p-6 sm:p-8">
          <div className="space-y-4 text-center">
            <div className="mx-auto inline-flex size-14 items-center justify-center rounded-[18px] bg-stone-950 text-white shadow-sm">
              <UserRoundPlus className="size-5" />
            </div>
            <div className="space-y-2">
              <h1 className="text-3xl font-semibold tracking-tight text-stone-950">注册账号</h1>
              <p className="text-sm leading-6 text-stone-500">创建一个新的登录密钥，注册后直接复制保存即可。</p>
            </div>
          </div>

          {createdKey ? (
            <div className="space-y-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
              <div className="font-medium">新密钥只显示一次：</div>
              <code className="block break-all rounded-xl border border-emerald-200 bg-white/80 px-3 py-3 font-mono text-[13px]">{createdKey}</code>
              <div className="flex flex-wrap gap-3">
                <Button
                  type="button"
                  variant="outline"
                  className="h-10 rounded-2xl border-emerald-200 bg-white text-emerald-700"
                  onClick={async () => {
                    await navigator.clipboard.writeText(createdKey);
                    toast.success("已复制密钥");
                  }}
                >
                  复制密钥
                </Button>
                <Button asChild className="h-10 rounded-2xl bg-stone-950 text-white hover:bg-stone-800">
                  <Link href="/login">去登录</Link>
                </Button>
              </div>
            </div>
          ) : null}

          <div className="space-y-3">
            <label className="block text-sm font-medium text-stone-700">昵称</label>
            <Input
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="例如：Mvh30"
              className="h-13 rounded-2xl border-stone-200 bg-white px-4"
            />
          </div>

          <div className="space-y-3">
            <label className="block text-sm font-medium text-stone-700">邀请码</label>
            <Input
              value={inviteCode}
              onChange={(event) => setInviteCode(event.target.value)}
              placeholder="如果后台设置了邀请码，这里填入"
              className="h-13 rounded-2xl border-stone-200 bg-white px-4"
            />
          </div>

          <Button
            className="h-13 w-full rounded-2xl bg-stone-950 text-white hover:bg-stone-800"
            onClick={() => void handleRegister()}
            disabled={isSubmitting}
          >
            {isSubmitting ? <LoaderCircle className="size-4 animate-spin" /> : null}
            注册
          </Button>

          <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
            <Link href="/login" className="text-stone-600 transition hover:text-stone-950">
              已有账号，去登录
            </Link>
            <a
              href={webConfig.donateUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 text-stone-600 transition hover:text-stone-950"
            >
              <Coffee className="size-4" />
              Donate
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
