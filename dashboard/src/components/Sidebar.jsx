import React, { useState } from 'react';
import {
  LayoutDashboard,
  ReceiptText,
  Layers,
  AlertCircle,
  ShieldAlert,
  BarChart3,
  Cpu,
  FileText,
  Users,
  Settings,
  Search,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  Sparkles,
  HelpCircle
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, collapsed, setCollapsed }) {
  const [searchQuery, setSearchQuery] = useState('');

  const navSections = [
    {
      title: 'MONITOR',
      items: [
        { id: 'overview', label: 'Overview', icon: LayoutDashboard, badge: null },
        { id: 'transactions', label: 'Transactions', icon: ReceiptText, badge: '18.4k' },
        { id: 'settlements', label: 'Settlements', icon: Layers, badge: null },
        { id: 'disputes', label: 'Disputes', icon: AlertCircle, badge: '1 open', badgeColor: 'bg-rose-50 text-rose-600 border border-rose-200' },
        { id: 'fraud', label: 'Fraud Review', icon: ShieldAlert, badge: '3', badgeColor: 'bg-amber-50 text-amber-600 border border-amber-200' },
      ],
    },
    {
      title: 'PERFORMANCE',
      items: [
        { id: 'methods', label: 'Methods', icon: BarChart3, badge: null },
        { id: 'processors', label: 'Processors', icon: Cpu, badge: null },
        { id: 'reports', label: 'Reports', icon: FileText, badge: null },
      ],
    },
    {
      title: 'MANAGE',
      items: [
        { id: 'customers', label: 'Customers', icon: Users, badge: null },
        { id: 'settings', label: 'Settings', icon: Settings, badge: null },
      ],
    },
  ];

  return (
    <aside
      className={`fixed top-0 left-0 z-30 h-screen bg-white border-r border-slate-200/80 transition-all duration-300 flex flex-col justify-between select-none ${
        collapsed ? 'w-[72px]' : 'w-[240px]'
      }`}
    >
      {/* Brand Header */}
      <div className="p-4 flex items-center justify-between border-b border-slate-100">
        <div className="flex items-center gap-2.5 overflow-hidden">
          <div className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center font-bold text-base shadow-sm shadow-emerald-500/20 shrink-0">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="w-4 h-4">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v18m-6-12l6-6 6 6m-12 6l6 6 6-6" />
            </svg>
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-semibold text-[17px] text-slate-900 tracking-tight leading-none">
                Tender
              </span>
              <span className="text-[10px] text-slate-400 font-medium tracking-wide mt-0.5 uppercase">
                Fintech Engine
              </span>
            </div>
          )}
        </div>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Search Input Box */}
      <div className="px-3 pt-3">
        {!collapsed ? (
          <div className="relative flex items-center">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 w-3.5 h-3.5" />
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-12 py-1.5 bg-slate-50 hover:bg-slate-100/80 focus:bg-white text-xs border border-slate-200/90 rounded-lg text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-emerald-500/30 focus:border-emerald-500 transition-all"
            />
            <span className="absolute right-2 top-1/2 -translate-y-1/2 px-1 py-0.5 text-[10px] font-medium text-slate-400 bg-white border border-slate-200 rounded">
              ⌘ F
            </span>
          </div>
        ) : (
          <button
            onClick={() => setCollapsed(false)}
            className="w-full p-2 flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg"
          >
            <Search size={16} />
          </button>
        )}
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-5">
        {navSections.map((section) => (
          <div key={section.title} className="space-y-1">
            {!collapsed && (
              <div className="px-2 pb-1 text-[10px] font-semibold tracking-wider text-slate-400 uppercase">
                {section.title}
              </div>
            )}
            {section.items.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-[13px] font-medium transition-all group relative ${
                    isActive
                      ? 'bg-slate-100/90 text-slate-900 font-semibold shadow-2xs'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                  title={collapsed ? item.label : undefined}
                >
                  <Icon
                    size={16}
                    className={`shrink-0 transition-colors ${
                      isActive ? 'text-slate-900' : 'text-slate-400 group-hover:text-slate-600'
                    }`}
                  />
                  {!collapsed && (
                    <span className="truncate flex-1 text-left">{item.label}</span>
                  )}
                  {!collapsed && item.badge && (
                    <span
                      className={`text-[10px] font-medium px-1.5 py-0.2 rounded-full ${
                        item.badgeColor || 'bg-slate-100 text-slate-500'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                  {collapsed && isActive && (
                    <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-4 bg-emerald-600 rounded-l" />
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </div>

      {/* Footer Profile */}
      <div className="p-3 border-t border-slate-100 bg-slate-50/50">
        {!collapsed ? (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-slate-900 text-white font-semibold text-xs flex items-center justify-center ring-2 ring-emerald-500/30">
                MX
              </div>
              <div className="flex flex-col text-left">
                <span className="text-xs font-semibold text-slate-800 leading-tight">Maxx Vance</span>
                <span className="text-[10px] text-slate-400 leading-tight">Head of Payments</span>
              </div>
            </div>
            <button className="text-slate-400 hover:text-slate-600 p-1">
              <HelpCircle size={15} />
            </button>
          </div>
        ) : (
          <div className="flex justify-center">
            <div className="w-8 h-8 rounded-full bg-slate-900 text-white font-semibold text-xs flex items-center justify-center ring-2 ring-emerald-500/30">
              MX
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
