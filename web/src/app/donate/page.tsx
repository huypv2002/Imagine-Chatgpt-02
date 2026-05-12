"use client";

import Image from "next/image";
import { Coffee, Heart } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import webConfig from "@/constants/common-env";

export default function DonatePage() {
  return (
    <div className="grid min-h-[calc(100vh-1rem)] w-full place-items-center px-4 py-6">
      <Card className="w-full max-w-[640px] rounded-[30px] border-white/80 bg-white/95 shadow-[0_28px_90px_rgba(28,25,23,0.10)]">
        <CardContent className="space-y-6 p-6 sm:p-8">
          <div className="space-y-4 text-center">
            <div className="mx-auto inline-flex size-14 items-center justify-center rounded-[18px] bg-amber-500 text-white shadow-sm">
              <Heart className="size-5" />
            </div>
            <div className="space-y-2">
              <h1 className="text-3xl font-semibold tracking-tight text-stone-950">Donate</h1>
              <p className="text-sm leading-6 text-stone-500">Nếu bạn thấy app này hữu ích, ủng hộ một ly cà phê giúp mình có thêm động lực nhé.</p>
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-[minmax(0,1fr)_280px]">
            <div className="space-y-4">
              <div className="rounded-2xl border border-stone-200 bg-stone-50 p-4">
                <div className="grid gap-3 text-sm">
                  <div className="flex items-center justify-between gap-4">
                    <span className="text-stone-500">Tên tài khoản</span>
                    <span className="font-semibold text-stone-950">Pham Van Huy</span>
                  </div>
                  <div className="flex items-center justify-between gap-4 border-t border-stone-200 pt-3">
                    <span className="text-stone-500">Số tài khoản</span>
                    <span className="font-mono font-semibold text-stone-950">04486011177779</span>
                  </div>
                </div>
              </div>

              <Button asChild className="h-13 w-full rounded-2xl bg-stone-950 text-white hover:bg-stone-800">
                <a href={webConfig.donateUrl} target="_blank" rel="noreferrer">
                  <Coffee className="size-4" />
                  Buy me a coffee
                </a>
              </Button>
            </div>

            <div className="overflow-hidden rounded-3xl border border-stone-200 bg-white p-3 shadow-sm">
              <div className="relative aspect-[3/4] w-full overflow-hidden rounded-2xl bg-stone-50">
                <Image
                  src="/qrdonate.jpg"
                  alt="QR nhận donate"
                  fill
                  className="object-contain"
                  priority
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
