interface StatCardProps {
  label: string;
  value: string;
  accent?: string;
  description?: string;
}

export function StatCard({ label, value, accent = 'text-[#FFB703]', description }: StatCardProps) {
  return (
    <div className="rounded-[32px] border border-[#262626] bg-[#151515] p-6 shadow-glow">
      <p className="text-sm uppercase tracking-[0.24em] text-[#9CA3AF]">{label}</p>
      <p className={`mt-4 text-3xl font-semibold ${accent}`}>{value}</p>
      {description ? <p className="mt-2 text-sm text-[#9CA3AF]">{description}</p> : null}
    </div>
  );
}
