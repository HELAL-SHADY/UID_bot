import { StatCard } from './StatCard';

export function OverviewStatsGrid() {
  return (
    <div className="grid gap-6 xl:grid-cols-4 lg:grid-cols-2">
      <StatCard label="Total Submitted UIDs" value="1,248" />
      <StatCard label="Pending Reviews" value="82" accent="text-[#F59E0B]" />
      <StatCard label="Approved UIDs" value="936" accent="text-[#10B981]" />
      <StatCard label="Rejected UIDs" value="230" accent="text-[#EF4444]" />
      <StatCard label="Total Rewards Paid" value="$14,820" accent="text-[#FFB703]" />
      <StatCard label="Binance Wallet Balance" value="$41,703" accent="text-[#FFFFFF]" />
      <StatCard label="Today’s Submissions" value="47" />
      <StatCard label="Today’s Payments" value="28" accent="text-[#10B981]" />
    </div>
  );
}
