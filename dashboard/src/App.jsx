import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import TopNav from './components/TopNav';
import MetricSummaryCards from './components/MetricSummaryCards';
import ProcessedYesterdayPanel from './components/ProcessedYesterdayPanel';
import MethodPerformancePanel from './components/MethodPerformancePanel';
import AttentionItemsPanel from './components/AttentionItemsPanel';
import ProcessorsTablePanel from './components/ProcessorsTablePanel';
import ModalDetail from './components/ModalDetail';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [currency, setCurrency] = useState('USD');
  const [dateRange, setDateRange] = useState('yesterday');
  
  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [modalData, setModalData] = useState(null);
  const [modalType, setModalType] = useState('');

  const currencySymbols = {
    USD: '$',
    EUR: '€',
    GBP: '£',
    CAD: 'CA$',
  };

  const symbol = currencySymbols[currency] || '$';

  const handleSelectTransaction = (tx) => {
    setModalData(tx);
    setModalType('transaction');
    setModalOpen(true);
  };

  const handleAttentionAction = (item) => {
    setModalData(item);
    setModalType('attention');
    setModalOpen(true);
  };

  const handleSelectProcessor = (proc) => {
    setModalData(proc);
    setModalType('processor');
    setModalOpen(true);
  };

  const handleCardClick = (cardId) => {
    setModalData({
      title: `Metric Deep-Dive: ${cardId.replace('_', ' ').toUpperCase()}`,
      description: `Detailed time-series telemetry and authorization logs for ${cardId}. All automated routing rules operating within standard 99.9% uptime SLA.`,
      id: `METRIC_${cardId.toUpperCase()}`
    });
    setModalType('metric');
    setModalOpen(true);
  };

  const handleExport = () => {
    const csvContent = "data:text/csv;charset=utf-8,Category,Value,Status\nTotal Processed,$1421880,94.6% Auth\nAuthorized,$1500000,Success\nSettled,$1390000,96% Complete\nRefunded,$79600,Processed\nPending,$31000,In Review";
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `tender_summary_${dateRange}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 flex">
      {/* Fixed Vertical Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        collapsed={sidebarCollapsed}
        setCollapsed={setSidebarCollapsed}
      />

      {/* Main Content Area */}
      <div
        className={`flex-1 flex flex-col min-w-0 transition-all duration-300 ${
          sidebarCollapsed ? 'ml-[72px]' : 'ml-[240px]'
        }`}
      >
        {/* Sticky Top Navigation Bar */}
        <TopNav
          activeTab={activeTab}
          currency={currency}
          setCurrency={setCurrency}
          dateRange={dateRange}
          setDateRange={setDateRange}
          onExportReport={handleExport}
        />

        {/* Dashboard Main Scrollable Area */}
        <main className="flex-1 p-6 md:p-8 max-w-[1440px] w-full mx-auto space-y-6">
          {/* Executive Greeting Header */}
          <div className="flex flex-col gap-1">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">
              Good morning, Maxx.
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 font-normal">
              Lumora: <span className="font-semibold text-slate-700">{symbol}1.42M</span> processed yesterday,{' '}
              <span className="font-semibold text-emerald-600">94.6% auth</span> (+0.8 pts WoW); travel volume +22% vs baseline.
            </p>
          </div>

          {/* Top Row: 4 Metric Summary Cards */}
          <section aria-label="Metric Summary Cards">
            <MetricSummaryCards
              currencySymbol={symbol}
              onCardClick={handleCardClick}
            />
          </section>

          {/* Middle Row: Split Column Grid */}
          <section className="grid grid-cols-1 lg:grid-cols-12 gap-6" aria-label="Processed & Method Performance">
            <div className="lg:col-span-7 flex flex-col">
              <ProcessedYesterdayPanel currencySymbol={symbol} />
            </div>
            <div className="lg:col-span-5 flex flex-col">
              <MethodPerformancePanel
                currencySymbol={symbol}
                onSelectTransaction={handleSelectTransaction}
              />
            </div>
          </section>

          {/* Bottom Row: Attention Items & Processors Table */}
          <section className="grid grid-cols-1 lg:grid-cols-12 gap-6" aria-label="Attention Items and Processors">
            <div className="lg:col-span-6 flex flex-col">
              <AttentionItemsPanel onItemAction={handleAttentionAction} />
            </div>
            <div className="lg:col-span-6 flex flex-col">
              <ProcessorsTablePanel onSelectProcessor={handleSelectProcessor} />
            </div>
          </section>
        </main>
      </div>

      {/* Global Interactive Modal */}
      <ModalDetail
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        data={modalData}
        type={modalType}
      />
    </div>
  );
}
