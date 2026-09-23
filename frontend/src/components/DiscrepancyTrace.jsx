import React from 'react';
import { Layers, ArrowRight, Database, AlertCircle } from 'lucide-react';

const DiscrepancyTrace = ({ trace }) => {
  if (!trace || trace.length === 0) {
    return (
      <div className="p-4 bg-slate-50 rounded-lg text-sm text-slate-500 flex items-center gap-2 border border-slate-200">
        <AlertCircle className="w-4 h-4 text-slate-400" />
        No intermediate computation trace steps recorded.
      </div>
    );
  }

  // Check if the trace contains an error or reason object
  if (trace.length === 1 && (trace[0].reason || trace[0].error)) {
    const info = trace[0];
    return (
      <div className="p-4 bg-amber-50 rounded-lg border border-amber-200 text-sm text-amber-900">
        <div className="font-semibold flex items-center gap-1.5 mb-1">
          <AlertCircle className="w-4 h-4 text-amber-600" />
          Unverifiable Reason: <span className="font-mono">{info.reason || 'unverifiable'}</span>
        </div>
        {info.error && <div className="text-xs text-amber-700 font-mono mt-1">{info.error}</div>}
      </div>
    );
  }

  return (
    <div className="overflow-hidden border border-slate-200 rounded-lg shadow-sm">
      <div className="bg-slate-50 px-4 py-2.5 border-b border-slate-200 flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-slate-500" />
          Deterministic Calculation Graph
        </span>
        <span className="text-xs text-slate-500">
          {trace.length} step{trace.length === 1 ? '' : 's'} derived
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50/50">
            <tr>
              <th scope="col" className="px-4 py-3 text-left font-semibold text-slate-700 text-xs uppercase tracking-wider">#</th>
              <th scope="col" className="px-4 py-3 text-left font-semibold text-slate-700 text-xs uppercase tracking-wider">Step Name</th>
              <th scope="col" className="px-4 py-3 text-left font-semibold text-slate-700 text-xs uppercase tracking-wider">Formula</th>
              <th scope="col" className="px-4 py-3 text-left font-semibold text-slate-700 text-xs uppercase tracking-wider">Computed Value</th>
              <th scope="col" className="px-4 py-3 text-left font-semibold text-slate-700 text-xs uppercase tracking-wider">Source Ground Truth</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 bg-white">
            {trace.map((step, idx) => {
              const stepName = step.step_name || step.step || `Step ${idx + 1}`;
              const formula = step.formula || '-';
              const value = step.computed_value !== undefined ? step.computed_value : (step.value !== undefined ? step.value : '-');
              const source = step.source_reference || step.source || 'Engine Computation';

              return (
                <tr key={idx} className="hover:bg-slate-50/75 transition-colors">
                  <td className="px-4 py-3 whitespace-nowrap text-xs text-slate-400 font-mono">
                    {idx + 1}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap font-medium text-slate-900 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                    {stepName}
                  </td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-1 bg-slate-100 border border-slate-200 rounded text-xs font-mono text-slate-800">
                      {formula}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap font-mono font-semibold text-slate-900">
                    {typeof value === 'number' ? value.toLocaleString(undefined, { maximumFractionDigits: 6 }) : String(value)}
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-600">
                    <span className="inline-flex items-center gap-1 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded text-slate-700 max-w-xs truncate" title={source}>
                      <Database className="w-3 h-3 text-slate-400 flex-shrink-0" />
                      <span className="truncate">{source}</span>
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DiscrepancyTrace;
