import React, { useState } from 'react';
import { ArrowUpDown, HelpCircle, CheckCircle2 } from 'lucide-react';

export default function ProcessorsTablePanel({ onSelectProcessor }) {
  const [sortField, setSortField] = useState('volume');
  const [sortAsc, setSortAsc] = useState(false);

  const processors = [
    {
      id: 'northwind',
      name: 'Northwind Acquiring',
      share: 29.5,
      color: 'bg-emerald-500',
      barColor: 'bg-emerald-500',
      effFee: '1.92%',
      disputeRate: '0.04%',
      successRate: 95.4,
      volumeUSD: '$419K',
    },
    {
      id: 'payflux',
      name: 'PayFlux Global',
      share: 23.4,
      color: 'bg-blue-500',
      barColor: 'bg-blue-500',
      effFee: '2.10%',
      disputeRate: '0.02%',
      successRate: 96.8,
      volumeUSD: '$332K',
    },
    {
      id: 'cardinal',
      name: 'Cardinal Merchant',
      share: 18.2,
      color: 'bg-violet-500',
      barColor: 'bg-violet-500',
      effFee: '1.85%',
      disputeRate: '0.08%',
      successRate: 93.1,
      volumeUSD: '$258K',
    },
    {
      id: 'adyen',
      name: 'Adyen Enterprise',
      share: 16.1,
      color: 'bg-sky-500',
      barColor: 'bg-sky-500',
      effFee: '2.05%',
      disputeRate: '0.01%',
      successRate: 97.9,
      volumeUSD: '$228K',
    },
    {
      id: 'chase',
      name: 'Chase Paymentech',
      share: 12.8,
      color: 'bg-amber-500',
      barColor: 'bg-amber-500',
      effFee: '1.98%',
      disputeRate: '0.05%',
      successRate: 94.2,
      volumeUSD: '$181K',
    },
  ];

  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const sortedProcessors = [...processors].sort((a, b) => {
    let aVal = a[sortField];
    let bVal = b[sortField];
    if (typeof aVal === 'string') aVal = parseFloat(aVal.replace('%', ''));
    if (typeof bVal === 'string') bVal = parseFloat(bVal.replace('%', ''));
    return sortAsc ? aVal - bVal : bVal - aVal;
  });

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-2xs flex flex-col justify-between">
      {/* Top Header */}
      <div>
        <div className="flex items-start justify-between pb-3 border-b border-slate-100 mb-3.5">
          <div>
            <h2 className="text-sm font-semibold text-slate-900 tracking-tight">
              Processors & Acquirers
            </h2>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Success rate, volume & disputes • last 30 days.
            </p>
          </div>
        </div>

        {/* Stacked Multi-Segment Progress Bar */}
        <div className="mb-3">
          <div className="h-3 w-full rounded-full flex overflow-hidden p-0.5 bg-slate-100 gap-0.5">
            {processors.map((p) => (
              <div
                key={p.id}
                className={`${p.barColor} h-full first:rounded-l-full last:rounded-r-full transition-all duration-500 hover:opacity-85`}
                style={{ width: `${p.share}%` }}
                title={`${p.name}: ${p.share}% share`}
              />
            ))}
          </div>

          {/* Segment Legend */}
          <div className="flex flex-wrap items-center gap-x-3.5 gap-y-1 mt-2 text-[11px] text-slate-600">
            {processors.map((p) => (
              <div key={p.id} className="flex items-center gap-1.5">
                <span className={`w-2 h-2 rounded-full ${p.color}`} />
                <span className="font-medium text-slate-700">{p.name.split(' ')[0]}</span>
                <span className="font-semibold text-slate-900">{p.share}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Data Table */}
        <div className="overflow-x-auto mt-4">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-100 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                <th className="pb-2 font-medium">Processor</th>
                <th className="pb-2 font-medium text-right cursor-pointer hover:text-slate-700" onClick={() => handleSort('effFee')}>
                  Eff Fee
                </th>
                <th className="pb-2 font-medium text-right cursor-pointer hover:text-slate-700" onClick={() => handleSort('disputeRate')}>
                  Dispute Rate
                </th>
                <th className="pb-2 font-medium text-right cursor-pointer hover:text-slate-700" onClick={() => handleSort('successRate')}>
                  Success Rate
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {sortedProcessors.map((p) => (
                <tr
                  key={p.id}
                  onClick={() => onSelectProcessor && onSelectProcessor(p)}
                  className="hover:bg-slate-50/80 transition-colors cursor-pointer group"
                >
                  <td className="py-2.5 flex items-center gap-2">
                    <span className={`w-1.5 h-1.5 rounded-full ${p.color}`} />
                    <span className="font-medium text-slate-800 group-hover:text-emerald-700 transition-colors">
                      {p.name}
                    </span>
                  </td>
                  <td className="py-2.5 text-right font-medium text-slate-600">
                    {p.effFee}
                  </td>
                  <td className="py-2.5 text-right font-medium text-slate-500">
                    {p.disputeRate}
                  </td>
                  <td className="py-2.5 text-right">
                    <div className="inline-flex items-center gap-1.5 justify-end">
                      <div className="w-12 h-1.5 bg-slate-100 rounded-full overflow-hidden hidden sm:block">
                        <div
                          className="h-full bg-emerald-500 rounded-full"
                          style={{ width: `${p.successRate}%` }}
                        />
                      </div>
                      <span className="font-semibold text-slate-800">
                        {p.successRate}%
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
