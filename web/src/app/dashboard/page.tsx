"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowUpRight,
  CheckCircle2,
  LoaderCircle,
  RefreshCw,
  Users,
  Video,
  ImageIcon,
} from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { fetchDashboardSummary, type DashboardSummary } from "@/lib/api";
import { useAuthGuard } from "@/lib/use-auth-guard";

const metricCards = [
  { key: "accounts_total", label: "Tổng tài khoản", icon: Users },
  { key: "accounts_active", label: "Tài khoản hoạt động", icon: CheckCircle2 },
  { key: "images_today", label: "Ảnh hôm nay", icon: ImageIcon },
  { key: "accounts_created_today", label: "Tài khoản tạo hôm nay", icon: ArrowUpRight },
  { key: "calls_today", label: "Tác vụ hôm nay", icon: Activity },
  { key: "videos_today", label: "Video hôm nay", icon: Video },
] as const;

function MetricCard({
  label,
  value,
  icon: Icon,
  tone = "text-stone-950",
}: {
  label: string;
  value: string | number;
  icon: typeof Users;
  tone?: string;
}) {
  return (
    <Card className="rounded-2xl border-white/80 bg-white/90 shadow-sm">
      <CardContent className="flex items-start justify-between gap-4 p-5">
        <div className="space-y-2">
          <div className="text-xs font-semibold tracking-[0.18em] text-stone-400 uppercase">{label}</div>
          <div className={`text-3xl font-semibold tracking-tight ${tone}`}>{value}</div>
        </div>
        <div className="rounded-2xl bg-stone-950/5 p-3 text-stone-900">
          <Icon className="size-5" />
        </div>
      </CardContent>
    </Card>
  );
}

function DashboardContent() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadSummary = async (silent = false) => {
    if (!silent) {
      setIsLoading(true);
    } else {
      setIsRefreshing(true);
    }
    try {
      const data = await fetchDashboardSummary();
      setSummary(data);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Không tải được dashboard");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    void loadSummary();
  }, []);

  const metrics = useMemo(() => {
    if (!summary) {
      return [];
    }
    return [
      { ...metricCards[0], value: summary.accounts.total.toLocaleString() },
      { ...metricCards[1], value: summary.accounts.active.toLocaleString(), tone: "text-emerald-600" },
      { ...metricCards[2], value: summary.images.today_total.toLocaleString(), tone: "text-blue-600" },
      { ...metricCards[3], value: summary.accounts.created_today.toLocaleString(), tone: "text-emerald-600" },
      { ...metricCards[4], value: summary.calls.today_total.toLocaleString(), tone: "text-violet-600" },
      { ...metricCards[5], value: summary.videos.today_total.toLocaleString(), tone: "text-cyan-600" },
    ];
  }, [summary]);

  if (isLoading && !summary) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <LoaderCircle className="size-5 animate-spin text-stone-400" />
      </div>
    );
  }

  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-1">
          <div className="text-xs font-semibold tracking-[0.18em] text-stone-500 uppercase">Dashboard</div>
          <h1 className="text-2xl font-semibold tracking-tight">Tổng quan hệ thống</h1>
          <p className="max-w-2xl text-sm leading-6 text-stone-500">
            Số liệu được lấy trực tiếp từ account pool, image tasks và log server.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="rounded-lg px-3 py-1.5 text-stone-600">
            Ngày {summary?.date || "-"}
          </Badge>
          <Button
            variant="outline"
            onClick={() => void loadSummary(true)}
            disabled={isRefreshing}
            className="h-10 rounded-xl border-stone-200 bg-white px-4 text-stone-700"
          >
            {isRefreshing ? <LoaderCircle className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
            Làm mới
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {metrics.map((item) => (
          <MetricCard key={item.label} label={item.label} value={item.value} icon={item.icon} tone={item.tone} />
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Card className="rounded-2xl border-white/80 bg-white/90 shadow-sm">
          <CardContent className="space-y-4 p-5">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-xs font-semibold tracking-[0.18em] text-stone-400 uppercase">Số liệu nhanh</div>
                <h2 className="text-lg font-semibold tracking-tight">Trạng thái tài khoản</h2>
              </div>
              <Badge variant="outline" className="rounded-lg border-stone-200 bg-white text-stone-600">
                {summary?.calls.unique_actors_today || 0} người dùng trong ngày
              </Badge>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl border border-stone-100 bg-stone-50 p-4">
                <div className="text-xs font-semibold tracking-[0.18em] text-stone-400 uppercase">Hoạt động</div>
                <div className="mt-2 text-3xl font-semibold text-emerald-600">{summary?.accounts.active || 0}</div>
                <div className="mt-1 text-sm text-stone-500">Tài khoản bình thường</div>
              </div>
              <div className="rounded-2xl border border-stone-100 bg-stone-50 p-4">
                <div className="text-xs font-semibold tracking-[0.18em] text-stone-400 uppercase">Giới hạn</div>
                <div className="mt-2 text-3xl font-semibold text-amber-500">{summary?.accounts.limited || 0}</div>
                <div className="mt-1 text-sm text-stone-500">Đang chờ hồi quota</div>
              </div>
              <div className="rounded-2xl border border-stone-100 bg-stone-50 p-4">
                <div className="text-xs font-semibold tracking-[0.18em] text-stone-400 uppercase">Lỗi</div>
                <div className="mt-2 text-3xl font-semibold text-rose-500">{summary?.accounts.abnormal || 0}</div>
                <div className="mt-1 text-sm text-stone-500">Bị lỗi hoặc vô hiệu</div>
              </div>
              <div className="rounded-2xl border border-stone-100 bg-stone-50 p-4">
                <div className="text-xs font-semibold tracking-[0.18em] text-stone-400 uppercase">Đã xoá hôm nay</div>
                <div className="mt-2 text-3xl font-semibold text-stone-900">{summary?.accounts.deleted_today || 0}</div>
                <div className="mt-1 text-sm text-stone-500">Số tài khoản đã dọn</div>
              </div>
            </div>
            <div className="grid gap-3 md:grid-cols-3">
              <div className="rounded-2xl border border-stone-100 px-4 py-3">
                <div className="text-xs font-semibold tracking-[0.16em] text-stone-400 uppercase">Tác vụ ảnh</div>
                <div className="mt-2 text-2xl font-semibold text-stone-900">{summary?.images.today_total || 0}</div>
                <div className="text-sm text-stone-500">Ảnh tạo hôm nay</div>
              </div>
              <div className="rounded-2xl border border-stone-100 px-4 py-3">
                <div className="text-xs font-semibold tracking-[0.16em] text-stone-400 uppercase">Tác vụ lưu</div>
                <div className="mt-2 text-2xl font-semibold text-stone-900">{summary?.tasks.total || 0}</div>
                <div className="text-sm text-stone-500">Tác vụ ảnh đang lưu</div>
              </div>
              <div className="rounded-2xl border border-stone-100 px-4 py-3">
                <div className="text-xs font-semibold tracking-[0.16em] text-stone-400 uppercase">Video</div>
                <div className="mt-2 text-2xl font-semibold text-stone-900">{summary?.videos.today_total || 0}</div>
                <div className="text-sm text-stone-500">Hiện repo chưa có pipeline video</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-white/80 bg-white/90 shadow-sm">
          <CardContent className="space-y-4 p-5">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold tracking-[0.18em] text-stone-400 uppercase">Hoạt động gần nhất</div>
                <h2 className="text-lg font-semibold tracking-tight">Recent activity</h2>
              </div>
              <Badge variant="secondary" className="rounded-lg px-3 py-1.5 text-stone-600">
                {summary?.calls.today_success || 0} thành công
              </Badge>
            </div>
            <div className="space-y-2">
              {(summary?.recent_activity || []).slice(0, 10).map((item) => (
                <div key={item.id} className="rounded-2xl border border-stone-100 px-4 py-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="text-sm font-medium text-stone-900">{item.summary || "—"}</div>
                      <div className="text-xs text-stone-500">
                        {item.time} · {item.actor || "system"}{item.endpoint ? ` · ${item.endpoint}` : ""}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {item.type ? <Badge variant="secondary" className="rounded-lg">{item.type}</Badge> : null}
                      {item.status === "success" ? (
                        <Badge variant="success" className="rounded-lg">Thành công</Badge>
                      ) : item.status === "failed" ? (
                        <Badge variant="danger" className="rounded-lg">Thất bại</Badge>
                      ) : null}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            {(summary?.recent_activity || []).length === 0 ? (
              <div className="rounded-2xl border border-dashed border-stone-200 px-4 py-10 text-center text-sm text-stone-500">
                Chưa có hoạt động gần đây
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <Card className="rounded-2xl border-white/80 bg-white/90 shadow-sm">
        <CardContent className="space-y-4 p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-xs font-semibold tracking-[0.18em] text-stone-400 uppercase">Endpoints</div>
              <h2 className="text-lg font-semibold tracking-tight">Top endpoints hôm nay</h2>
            </div>
            <Badge variant="outline" className="rounded-lg border-stone-200 bg-white text-stone-600">
              {summary?.calls.today_total || 0} lượt gọi
            </Badge>
          </div>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
            {(summary?.endpoints || []).map((item) => (
              <div key={item.endpoint} className="rounded-2xl border border-stone-100 px-4 py-3">
                <div className="truncate text-sm font-medium text-stone-900">{item.endpoint}</div>
                <div className="mt-1 text-xs text-stone-500">{item.count} lượt</div>
              </div>
            ))}
            {(summary?.endpoints || []).length === 0 ? (
              <div className="rounded-2xl border border-dashed border-stone-200 px-4 py-8 text-sm text-stone-500">
                Chưa có dữ liệu endpoint
              </div>
            ) : null}
          </div>
        </CardContent>
      </Card>
    </section>
  );
}

export default function DashboardPage() {
  const { isCheckingAuth, session } = useAuthGuard(["admin"]);
  if (isCheckingAuth || !session || session.role !== "admin") {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <LoaderCircle className="size-5 animate-spin text-stone-400" />
      </div>
    );
  }
  return <DashboardContent />;
}
