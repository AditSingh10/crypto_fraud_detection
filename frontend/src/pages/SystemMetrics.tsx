import React from 'react';

export const SystemMetrics: React.FC = () => {
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900 tracking-tight">System Metrics</h1>
        <p className="text-sm text-slate-500 mt-1">Infrastructure and streaming pipeline health</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded border border-slate-200 shadow-sm">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Throughput</div>
          <div className="text-3xl font-semibold text-slate-900">842 <span className="text-base font-normal text-slate-500">tx/s</span></div>
        </div>
        <div className="bg-white p-5 rounded border border-slate-200 shadow-sm">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">p99 Latency</div>
          <div className="text-3xl font-semibold text-slate-900">85 <span className="text-base font-normal text-slate-500">ms</span></div>
        </div>
        <div className="bg-white p-5 rounded border border-slate-200 shadow-sm">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Queue Size</div>
          <div className="text-3xl font-semibold text-slate-900">12 <span className="text-base font-normal text-slate-500">items</span></div>
        </div>
        <div className="bg-white p-5 rounded border border-slate-200 shadow-sm">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Error Rate</div>
          <div className="text-3xl font-semibold text-emerald-600">0.01%</div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6">
        <div className="bg-white p-6 rounded border border-slate-200 shadow-sm h-72 flex flex-col">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">Throughput Over Time</h3>
          <div className="flex-1 bg-slate-50 border border-slate-100 rounded flex items-center justify-center text-slate-400 text-sm">
            {/* TODO: Add system throughput chart */}
            [ Time Series Chart Placeholder ]
          </div>
        </div>
        
        <div className="bg-white p-6 rounded border border-slate-200 shadow-sm h-72 flex flex-col">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">Latency Distribution</h3>
          <div className="flex-1 bg-slate-50 border border-slate-100 rounded flex items-center justify-center text-slate-400 text-sm">
            {/* TODO: Add latency histogram */}
            [ Histogram Placeholder ]
          </div>
        </div>
      </div>
    </div>
  );
};
