import { GlassPanel } from './GlassPanel';

const payouts = [
  { id: 'P-8743', recipient: '@crypto_ace', amount: '$1', status: 'Completed', date: '2026-08-03' },
  { id: 'P-8744', recipient: '@blockchain_guru', amount: '$1', status: 'Pending', date: '2026-08-03' },
  { id: 'P-8745', recipient: '@fintechqueen', amount: '$1', status: 'Failed', date: '2026-08-02' },
];

function StatusBadge({ status }: { status: string }) {
  const classes = {
    Completed: 'bg-[#10B981]/15 text-[#10B981]',
    Pending: 'bg-[#F59E0B]/15 text-[#F59E0B]',
    Failed: 'bg-[#EF4444]/15 text-[#EF4444]',
  };
  return <span className={`rounded-full px-3 py-1 text-xs font-semibold ${classes[status as keyof typeof classes]}`}>{status}</span>;
}

export function RecentPayoutsTable() {
  return (
    <GlassPanel>
      <div className="flex items-center justify-between gap-4 mb-6">
        <div>
          <p className="text-sm uppercase tracking-[0.24em] text-[#9CA3AF]">Recent payouts</p>
          <h2 className="mt-2 text-xl font-semibold">Payout activity</h2>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-[#262626] text-[#9CA3AF]">
              <th className="py-3 pr-6">Transaction</th>
              <th className="py-3 pr-6">Recipient</th>
              <th className="py-3 pr-6">Amount</th>
              <th className="py-3 pr-6">Status</th>
              <th className="py-3">Date</th>
            </tr>
          </thead>
          <tbody>
            {payouts.map((payout) => (
              <tr key={payout.id} className="border-b border-[#262626] transition hover:bg-white/5">
                <td className="py-4 pr-6 font-medium text-white">{payout.id}</td>
                <td className="py-4 pr-6 text-[#9CA3AF]">{payout.recipient}</td>
                <td className="py-4 pr-6 text-[#FFFFFF]">{payout.amount}</td>
                <td className="py-4 pr-6"><StatusBadge status={payout.status} /></td>
                <td className="py-4 text-[#9CA3AF]">{payout.date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </GlassPanel>
  );
}
