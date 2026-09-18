import React from 'react';
import { X, CheckCircle, AlertTriangle, ShieldCheck, ArrowRight, ExternalLink, RefreshCw } from 'lucide-react';

export default function ModalDetail({ isOpen, onClose, data, type }) {
  if (!isOpen || !data) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-in fade-in">
      <div
        className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-lg w-full overflow-hidden animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <h3 className="font-semibold text-sm text-slate-900">
              {data.title || data.name || 'Detail Inspection'}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-4 text-xs">
          {data.description && (
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 text-slate-700">
              <span className="font-semibold block mb-0.5 text-slate-900">Overview</span>
              {data.description}
            </div>
          )}

          {data.method && (
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                  Payment Method
                </span>
                <span className="text-xs font-semibold text-slate-800">
                  {data.method}
                </span>
              </div>
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                  Amount
                </span>
                <span className="text-xs font-bold text-slate-900">
                  ${data.amount?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </span>
              </div>
            </div>
          )}

          {data.effFee && (
            <div className="grid grid-cols-3 gap-2">
              <div className="p-2.5 bg-slate-50 rounded-lg text-center">
                <span className="text-[10px] text-slate-400 block font-medium">Effective Fee</span>
                <span className="font-bold text-slate-800">{data.effFee}</span>
              </div>
              <div className="p-2.5 bg-slate-50 rounded-lg text-center">
                <span className="text-[10px] text-slate-400 block font-medium">Dispute Rate</span>
                <span className="font-bold text-slate-800">{data.disputeRate}</span>
              </div>
              <div className="p-2.5 bg-slate-50 rounded-lg text-center">
                <span className="text-[10px] text-slate-400 block font-medium">Success Rate</span>
                <span className="font-bold text-emerald-700">{data.successRate}%</span>
              </div>
            </div>
          )}

          {/* Simulated Live Telemetry Feed */}
          <div className="space-y-1.5 pt-1">
            <span className="text-[11px] font-semibold text-slate-700 block">
              Audit Logs & Telemetry
            </span>
            <div className="p-2.5 bg-slate-900 text-slate-200 rounded-lg font-mono text-[11px] space-y-1 overflow-x-auto">
              <div className="text-emerald-400">[2026-06-21 08:14:02 UTC] Routing engine matched gateway tier-1</div>
              <div className="text-slate-400">[2026-06-21 08:14:03 UTC] 3DS token verified • Issuer: NatWest</div>
              <div className="text-amber-400">[2026-06-21 08:14:04 UTC] Latency: 114ms • Status: 200 OK</div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
          <span className="text-[11px] text-slate-400">
            ID: <span className="font-mono text-slate-600">{data.id || 'REF_9921'}</span>
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-3 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-200/60 rounded-lg transition-colors"
            >
              Close
            </button>
            <button
              onClick={() => {
                alert(`Action dispatched successfully for ${data.title || data.name}!`);
                onClose();
              }}
              className="px-3.5 py-1.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-sm shadow-emerald-600/20 transition-all flex items-center gap-1.5"
            >
              <span>Execute Action</span>
              <ArrowRight size={13} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
