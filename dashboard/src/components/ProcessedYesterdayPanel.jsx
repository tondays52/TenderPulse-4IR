import React, { useState } from 'react';
import { ChevronDown, Edit3, Check, TrendingUp, HelpCircle } from 'lucide-react';

export default function ProcessedYesterdayPanel({ currencySymbol = '$' }) {
  const [sourceFilter, setSourceFilter] = useState('All Sources');
  const [filterOpen, setFilterOpen] = useState(false);
  const [targetVal, setTargetVal] = useState(95.0);
  const [isEditingTarget, setIsEditingTarget] = useState(false);

  const sources = [
    'All Sources',
    'Northwind Core (US)',
    'PayFlux Global (EU)',
    'Adyen Enterprise',
    'Direct APM Channels',
  ];

  const currentAuthRate = 94.6;
  const gap = (targetVal - currentAuthRate).toFixed(1);
  const progressPercent = Math.min(100, Math.round((currentAuthRate / targetVal) * 100));

  const stats = [
    { label: 'Authorized', value: `${currencySymbol}1.50M`, dot: 'bg-emerald-500' },
    { label: 'Settled', value: `${currencySymbol}1.39M`, dot: 'bg-teal-500' },
    { label: 'Refunded', value: `${currencySymbol}79.6K`, dot: 'bg-rose-500' },
    { label: 'Pending', value: `${currencySymbol}31K`, dot: 'bg-amber-500' },
  ];

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-2xs flex flex-col justify-between">
      {/* Top Header Row */}
      <div>
        <div className="flex items-start justify-between pb-3 border-b border-slate-100 mb-4">
          <div>
            <h2 className="text-sm font-semibold text-slate-900 tracking-tight">
              Processed Yesterday
            </h2>
            <p className="text-[11px] text-slate-400 mt-0.5">
              21 Jun 2026 • 18,402 transactions • avg ticket {currencySymbol}77.27
            </p>
          </div>

          {/* Sources Dropdown */}
          <div className="relative">
            <button
              onClick={() => setFilterOpen(!filterOpen)}
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-slate-700 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors"
            >
              <span>{sourceFilter}</span>
              <ChevronDown size={12} className="text-slate-400" />
            </button>

            {filterOpen && (
              <div className="absolute right-0 mt-1.5 w-44 bg-white border border-slate-200 rounded-xl shadow-lg py-1 z-20 text-xs animate-in fade-in zoom-in-95">
                {sources.map((s) => (
                  <button
                    key={s}
                    onClick={() => {
                      setSourceFilter(s);
                      setFilterOpen(false);
                    }}
                    className="w-full text-left px-3 py-1.5 hover:bg-slate-50 text-slate-700 flex items-center justify-between"
                  >
                    <span>{s}</span>
                    {sourceFilter === s && <Check size={12} className="text-emerald-600" />}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Total Processed Amount */}
        <div className="mb-4">
          <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider mb-1">
            Total processed
          </div>
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
              {currencySymbol}1,421,880
            </span>
            <div className="flex items-center gap-1.5">
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200/80">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                94.6% auth rate
              </span>
              <span className="text-[11px] text-slate-400 font-normal">
                • 8/8 sources live
              </span>
            </div>
          </div>
        </div>

        {/* Breakdown Metric Tiles */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mb-5">
          {stats.map((s) => (
            <div
              key={s.label}
              className="p-3 bg-slate-50/70 hover:bg-slate-50 border border-slate-100 rounded-xl transition-all"
            >
              <div className="flex items-center gap-1.5 text-[11px] font-medium text-slate-500 mb-1">
                <span className={`w-2 h-2 rounded-full ${s.dot}`} />
                <span>{s.label}</span>
              </div>
              <div className="text-base font-bold text-slate-800 tracking-tight">
                {s.value}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Target Progress Bar Section */}
      <div className="pt-3 border-t border-dashed border-slate-200">
        <div className="flex items-center justify-between mb-2 text-xs">
          <span className="font-semibold text-slate-800">Auth rate vs target</span>
          <button
            onClick={() => setIsEditingTarget(!isEditingTarget)}
            className="flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100/80 px-2 py-0.5 rounded-md border border-emerald-200/60 transition-colors"
          >
            <Edit3 size={11} />
            <span>{targetVal.toFixed(1)}% target</span>
          </button>
        </div>

        {isEditingTarget && (
          <div className="mb-2 p-2 bg-emerald-50/50 border border-emerald-100 rounded-lg flex items-center justify-between text-xs">
            <span className="text-emerald-900 font-medium text-[11px]">Adjust Target (%):</span>
            <div className="flex items-center gap-1.5">
              <input
                type="number"
                step="0.1"
                min="80"
                max="99.9"
                value={targetVal}
                onChange={(e) => setTargetVal(parseFloat(e.target.value) || 95)}
                className="w-16 px-1.5 py-0.5 text-xs bg-white border border-emerald-300 rounded text-right font-semibold text-emerald-900"
              />
              <button
                onClick={() => setIsEditingTarget(false)}
                className="px-2 py-0.5 bg-emerald-600 text-white rounded text-[11px] font-medium hover:bg-emerald-700"
              >
                Save
              </button>
            </div>
          </div>
        )}

        <div className="flex items-center justify-between text-[11px] text-slate-500 mb-1.5">
          <span>{gap > 0 ? `${gap} pts to reach your ${targetVal.toFixed(1)}% target` : 'Target achieved! 🎉'}</span>
          <span className="font-semibold text-slate-700">{currentAuthRate}% / {targetVal.toFixed(1)}%</span>
        </div>

        {/* Dynamic Dual Gradient Bar */}
        <div className="relative w-full h-3 bg-slate-100 rounded-full overflow-hidden p-0.5">
          <div
            className="h-full bg-gradient-to-r from-teal-500 via-emerald-500 to-emerald-600 rounded-full transition-all duration-700 shadow-xs"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>
    </div>
  );
}
