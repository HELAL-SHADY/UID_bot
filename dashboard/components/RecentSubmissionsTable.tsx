import { GlassPanel } from './GlassPanel';

const rows = [
  { user: '@crypto_ace', uid: 'BYB12345', date: '2026-08-03', status: 'Pending', reward: '$1' },
  { user: '@blockchain_guru', uid: 'BYB67890', date: '2026-08-03', status: 'Approved', reward: '$1' },
  { user: '@fintechqueen', uid: 'BYB11121', date: '2026-08-02', status: 'Rejected', reward: '$0' },
];

function StatusBadge({ status }: { status: string }) {
  const classes = {
    Pending: 'bg-[#F59E0B]/15 text-[#F59E0B]',
    Approved: 'bg-[#10B981]/15 text-[#10B981]',
    Rejected: 'bg-[#EF4444]/15 text-[#EF4444]',
  };
  return <span className={`rounded-full px-3 py-1 text-xs font-semibold ${classes[status as keyof typeof classes]}`}>{status}</span>;
}

export function RecentSubmissionsTable() {
  return (
    <GlassPanel>
      <div className="flex items-center justify-between gap-4 mb-6">
        <div>
          <p className="text-sm uppercase tracking-[0.24em] text-[#9CA3AF]">Recent submissions</p>
          <h2 className="mt-2 text-xl font-semibold">Latest UID approvals</h2>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-[#262626] text-[#9CA3AF]">
              <th className="py-3 pr-6">User</th>
              <th className="py-3 pr-6">Bybit UID</th>
              <th className="py-3 pr-6">Date</th>
              <th className="py-3 pr-6">Status</th>
              <th className="py-3">Reward</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.uid} className="border-b border-[#262626] transition hover:bg-white/5">
                <td className="py-4 pr-6 font-medium text-white">{row.user}</td>
                <td className="py-4 pr-6 text-[#9CA3AF]">{row.uid}</td>
                <td className="py-4 pr-6 text-[#9CA3AF]">{row.date}</td>
                <td className="py-4 pr-6"><StatusBadge status={row.status} /></td>
                <td className="py-4 text-[#FFFFFF]">{row.reward}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </GlassPanel>
  );
}
