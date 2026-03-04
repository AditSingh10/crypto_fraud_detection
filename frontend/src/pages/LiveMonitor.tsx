import React, { useState } from 'react';
import { Transaction } from '../types';
import { TransactionDrawer } from '../components/monitor/TransactionDrawer';

// Dummy data for visual scaffolding
const MOCK_TRANSACTIONS: Transaction[] = [
  { tx_id: '0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b', timestamp: Date.now() - 1000, amount: 45.2, illicit_probability: 0.92, threshold: 0.85, flagged: true, inference_latency_ms: 41 },
  { tx_id: '0x5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x', timestamp: Date.now() - 2500, amount: 1.5, illicit_probability: 0.12, threshold: 0.85, flagged: false, inference_latency_ms: 38 },
  { tx_id: '0x9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b', timestamp: Date.now() - 4000, amount: 1200.0, illicit_probability: 0.88, threshold: 0.85, flagged: true, inference_latency_ms: 45 },
  { tx_id: '0x3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f', timestamp: Date.now() - 5200, amount: 0.1, illicit_probability: 0.05, threshold: 0.85, flagged: false, inference_latency_ms: 40 },
  { tx_id: '0x7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3a4b5c6d', timestamp: Date.now() - 6100, amount: 8.4, illicit_probability: 0.45, threshold: 0.85, flagged: false, inference_latency_ms: 42 },
];

export const LiveMonitor: React.FC = () => {
  const [selectedTx, setSelectedTx] = useState<Transaction | null>(null);
  const [minProb, setMinProb] = useState<number>(0);
  const [flaggedOnly, setFlaggedOnly] = useState<boolean>(false);
  const [threshold, setThreshold] = useState<number>(0.85);
  const [isPaused, setIsPaused] = useState<boolean>(false);

  // TODO: Replace with actual WebSocket data stream from FastAPI backend
  const transactions = MOCK_TRANSACTIONS.filter(tx => {
    if (flaggedOnly && !tx.flagged) return false;
    if (tx.illicit_probability < minProb) return false;
    return true;
  });

  return (
    <div className="max-w-7xl mx-auto flex flex-col h-full">
      <div className="flex justify-between items-end mb-6 shrink-0">
        <div>
          <h1 className="text-xl font-semibold text-slate-900 tracking-tight">Live Monitoring Console</h1>
          <p className="text-sm text-slate-500 mt-1">Real-time blockchain transaction inference stream</p>
        </div>
        
        <div className="flex items-center space-x-4 bg-white p-2.5 rounded border border-slate-200 shadow-sm">
          <div className="flex items-center space-x-3 border-r border-slate-200 pr-4">
            <label className="text-sm font-medium text-slate-700 flex items-center">
              <span className="mr-3 w-32">Threshold: {(threshold * 100).toFixed(0)}%</span>
              <input 
                type="range" 
                min="0" max="1" step="0.01" 
                value={threshold} 
                onChange={e => setThreshold(parseFloat(e.target.value))}
                className="w-24 accent-slate-600"
              />
            </label>
          </div>
          <div className="flex items-center space-x-2 border-r border-slate-200 pr-4">
            <label className="text-sm text-slate-700 flex items-center cursor-pointer">
              <input 
                type="checkbox" 
                checked={flaggedOnly} 
                onChange={e => setFlaggedOnly(e.target.checked)}
                className="mr-2 rounded border-slate-300 text-slate-600 focus:ring-slate-500 cursor-pointer"
              />
              Flagged Only
            </label>
          </div>
          <button 
            onClick={() => setIsPaused(!isPaused)}
            className="text-sm font-medium px-4 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded transition-colors"
          >
            {isPaused ? '▶ Resume Stream' : '⏸ Pause Stream'}
          </button>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded flex-1 overflow-hidden flex flex-col shadow-sm">
        <div className="overflow-auto flex-1">
          <table className="min-w-full divide-y divide-slate-200 text-sm text-left">
            <thead className="bg-slate-50 sticky top-0 z-10 shadow-sm">
              <tr>
                <th className="px-6 py-3.5 font-semibold text-slate-600 uppercase tracking-wider text-xs">Time</th>
                <th className="px-6 py-3.5 font-semibold text-slate-600 uppercase tracking-wider text-xs">Tx Hash</th>
                <th className="px-6 py-3.5 font-semibold text-slate-600 uppercase tracking-wider text-xs text-right">Amount</th>
                <th className="px-6 py-3.5 font-semibold text-slate-600 uppercase tracking-wider text-xs text-right">Probability</th>
                <th className="px-6 py-3.5 font-semibold text-slate-600 uppercase tracking-wider text-xs text-center">Status</th>
                <th className="px-6 py-3.5 font-semibold text-slate-600 uppercase tracking-wider text-xs text-right">Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {transactions.map((tx) => (
                <tr 
                  key={tx.tx_id} 
                  onClick={() => setSelectedTx(tx)}
                  className="hover:bg-slate-50 cursor-pointer transition-colors"
                >
                  <td className="px-6 py-3 text-slate-500 whitespace-nowrap">
                    {new Date(tx.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="px-6 py-3 font-mono text-slate-600 truncate max-w-[200px]">
                    {tx.tx_id}
                  </td>
                  <td className="px-6 py-3 text-right text-slate-900 font-medium">
                    {tx.amount.toFixed(4)}
                  </td>
                  <td className="px-6 py-3 text-right">
                    <span className={tx.illicit_probability > threshold ? 'text-red-700 font-semibold' : 'text-slate-600'}>
                      {(tx.illicit_probability * 100).toFixed(2)}%
                    </span>
                  </td>
                  <td className="px-6 py-3 text-center">
                    {tx.flagged ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-50 text-red-700 border border-red-200">
                        Flagged
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-50 text-slate-600 border border-slate-200">
                        Cleared
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-3 text-right text-slate-400 font-mono text-xs">
                    {tx.inference_latency_ms}ms
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {transactions.length === 0 && (
            <div className="p-12 text-center text-slate-500 text-sm">
              No transactions matching current filters.
            </div>
          )}
        </div>
      </div>

      <TransactionDrawer transaction={selectedTx} onClose={() => setSelectedTx(null)} />
    </div>
  );
};
