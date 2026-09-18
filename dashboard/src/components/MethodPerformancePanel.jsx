import React, { useState } from 'react';
import { CreditCard, ArrowUpRight, ShieldCheck, AlertCircle } from 'lucide-react';

export default function MethodPerformancePanel({ currencySymbol = '$', onSelectTransaction }) {
  const [activeTab, setActiveTab] = useState('at_risk'); // 'at_risk' or 'all'

  const atRiskTransactions = [
    {
      id: 'tx_8819',
      name: 'Marisol Okonkwo',
      method: 'Visa • 4417',
      amount: 4280.00,
      status: 'settled',
      statusLabel: 'settled',
      badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200/80',
      dotClass: 'bg-emerald-500',
    },
    {
      id: 'tx_3920',
      name: 'Dev Ramachandran',
      method: 'Amex • 1009',
      amount: 2910.50,
      status: 'pending',
      statusLabel: 'pending',
      badgeClass: 'bg-amber-50 text-amber-700 border-amber-200/80',
      dotClass: 'bg-amber-500',
    },
    {
      id: 'tx_7721',
      name: 'Hertz Fleet EU',
      method: 'MC • 8820',
      amount: 9640.00,
      status: 'delayed',
      statusLabel: 'delayed',
      badgeClass: 'bg-orange-50 text-orange-700 border-orange-200/80',
      dotClass: 'bg-orange-500',
    },
    {
      id: 'tx_1A2D5T',
      name: 'Léa Dubois',
      method: 'Wallet (BR)',
      amount: 1755.00,
      status: 'disputed',
      statusLabel: 'disputed',
      badgeClass: 'bg-rose-50 text-rose-700 border-rose-200/80',
      dotClass: 'bg-rose-500',
    },
  ];

  const topMethods = [
    { rank: '#1', name: 'Visa', share: '59.1%', successRate: '96.2%', volume: '840K' },
    { rank: '#2', name: 'Mastercard', share: '26.7%', successRate: '93.8%', volume: '380K' },
    { rank: '#3', name: 'Apple Pay', share: '7.7%', successRate: '98.1%', volume: '110K' },
    { rank: '#4', name: 'Amex', share: '4.6%', successRate: '91.4%', volume: '65K' },
    { rank: '#5', name: 'iDeal (NL)', share: '1.4%', successRate: '99.0%', volume: '20K' },
    { rank: '#6', name: 'Wallet (BR)', share: '0.5%', successRate: '88.5%', volume: '6.8K' },
  ];

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-2xs flex flex-col justify-between">
      {/* Top Header */}
      <div className="flex items-start justify-between pb-3 border-b border-slate-100 mb-3.5">
        <div>
          <h2 className="text-sm font-semibold text-slate-900 tracking-tight">
            Method Performance
          </h2>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Success & decline rates by method • yesterday.
          </p>
        </div>
      </div>

      {/* Content Grid: At-Risk & Top Methods */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* At-Risk Transactions Column */}
        <div>
          <div className="text-[11px] font-semibold text-slate-700 uppercase tracking-wider mb-2.5 flex items-center justify-between">
            <span>At-Risk Transactions</span>
            <span className="text-[10px] text-slate-400 font-normal">4 flagged</span>
          </div>

          <div className="space-y-2">
            {atRiskTransactions.map((tx) => (
              <div
                key={tx.id}
                onClick={() => onSelectTransaction && onSelectTransaction(tx)}
                className="p-2.5 rounded-lg border border-slate-100 hover:border-slate-200 hover:bg-slate-50/70 transition-all cursor-pointer flex items-center justify-between group"
              >
                <div className="flex flex-col">
                  <div className="flex items-center gap-1.5">
                    <span className={`w-1.5 h-1.5 rounded-full ${tx.dotClass}`} />
                    <span className="text-xs font-semibold text-slate-800 group-hover:text-emerald-700 transition-colors">
                      {tx.name}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-400 pl-3">
                    {tx.method}
                  </span>
                </div>

                <div className="flex flex-col items-end">
                  <span className="text-xs font-bold text-slate-900">
                    {currencySymbol}{tx.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>
                  <span
                    className={`mt-0.5 px-1.5 py-0.2 rounded text-[9px] font-semibold border ${tx.badgeClass}`}
                  >
                    {tx.statusLabel}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Methods Breakdown Column */}
        <div>
          <div className="text-[11px] font-semibold text-slate-700 uppercase tracking-wider mb-2.5 flex items-center justify-between">
            <span>Top Methods</span>
            <span className="text-[10px] text-slate-400 font-normal">Success Rate</span>
          </div>

          <div className="space-y-1.5">
            {topMethods.map((m) => (
              <div
                key={m.name}
                className="p-1.5 px-2 rounded-lg bg-slate-50/60 hover:bg-slate-50 border border-slate-100/80 flex items-center justify-between text-xs transition-colors"
              >
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono font-medium text-slate-400 w-4">
                    {m.rank}
                  </span>
                  <span className="font-medium text-slate-800 text-xs">
                    {m.name}
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-[10px] text-slate-400">
                    {currencySymbol}{m.volume}
                  </span>
                  <div className="flex items-center gap-1">
                    <span className="font-semibold text-slate-700 text-xs">
                      {m.successRate}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
