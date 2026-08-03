'use client';

import { motion } from 'framer-motion';
import { Clock3 } from 'lucide-react';

const events = [
  { time: '2m ago', label: 'New UID submitted', description: 'User @crypto_ace submitted a new Bybit UID for review.', variant: 'info' },
  { time: '12m ago', label: 'Payout completed', description: 'Reward payout sent to @blockchain_guru via Binance.', variant: 'success' },
  { time: '35m ago', label: 'UID rejected', description: 'Submission BYB11121 was rejected for invalid UID format.', variant: 'danger' },
];

function eventColor(variant: string) {
  return variant === 'success'
    ? 'bg-[#10B981]'
    : variant === 'danger'
    ? 'bg-[#EF4444]'
    : 'bg-[#FFB703]';
}

export function ActivityTimeline() {
  return (
    <div className="rounded-[32px] border border-[#262626] bg-[rgba(23,23,23,0.72)] p-6 shadow-glow backdrop-blur-xl">
      <div className="flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-3xl bg-[#111111] text-[#FFB703]">
          <Clock3 size={20} />
        </div>
        <div>
          <p className="text-sm uppercase tracking-[0.24em] text-[#9CA3AF]">Activity timeline</p>
          <h2 className="text-xl font-semibold text-white">Live review feed</h2>
        </div>
      </div>

      <div className="mt-8 space-y-6">
        {events.map((event) => (
          <motion.div
            key={event.time + event.label}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
            className="flex items-start gap-4"
          >
            <span className={`mt-2 h-3.5 w-3.5 rounded-full ${eventColor(event.variant)}`}></span>
            <div>
              <p className="font-semibold text-white">{event.label}</p>
              <p className="mt-1 text-sm text-[#9CA3AF]">{event.description}</p>
              <p className="mt-2 text-xs uppercase tracking-[0.2em] text-[#6B7280]">{event.time}</p>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
