"use client";

import React, { useState, useEffect } from "react";
import {
  Activity, Globe2, ShieldAlert, CheckCircle2,
  ArrowUpRight, ArrowDownRight, RefreshCcw, BookOpen, BarChart3, Wallet, Clock, Search
} from "lucide-react";

export default function TradingDesk() {
  const [selectedAction, setSelectedAction] = useState<"BUY" | "SELL">("BUY");
  const [activeMarket, setActiveMarket] = useState<"INDIA" | "US">("INDIA");
  const [ticker, setTicker] = useState("RELIANCE.NS");
  const [customTicker, setCustomTicker] = useState("");
  const [marketData, setMarketData] = useState<any>(null);
  const [simResult, setSimResult] = useState<any>(null);
  const [portfolio, setPortfolio] = useState<any>(null);
  const [analysisTab, setAnalysisTab] = useState<"QUANT" | "BEGINNER">("QUANT");
  const [loading, setLoading] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [orderQuantity, setOrderQuantity] = useState(1);
  const [orderSubmitting, setOrderSubmitting] = useState(false);

  const presets = {
    INDIA: ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "TATAMOTORS.NS"],
    US: ["NVDA", "AAPL", "MSFT", "TSLA", "GOOGL"],
  };

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  const loadMarket = async (sym: string) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/market/${sym}`);
      if (res.ok) {
        const data = await res.json();
        setMarketData(data);
      }
    } catch (err) {
      console.warn("Market fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadPortfolio = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/paper/portfolio`);
      if (res.ok) {
        const data = await res.json();
        setPortfolio(data);
      }
    } catch (err) {
      console.warn("Portfolio fetch error:", err);
    }
  };

  const handleSelectTicker = (sym: string) => {
    const cleanSym = sym.trim().toUpperCase();
    if (!cleanSym) return;
    setTicker(cleanSym);
    setSimResult(null); // Clear previous consensus diagnosis
    loadMarket(cleanSym);
  };

  const switchMarket = (market: "INDIA" | "US") => {
    setActiveMarket(market);
    const nextTicker = market === "INDIA" ? "RELIANCE.NS" : "NVDA";
    setTicker(nextTicker);
    setSimResult(null);
    loadMarket(nextTicker);
  };

  const handleCustomSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (customTicker.trim()) {
      handleSelectTicker(customTicker.trim());
      setCustomTicker("");
    }
  };

  const runSimulation = async () => {
    setSimulating(true);
    try {
      const res = await fetch(`${API_BASE}/api/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker }),
      });
      if (res.ok) {
        const data = await res.json();
        setSimResult(data);

        // Sync execution button to audited consensus with manual override allowed
        if (data.final_action === "BUY" || data.final_action === "SELL") {
          setSelectedAction(data.final_action);
        }
      }
    } catch (err) {
      console.error("Simulation error:", err);
    } finally {
      setSimulating(false);
    }
  };

  const executeTrade = async (action: "BUY" | "SELL") => {
    if (!marketData) return;
    setOrderSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/paper/order`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker,
          action,
          quantity: orderQuantity,
          current_price: marketData.current_price,
        }),
      });
      if (res.ok) {
        alert(`Executed paper ${action} order for ${orderQuantity} share(s) of ${ticker}.`);
        await loadPortfolio();
      } else {
        const err = await res.json().catch(() => ({ detail: "Order rejected." }));
        alert(err.detail || "Order failed.");
      }
    } catch (err: any) {
      alert("Execution error: " + err.message);
    } finally {
      setOrderSubmitting(false);
    }
  };

  useEffect(() => {
    loadMarket(ticker);
    loadPortfolio();
  }, []);

  const renderChart = () => {
    if (!marketData?.candles || marketData.candles.length === 0) return null;
    const candles = marketData.candles;
    const closes = candles.map((c: any) => c.close);
    const min = Math.min(...closes);
    const max = Math.max(...closes);
    const range = max - min || 1;
    const width = 600;
    const height = 140;

    const points = candles.map((c: any, i: number) => {
      const x = (i / (candles.length - 1)) * width;
      const y = height - ((c.close - min) / range) * (height - 20) - 10;
      return `${x},${y}`;
    }).join(" ");

    return (
      <div className="w-full bg-slate-900 rounded-2xl p-5 text-white shadow-sm flex flex-col justify-between">
        <div className="flex justify-between items-center mb-2">
          <span className="text-xs font-semibold text-slate-400">6-Month Price Trend ({ticker})</span>
          <span className="text-xs font-bold text-emerald-400">{marketData.currency_symbol || marketData.currency}{Number(marketData.current_price).toFixed(2)}</span>
        </div>
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-28 overflow-visible">
          <polyline
            fill="none"
            stroke="#10b981"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={points}
          />
        </svg>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans antialiased pb-16">
      {/* Top Header */}
      <header className="border-b border-slate-200 bg-white sticky top-0 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-blue-600 text-white p-2 rounded-xl font-bold flex items-center justify-center">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-bold text-slate-900 text-base leading-tight">Autonomous Trading Desk</h1>
              <p className="text-xs text-slate-500 font-medium">Neuro-Symbolic Consensus · Dual Execution Desk</p>
            </div>
          </div>

          <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200">
            <button
              onClick={() => switchMarket("INDIA")}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeMarket === "INDIA"
                  ? "bg-white text-blue-700 shadow-sm border border-slate-200/80"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              🇮🇳 Indian Market (NSE)
            </button>
            <button
              onClick={() => switchMarket("US")}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeMarket === "US"
                  ? "bg-white text-blue-700 shadow-sm border border-slate-200/80"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              🇺🇸 US Market (NASDAQ/NYSE)
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-6 pt-6 space-y-6">
        {/* Watchlist & Search Action Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Watchlist:</span>
            {presets[activeMarket].map((sym) => (
              <button
                key={sym}
                onClick={() => handleSelectTicker(sym)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  ticker === sym
                    ? "bg-blue-50 text-blue-700 border border-blue-200 shadow-xs"
                    : "bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200/60"
                }`}
              >
                {sym}
              </button>
            ))}

            {/* Custom Search Input */}
            <form onSubmit={handleCustomSearch} className="flex items-center ml-2">
              <div className="relative flex items-center">
                <input
                  type="text"
                  placeholder="Custom Ticker (e.g. INFY.NS)"
                  value={customTicker}
                  onChange={(e) => setCustomTicker(e.target.value)}
                  className="w-44 px-3 py-1.5 pl-7 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500 font-semibold"
                />
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2 pointer-events-none" />
              </div>
              <button
                type="submit"
                className="ml-1.5 px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-lg border border-slate-200 transition-colors"
              >
                Go
              </button>
            </form>
          </div>

          <button
            onClick={runSimulation}
            disabled={simulating || loading}
            className="flex items-center space-x-2 bg-slate-900 hover:bg-blue-600 text-white px-5 py-2.5 rounded-xl text-xs font-bold transition-all disabled:opacity-50 cursor-pointer"
          >
            <RefreshCcw className={`w-3.5 h-3.5 ${simulating ? "animate-spin" : ""}`} />
            <span>{simulating ? `Synthesizing ${ticker} Consensus...` : `Run Consensus (${ticker})`}</span>
          </button>
        </div>

        {/* Primary Market KPI Cards */}
        {marketData && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Current Price</span>
              <div className="flex items-baseline space-x-2 mt-2">
                <span className="text-2xl font-black text-slate-900">
                  {marketData.currency_symbol || marketData.currency}{Number(marketData.current_price).toFixed(2)}
                </span>
                <span className={`text-xs font-bold flex items-center ${marketData.change_pct >= 0 ? "text-emerald-600" : "text-rose-600"}`}>
                  {marketData.change_pct >= 0 ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                  {Math.abs(marketData.change_pct).toFixed(2)}%
                </span>
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">RSI (14-Period)</span>
              <div className="text-2xl font-black text-slate-900 mt-2">{Number(marketData.rsi).toFixed(1)}</div>
              <span className="text-[11px] font-semibold text-slate-400">
                {marketData.rsi > 70 ? "Overbought" : marketData.rsi < 30 ? "Oversold" : "Neutral Zone"}
              </span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">20-Day SMA</span>
              <div className="text-2xl font-black text-slate-900 mt-2">{marketData.currency_symbol || marketData.currency}{Number(marketData.sma_20).toFixed(2)}</div>
              <span className="text-[11px] font-semibold text-slate-400">Short-Term Baseline</span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">50-Day SMA</span>
              <div className="text-2xl font-black text-slate-900 mt-2">{marketData.currency_symbol || marketData.currency}{Number(marketData.sma_50).toFixed(2)}</div>
              <span className="text-[11px] font-semibold text-slate-400">Medium-Term Baseline</span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">P/E Valuation</span>
              <div className="text-2xl font-black text-slate-900 mt-2">
                {marketData.pe_ratio > 0 ? Number(marketData.pe_ratio).toFixed(1) : "N/A"}
              </div>
              <span className="text-[11px] font-semibold text-slate-400">Earnings Multiple</span>
            </div>
          </div>
        )}

        {/* Chart + Attribution Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {renderChart()}

          {marketData?.attribution && (
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3 flex flex-col justify-between">
              <div>
                <div className="flex items-center space-x-2 mb-2">
                  <Globe2 className="w-4 h-4 text-blue-600" />
                  <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                    Macro & Catalyst Attribution: {marketData.ticker}
                  </h2>
                  <span className="bg-blue-100 text-blue-800 text-[10px] font-extrabold px-2 py-0.5 rounded-full uppercase">
                    {marketData.attribution.category}
                  </span>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-xs text-slate-700 mb-2">
                  <span className="font-bold text-slate-500 uppercase text-[10px] block mb-1">Market Contagion Drivers</span>
                  {marketData.attribution.drivers?.[0] || "Asset movement driven by idiosyncratic volume."}
                </div>
              </div>
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-xs text-slate-800 italic">
                <span className="font-bold text-slate-500 uppercase text-[10px] block mb-1 not-italic">Top Corporate Catalyst</span>
                "{marketData.attribution.headline}"
              </div>
            </div>
          )}
        </div>

        {/* Multi-Agent Consensus & Deterministic Risk Execution */}
        {simResult && (
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h3 className="font-bold text-base text-slate-900">Consensus & Deterministic Risk Audit ({simResult.ticker})</h3>
                <p className="text-xs text-slate-400">Audited against 5.0% allocation cap and 70.0% confidence floor</p>
              </div>

              {simResult.override_triggered ? (
                <div className="flex items-center space-x-2 bg-rose-50 text-rose-700 border border-rose-200 px-3.5 py-1.5 rounded-xl text-xs font-bold">
                  <ShieldAlert className="w-4 h-4" />
                  <span>Circuit Breaker Enforced</span>
                </div>
              ) : (
                <div className="flex items-center space-x-2 bg-emerald-50 text-emerald-700 border border-emerald-200 px-3.5 py-1.5 rounded-xl text-xs font-bold">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Safety Bounds Verified</span>
                </div>
              )}
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 text-center">
                <span className="text-xs font-medium text-slate-400">Audited Decision</span>
                <div className={`mt-1 font-black text-2xl tracking-wide ${
                  simResult.final_action === "BUY" ? "text-emerald-600" : simResult.final_action === "SELL" ? "text-rose-600" : "text-amber-600"
                }`}>
                  {simResult.final_action}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 text-center">
                <span className="text-xs font-medium text-slate-400">Consensus Confidence</span>
                <div className="mt-1 font-black text-2xl text-slate-800">
                  {(Number(simResult.confidence_score) * 100).toFixed(1)}%
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 text-center">
                <span className="text-xs font-medium text-slate-400">Allocated Capital</span>
                <div className="mt-1 font-black text-2xl text-slate-800">
                  {(Number(simResult.final_allocation_pct) * 100).toFixed(1)}%
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 text-center">
                <span className="text-xs font-medium text-slate-400">Stop-Loss Buffer</span>
                <div className="mt-1 font-black text-2xl text-slate-800">±2.5% Dynamic</div>
              </div>
            </div>

            {/* Rationale */}
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
              <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">Adversarial Debate Synthesis</p>
              <p className="text-xs text-slate-800 font-medium leading-relaxed">{simResult.rationale}</p>
            </div>

            {/* Dual Mode Pedagogical Tab */}
            <div className="border border-slate-200 rounded-xl overflow-hidden">
              <div className="flex items-center border-b border-slate-200 bg-slate-50">
                <button
                  onClick={() => setAnalysisTab("QUANT")}
                  className={`flex items-center space-x-2 px-5 py-3 text-xs font-bold transition-all ${
                    analysisTab === "QUANT" ? "bg-white text-blue-700 border-r border-slate-200" : "text-slate-500 hover:text-slate-800"
                  }`}
                >
                  <BarChart3 className="w-4 h-4" />
                  <span>Institutional Quant Metrics (Sharpe / Volatility)</span>
                </button>
                <button
                  onClick={() => setAnalysisTab("BEGINNER")}
                  className={`flex items-center space-x-2 px-5 py-3 text-xs font-bold transition-all ${
                    analysisTab === "BEGINNER" ? "bg-white text-blue-700 border-l border-r border-slate-200" : "text-slate-500 hover:text-slate-800"
                  }`}
                >
                  <BookOpen className="w-4 h-4" />
                  <span>Beginner Investor Briefing (ELI5 Guidance)</span>
                </button>
              </div>

              <div className="p-5 bg-white">
                {analysisTab === "BEGINNER" ? (
                  <div className="space-y-4">
                    <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl">
                      <p className="text-xs font-bold text-amber-800 uppercase tracking-wide">Plain-Language Risk Warning</p>
                      <p className="text-xs text-amber-900 mt-1 leading-relaxed">
                        {simResult.analysis?.beginner_guidance?.plain_risk_warning}
                      </p>
                    </div>

                    <div className="bg-blue-50 border border-blue-200 p-4 rounded-xl">
                      <p className="text-xs font-bold text-blue-800 uppercase tracking-wide">Tangible Currency Scenario</p>
                      <p className="text-xs text-blue-900 mt-1 leading-relaxed font-medium">
                        {simResult.analysis?.beginner_guidance?.tangible_currency_scenario}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                      <span className="text-xs text-slate-400">Sharpe Ratio</span>
                      <p className="text-xl font-bold text-slate-900 mt-1">{simResult.analysis?.quant_metrics?.sharpe_ratio}</p>
                    </div>
                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                      <span className="text-xs text-slate-400">Sortino Ratio</span>
                      <p className="text-xl font-bold text-slate-900 mt-1">{simResult.analysis?.quant_metrics?.sortino_ratio}</p>
                    </div>
                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                      <span className="text-xs text-slate-400">Realized Volatility</span>
                      <p className="text-xl font-bold text-slate-900 mt-1">{simResult.analysis?.quant_metrics?.realized_volatility_pct}%</p>
                    </div>
                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                      <span className="text-xs text-slate-400">Max Drawdown</span>
                      <p className="text-xl font-bold text-slate-900 mt-1">{simResult.analysis?.quant_metrics?.max_drawdown_pct}%</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Paper Execution Bar */}
            <div className="bg-slate-900 text-white p-5 rounded-2xl flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Deploy Paper Order ({ticker})
                </p>
                <p className="text-xs text-slate-300 mt-0.5">
                  Simulates execution slippage (0.05% - 0.15%) and credits/debits the isolated currency vault.
                </p>
              </div>

              <div className="flex items-center space-x-3">
                <div className="flex bg-slate-800 p-1 rounded-xl border border-slate-700">
                  <button
                    type="button"
                    onClick={() => setSelectedAction("BUY")}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                      selectedAction === "BUY" ? "bg-emerald-600 text-white shadow-xs" : "text-slate-400 hover:text-white"
                    }`}
                  >
                    BUY
                  </button>
                  <button
                    type="button"
                    onClick={() => setSelectedAction("SELL")}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                      selectedAction === "SELL" ? "bg-rose-600 text-white shadow-xs" : "text-slate-400 hover:text-white"
                    }`}
                  >
                    SELL
                  </button>
                </div>

                <input
                  type="number"
                  min="1"
                  value={orderQuantity}
                  onChange={(e) => setOrderQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                  className="w-20 px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs font-bold text-center"
                />

                <button
                  onClick={() => executeTrade(selectedAction)}
                  disabled={orderSubmitting}
                  className={`px-5 py-2 rounded-xl text-xs font-bold transition-all disabled:opacity-50 cursor-pointer ${
                    selectedAction === "BUY"
                      ? "bg-emerald-600 hover:bg-emerald-500 text-white"
                      : "bg-rose-600 hover:bg-rose-500 text-white"
                  }`}
                >
                  {orderSubmitting ? "Routing..." : `Place ${selectedAction} Order`}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Paper Portfolio Ledger & Order Book Fills */}
        {portfolio && (
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Wallet className="w-5 h-5 text-blue-600" />
                <h3 className="font-bold text-sm text-slate-900">Paper Trading Cash Vaults</h3>
              </div>
              <span className="text-xs text-slate-400 font-medium">Total Orders Logged: {portfolio.total_trades}</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                <span className="text-xs font-medium text-slate-400">🇮🇳 Indian Cash Vault (NSE)</span>
                <p className="text-2xl font-bold text-slate-900 mt-1">₹{Number(portfolio.inr_cash).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</p>
              </div>
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                <span className="text-xs font-medium text-slate-400">🇺🇸 US Cash Vault (USD)</span>
                <p className="text-2xl font-bold text-slate-900 mt-1">${Number(portfolio.usd_cash).toLocaleString("en-US", { minimumFractionDigits: 2 })}</p>
              </div>
            </div>

            {/* Recent Executed Orders Table */}
            {portfolio.recent_orders && portfolio.recent_orders.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-slate-500" />
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">Executed Order Book & Bracket Stops</h4>
                </div>
                <div className="border border-slate-200 rounded-xl overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase">
                      <tr>
                        <th className="px-4 py-3">Order ID</th>
                        <th className="px-4 py-3">Asset</th>
                        <th className="px-4 py-3">Action</th>
                        <th className="px-4 py-3">Quantity</th>
                        <th className="px-4 py-3">Fill Price</th>
                        <th className="px-4 py-3">Stop-Loss</th>
                        <th className="px-4 py-3">Take-Profit</th>
                        <th className="px-4 py-3">Brokerage Fee</th>
                        <th className="px-4 py-3">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {portfolio.recent_orders.map((o: any) => (
                        <tr key={o.id} className="hover:bg-slate-50/50">
                          <td className="px-4 py-2.5 font-mono text-slate-400">#{o.id}</td>
                          <td className="px-4 py-2.5 font-bold text-slate-800">{o.ticker}</td>
                          <td className="px-4 py-2.5">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              o.action === "BUY" ? "bg-emerald-100 text-emerald-800" : "bg-rose-100 text-rose-800"
                            }`}>
                              {o.action}
                            </span>
                          </td>
                          <td className="px-4 py-2.5 text-slate-700 font-semibold">{o.quantity}</td>
                          <td className="px-4 py-2.5 font-bold text-slate-900">{o.executed_price}</td>
                          <td className="px-4 py-2.5 text-rose-600 font-medium">{o.stop_loss}</td>
                          <td className="px-4 py-2.5 text-emerald-600 font-medium">{o.take_profit}</td>
                          <td className="px-4 py-2.5 text-slate-400">{o.fee}</td>
                          <td className="px-4 py-2.5">
                            <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full text-[10px] font-semibold">
                              {o.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}