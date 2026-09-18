import React from 'react';
import { ArrowUpRight, ArrowDownRight, AlertTriangle, CheckCircle2, Clock } from 'lucide-react';

export default function MetricSummaryCards({ currencySymbol = '$', onCardClick }) {
  const cards = [
    {
      id: 'auth_rate',
      title: 'Auth rate',
      value: '94.6%',
      subtext: '18,402 txns',
      statusText: '+0.8 pts vs last week',
      statusType: 'success', // emerald
      dotColor: 'bg-emerald-500',
      textColor: 'text-emerald-700',
      bgColor: 'bg-emerald-50/70',
      borderColor: 'border-emerald-200/80',
    },
    {
      id: 'decline_rate',
      title: 'Decline rate',
      value: '5.4%',
      subtext: '+0.3 pts',
      statusText: 'drift on BIN 441712',
      statusType: 'warning', // amber
      dotColor: 'bg-amber-500',
      textColor: 'text-amber-800',
      bgColor: 'bg-amber-50/70',
      borderColor: 'border-amber-200/80',
    },
    {
      id: 'settled',
      title: 'Settled',
      value: `${currencySymbol}1.39M`,
      subtext: `of ${currencySymbol}1.50M auth`,
      statusText: '96% complete',
      statusType: 'success', // emerald
      dotColor: 'bg-emerald-500',
      textColor: 'text-emerald-700',
      bgColor: 'bg-emerald-50/70',
      borderColor: 'border-emerald-200/80',
    },
    {
      id: 'disputes_open',
      title: 'Disputes open',
      value: '1',
      subtext: `${currencySymbol}1,755`,
      statusText: 'deadline 2 days',
      statusType: 'danger', // rose
      dotColor: 'bg-rose-500',
      textColor: 'text-rose-700',
      bgColor: 'bg-rose-50/70',
      borderColor: 'border-rose-200/80',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <div
          key={card.id}
          onClick={() => onCardClick && onCardClick(card.id)}
          className="bg-white rounded-xl border border-slate-200/80 p-4 shadow-2xs hover:border-slate-300 hover:shadow-xs transition-all cursor-pointer flex flex-col justify-between group"
        >
          {/* Title and Top Area */}
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-medium text-slate-500 group-hover:text-slate-700 transition-colors">
              {card.title}
            </span>
          </div>

          {/* Value & Subtext */}
          <div className="flex items-baseline gap-2 mb-3">
            <span className="text-2xl font-bold tracking-tight text-slate-900">
              {card.value}
            </span>
            {card.subtext && (
              <span className="text-xs font-normal text-slate-400">
                • {card.subtext}
              </span>
            )}
          </div>

          {/* Status Badge / Footer */}
          <div className="flex items-center">
            <div
              className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-medium border ${card.bgColor} ${card.borderColor} ${card.textColor}`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${card.dotColor}`} />
              <span>{card.statusText}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
