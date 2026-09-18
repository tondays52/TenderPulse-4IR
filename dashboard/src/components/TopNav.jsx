import React, { useState } from 'react';
import {
  Grid,
  Calendar,
  ChevronDown,
  DollarSign,
  Bell,
  SlidersHorizontal,
  Download,
  Share2,
  Check
} from 'lucide-react';

export default function TopNav({
  activeTab,
  currency,
  setCurrency,
  dateRange,
  setDateRange,
  onExportReport
}) {
  const [currencyOpen, setCurrencyOpen] = useState(false);
  const [dateOpen, setDateOpen] = useState(false);
  const [notificationOpen, setNotificationOpen] = useState(false);

  const currencies = [
    { code: 'USD', symbol: '$', label: 'US Dollar (USD)' },
    { code: 'EUR', symbol: '€', label: 'Euro (EUR)' },
    { code: 'GBP', symbol: '£', label: 'British Pound (GBP)' },
    { code: 'CAD', symbol: 'CA$', label: 'Canadian Dollar (CAD)' },
  ];

  const dateOptions = [
    { id: 'yesterday', label: 'Yesterday', dateText: '21 Jun 2026' },
    { id: '7d', label: 'Last 7 days', dateText: '15 Jun – 21 Jun 2026' },
    { id: '30d', label: 'Last 30 days', dateText: '22 May – 21 Jun 2026' },
    { id: 'custom', label: 'Custom Range', dateText: '2 Aug – 18 Sep 2026' },
  ];

  const selectedDate = dateOptions.find((d) => d.id === dateRange) || dateOptions[0];

  return (
    <header className="sticky top-0 z-20 bg-white/90 backdrop-blur-md border-b border-slate-200/80 px-6 py-2.5 flex items-center justify-between transition-all">
      {/* Breadcrumb Left */}
      <div className="flex items-center gap-2 text-xs font-medium text-slate-500">
        <Grid size={14} className="text-slate-400" />
        <span>Monitor</span>
        <span className="text-slate-300">/</span>
        <span className="text-slate-900 font-semibold capitalize">{activeTab}</span>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-2.5">
        {/* Currency Switcher Dropdown */}
        <div className="relative">
          <button
            onClick={() => {
              setCurrencyOpen(!currencyOpen);
              setDateOpen(false);
              setNotificationOpen(false);
            }}
            className="flex items-center gap-1.5 px-2.5 py-1.5 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 shadow-2xs hover:border-slate-300 transition-all"
          >
            <span>{currency}</span>
            <ChevronDown size={13} className="text-slate-400" />
          </button>

          {currencyOpen && (
            <div className="absolute right-0 mt-1.5 w-44 bg-white border border-slate-200 rounded-xl shadow-lg shadow-slate-200/50 py-1 z-30 text-xs animate-in fade-in zoom-in-95">
              <div className="px-3 py-1.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                Select Currency
              </div>
              {currencies.map((c) => (
                <button
                  key={c.code}
                  onClick={() => {
                    setCurrency(c.code);
                    setCurrencyOpen(false);
                  }}
                  className={`w-full flex items-center justify-between px-3 py-1.5 hover:bg-slate-50 transition-colors text-left ${
                    currency === c.code ? 'text-emerald-700 font-semibold bg-emerald-50/50' : 'text-slate-700'
                  }`}
                >
                  <span>{c.label}</span>
                  {currency === c.code && <Check size={13} className="text-emerald-600" />}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Date Filter Dropdown */}
        <div className="relative">
          <button
            onClick={() => {
              setDateOpen(!dateOpen);
              setCurrencyOpen(false);
              setNotificationOpen(false);
            }}
            className="flex items-center gap-2 px-3 py-1.5 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 shadow-2xs hover:border-slate-300 transition-all"
          >
            <Calendar size={13} className="text-slate-500" />
            <span className="font-semibold text-slate-800">{selectedDate.label}</span>
            <span className="text-slate-300">|</span>
            <span className="text-slate-500 text-[11px]">{selectedDate.dateText}</span>
            <ChevronDown size={13} className="text-slate-400 ml-0.5" />
          </button>

          {dateOpen && (
            <div className="absolute right-0 mt-1.5 w-56 bg-white border border-slate-200 rounded-xl shadow-lg shadow-slate-200/50 py-1.5 z-30 text-xs animate-in fade-in zoom-in-95">
              <div className="px-3 py-1 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                Date Preset
              </div>
              {dateOptions.map((opt) => (
                <button
                  key={opt.id}
                  onClick={() => {
                    setDateRange(opt.id);
                    setDateOpen(false);
                  }}
                  className={`w-full flex flex-col px-3 py-1.5 hover:bg-slate-50 transition-colors text-left ${
                    dateRange === opt.id ? 'bg-emerald-50/60 font-semibold' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className={dateRange === opt.id ? 'text-emerald-800' : 'text-slate-800'}>
                      {opt.label}
                    </span>
                    {dateRange === opt.id && <Check size={13} className="text-emerald-600" />}
                  </div>
                  <span className="text-[10px] text-slate-400">{opt.dateText}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Quick Action Export / Share */}
        <button
          onClick={onExportReport}
          className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg border border-slate-200 transition-colors"
          title="Export CSV Summary"
        >
          <Download size={14} />
        </button>

        {/* Notification Bell */}
        <div className="relative">
          <button
            onClick={() => setNotificationOpen(!notificationOpen)}
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg border border-slate-200 transition-colors relative"
            title="System alerts"
          >
            <Bell size={14} />
            <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-rose-500 rounded-full ring-2 ring-white"></span>
          </button>

          {notificationOpen && (
            <div className="absolute right-0 mt-1.5 w-72 bg-white border border-slate-200 rounded-xl shadow-lg p-3 z-30 text-xs animate-in fade-in zoom-in-95">
              <div className="flex items-center justify-between pb-2 border-b border-slate-100 mb-2">
                <span className="font-semibold text-slate-800">Alerts & Actions</span>
                <span className="text-[10px] bg-emerald-100 text-emerald-800 font-semibold px-1.5 py-0.5 rounded">
                  Live
                </span>
              </div>
              <div className="space-y-2">
                <div className="p-2 rounded-lg bg-rose-50/60 border border-rose-100 flex flex-col gap-0.5">
                  <div className="flex items-center justify-between font-semibold text-rose-800 text-[11px]">
                    <span>BIN 441712 Spike</span>
                    <span className="text-[9px] text-rose-500">6m ago</span>
                  </div>
                  <p className="text-[10px] text-rose-700">14.2% decline rate detected on UK issuers.</p>
                </div>
                <div className="p-2 rounded-lg bg-amber-50/60 border border-amber-100 flex flex-col gap-0.5">
                  <div className="flex items-center justify-between font-semibold text-amber-800 text-[11px]">
                    <span>Chargeback Deadline</span>
                    <span className="text-[9px] text-amber-500">2h ago</span>
                  </div>
                  <p className="text-[10px] text-amber-700">tx_1A2D5T evidence submission due in 48 hours.</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
