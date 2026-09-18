import React, { useState } from 'react';
import { ChevronDown, ArrowRight, AlertTriangle, Clock, ShieldAlert, Check } from 'lucide-react';

export default function AttentionItemsPanel({ onItemAction }) {
  const [filterCount, setFilterCount] = useState('All 5 items');
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const attentionItems = [
    {
      id: 'bin_spike',
      type: 'critical',
      title: 'Decline-rate spike on Visa BIN 441712',
      description: '14.2% in 6h vs 4.8% baseline (UK issuers) • ~$18K/day at risk',
      actionText: 'Open BIN breakdown →',
      actionKey: 'bin',
      dotColor: 'bg-rose-500',
    },
    {
      id: 'chargeback_deadline',
      type: 'danger',
      title: 'Chargeback deadline in 2 days',
      description: 'tx_1A2D5T • $1,755 BR • representment due 24 Jun, evidence missing',
      actionText: 'Open dispute →',
      actionKey: 'dispute',
      dotColor: 'bg-rose-500',
    },
    {
      id: 'settlement_delay',
      type: 'warning',
      title: 'Settlement delayed — Northwind Acquiring',
      description: '$214K batch • 6h past the expected payout window',
      actionText: 'View settlement →',
      actionKey: 'settlement',
      dotColor: 'bg-amber-500',
    },
    {
      id: 'threeds_anomaly',
      type: 'info',
      title: '3D Secure fallback anomaly on Apple Pay',
      description: 'Cardholder auth routing dropping back to 2DS on iOS 19.4',
      actionText: 'Inspect logs →',
      actionKey: 'logs',
      dotColor: 'bg-blue-500',
    },
    {
      id: 'velocity_burst',
      type: 'warning',
      title: 'High-velocity burst detected from IP subnet 185.220.*',
      description: '28 attempts in 3 mins, 82% fraud score threshold exceeded',
      actionText: 'Review rule →',
      actionKey: 'rule',
      dotColor: 'bg-amber-500',
    },
  ];

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-2xs flex flex-col justify-between">
      {/* Top Header */}
      <div>
        <div className="flex items-start justify-between pb-3 border-b border-slate-100 mb-3.5">
          <div>
            <h2 className="text-sm font-semibold text-slate-900 tracking-tight">
              What Needs Your Attention
            </h2>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Ranked by dollar impact • updated 14 min ago
            </p>
          </div>

          {/* Filter Dropdown */}
          <div className="relative">
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-slate-700 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors"
            >
              <span>{filterCount}</span>
              <ChevronDown size={12} className="text-slate-400" />
            </button>

            {dropdownOpen && (
              <div className="absolute right-0 mt-1.5 w-36 bg-white border border-slate-200 rounded-xl shadow-lg py-1 z-20 text-xs animate-in fade-in zoom-in-95">
                {['All 5 items', 'High Priority', 'Settlements', 'Security'].map((f) => (
                  <button
                    key={f}
                    onClick={() => {
                      setFilterCount(f);
                      setDropdownOpen(false);
                    }}
                    className="w-full text-left px-3 py-1.5 hover:bg-slate-50 text-slate-700 flex items-center justify-between"
                  >
                    <span>{f}</span>
                    {filterCount === f && <Check size={12} className="text-emerald-600" />}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* List of Attention Cards */}
        <div className="space-y-2.5">
          {attentionItems.map((item) => (
            <div
              key={item.id}
              className="p-3 bg-slate-50/50 hover:bg-slate-50/90 border border-slate-100 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 transition-all group hover:border-slate-200"
            >
              <div className="flex items-start gap-2.5">
                <span className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${item.dotColor}`} />
                <div>
                  <h4 className="text-xs font-semibold text-slate-900 group-hover:text-emerald-800 transition-colors">
                    {item.title}
                  </h4>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    {item.description}
                  </p>
                </div>
              </div>

              <button
                onClick={() => onItemAction && onItemAction(item)}
                className="shrink-0 inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 hover:text-emerald-800 hover:underline transition-colors pl-4.5 sm:pl-0 self-end sm:self-center"
              >
                <span>{item.actionText}</span>
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
