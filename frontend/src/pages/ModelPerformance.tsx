import React from 'react';

export const ModelPerformance: React.FC = () => {
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900 tracking-tight">Model Performance</h1>
        <p className="text-sm text-slate-500 mt-1">GAT-ResNet temporally trained evaluation metrics</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded border border-slate-200 shadow-sm">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">AUC-PR</div>
          <div className="text-3xl font-semibold text-slate-900">0.874</div>
        </div>
        <div className="bg-white p-5 rounded border border-slate-200 shadow-sm">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">MCC</div>
          <div className="text-3xl font-semibold text-slate-900">0.712</div>
        </div>
        <div className="bg-white p-5 rounded border border-slate-200 shadow-sm">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Precision (At Thresh)</div>
          <div className="text-3xl font-semibold text-slate-900">0.54</div>
        </div>
        <div className="bg-white p-5 rounded border border-slate-200 shadow-sm">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Recall (At Thresh)</div>
          <div className="text-3xl font-semibold text-slate-900">0.68</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded border border-slate-200 shadow-sm h-80 flex flex-col">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">Precision-Recall Curve</h3>
          <div className="flex-1 bg-slate-50 border border-slate-100 rounded flex items-center justify-center text-slate-400 text-sm">
            {/* TODO: Implement PR curve via Recharts / Chart.js */}
            [ PR Curve Chart Placeholder ]
          </div>
        </div>
        
        <div className="bg-white p-6 rounded border border-slate-200 shadow-sm h-80 flex flex-col">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">Threshold Sensitivity</h3>
          <div className="flex-1 bg-slate-50 border border-slate-100 rounded flex items-center justify-center text-slate-400 text-sm">
            {/* TODO: Implement sensitivity chart */}
            [ Sensitivity Chart Placeholder ]
          </div>
        </div>

        <div className="bg-white p-6 rounded border border-slate-200 shadow-sm col-span-1 md:col-span-2 flex flex-col">
          <h3 className="text-sm font-semibold text-slate-900 mb-6">Confusion Matrix (Threshold = 0.85)</h3>
          <div className="flex items-center justify-center py-4">
             <table className="text-sm border-collapse">
                <tbody>
                  <tr>
                    <td className="p-3 border border-slate-200 bg-slate-50 text-right font-medium text-slate-500"></td>
                    <td className="p-3 border border-slate-200 bg-slate-50 text-center font-medium text-slate-700 w-32">Pred Neg</td>
                    <td className="p-3 border border-slate-200 bg-slate-50 text-center font-medium text-slate-700 w-32">Pred Pos</td>
                  </tr>
                  <tr>
                    <td className="p-3 border border-slate-200 bg-slate-50 text-right font-medium text-slate-700">Actual Neg</td>
                    <td className="p-5 border border-slate-200 text-center bg-white text-slate-900 text-lg">1,204,500</td>
                    <td className="p-5 border border-slate-200 text-center bg-red-50 text-red-900 text-lg font-semibold">4,120</td>
                  </tr>
                  <tr>
                    <td className="p-3 border border-slate-200 bg-slate-50 text-right font-medium text-slate-700">Actual Pos</td>
                    <td className="p-5 border border-slate-200 text-center bg-red-50 text-red-900 text-lg font-semibold">2,300</td>
                    <td className="p-5 border border-slate-200 text-center bg-white text-slate-900 text-lg">4,890</td>
                  </tr>
                </tbody>
             </table>
          </div>
        </div>
      </div>
    </div>
  );
};
