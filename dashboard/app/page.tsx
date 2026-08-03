import { ActivityTimeline } from '../components/ActivityTimeline';
import { OverviewStatsGrid } from '../components/OverviewStatsGrid';
import { RecentSubmissionsTable } from '../components/RecentSubmissionsTable';
import { RecentPayoutsTable } from '../components/RecentPayoutsTable';

export default function Home() {
  return (
    <main className="min-h-screen bg-[#0B0B0B] p-6 text-white">
      <div className="mx-auto max-w-[1600px] space-y-6">
        <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.28em] text-[#FFB703]/80">Admin dashboard</p>
            <h1 className="mt-2 text-3xl font-semibold">Bybit UID Verification Hub</h1>
            <p className="mt-2 max-w-2xl text-sm text-[#9CA3AF]">
              Monitor verified UIDs, payouts, user activity, and system health in one premium dashboard.
            </p>
          </div>
        </header>

        <OverviewStatsGrid />

        <div className="grid gap-6 xl:grid-cols-[1.4fr_0.8fr]">
          <div className="space-y-6">
            <RecentSubmissionsTable />
            <RecentPayoutsTable />
          </div>
          <ActivityTimeline />
        </div>
      </div>
    </main>
  );
}
