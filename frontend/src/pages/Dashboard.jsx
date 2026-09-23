import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { getLedger } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import { 
  FileSpreadsheet, 
  Search, 
  RefreshCw, 
  ChevronLeft, 
  ChevronRight, 
  ArrowUpRight,
  TrendingUp,
  AlertOctagon,
  CheckCircle2,
  HelpCircle,
  PlusCircle,
  FileText
} from 'lucide-react';

const Dashboard = () => {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [cikFilter, setCikFilter] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 15;

  useEffect(() => {
    fetchLedgerData();
  }, [statusFilter, cikFilter, page]);

  const fetchLedgerData = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
      };
      if (statusFilter) params.status = statusFilter;
      if (cikFilter) params.filing_cik = cikFilter;

      const data = await getLedger(params);
      const list = data.items || data.reports || data || [];
      setItems(list);
      setTotal(data.total !== undefined ? data.total : list.length);
    } catch (error) {
      console.error('Failed to fetch ledger', error);
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  // Compute live high-level statistics from the loaded items
  const stats = useMemo(() => {
    const passCount = items.filter(i => (i.status || '').toLowerCase() === 'pass').length;
    const warningCount = items.filter(i => (i.status || '').toLowerCase().includes('warning')).length;
    const failCount = items.filter(i => (i.status || '').toLowerCase() === 'fail').length;
    const unverifiableCount = items.filter(i => (i.status || '').toLowerCase() === 'unverifiable').length;

    return {
      total: total || items.length,
      pass: passCount,
      warning: warningCount,
      fail: failCount,
      unverifiable: unverifiableCount
    };
  }, [items, total]);

  const truncate = (str, len = 8) => {
    if (!str) return '-';
    return str.length > len ? str.substring(0, len) + '...' : str;
  };

  return (
    <div className="space-y-6">
      {/* Header section */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Audit Ledger & Reports</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Immutable post-hoc verification records anchored against SEC EDGAR ground truth.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchLedgerData()}
            className="inline-flex items-center gap-1.5 px-3 py-2 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 shadow-sm transition-colors"
            title="Refresh Ledger"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          <Link
            to="/submit"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition-colors"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>Submit Verification</span>
          </Link>
        </div>
      </div>

      {/* Metrics overview cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Total Certified</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">{stats.total}</p>
          </div>
          <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
            <FileSpreadsheet className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Verified Pass</p>
            <p className="text-2xl font-bold text-emerald-600 mt-1">{stats.pass}</p>
          </div>
          <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Warnings & Fails</p>
            <p className="text-2xl font-bold text-rose-600 mt-1">{stats.warning + stats.fail}</p>
          </div>
          <div className="w-10 h-10 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center">
            <AlertOctagon className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Unverifiable</p>
            <p className="text-2xl font-bold text-slate-600 mt-1">{stats.unverifiable}</p>
          </div>
          <div className="w-10 h-10 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center">
            <HelpCircle className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Filter and search bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row gap-3 items-center justify-between">
        <div className="flex flex-1 w-full sm:w-auto items-center gap-3">
          <div className="relative flex-1 sm:max-w-xs">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Filter by SEC CIK (e.g. 0000320193)..."
              value={cikFilter}
              onChange={(e) => {
                setCikFilter(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-1.5 text-sm border border-slate-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-slate-700"
          >
            <option value="">All Statuses</option>
            <option value="pass">Pass (≤ 0.2%)</option>
            <option value="pass_with_warning">Warning (0.2% - 1.0%)</option>
            <option value="fail">Fail (&gt; 1.0%)</option>
            <option value="unverifiable">Unverifiable</option>
          </select>
        </div>

        <div className="text-xs text-slate-500 whitespace-nowrap">
          Showing <span className="font-semibold text-slate-700">{items.length}</span> of <span className="font-semibold text-slate-700">{total}</span> records
        </div>
      </div>

      {/* Ledger Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-slate-500 space-y-3">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-blue-600" />
            <p className="text-sm">Querying verified ledger...</p>
          </div>
        ) : items.length === 0 ? (
          <div className="py-16 text-center text-slate-500 space-y-3">
            <FileText className="w-10 h-10 text-slate-300 mx-auto" />
            <p className="text-base font-semibold text-slate-700">No records found</p>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Submit your first LLM financial output for verification to start auditing calculations.
            </p>
            <Link
              to="/submit"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 transition-colors shadow-sm"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Submit Verification</span>
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th scope="col" className="px-5 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    Cert ID / Claim
                  </th>
                  <th scope="col" className="px-5 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    Status
                  </th>
                  <th scope="col" className="px-5 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    Expected Claimed
                  </th>
                  <th scope="col" className="px-5 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    Computed Truth
                  </th>
                  <th scope="col" className="px-5 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    Rel Error
                  </th>
                  <th scope="col" className="px-5 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    Issued At
                  </th>
                  <th scope="col" className="px-5 py-3 text-right text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {items.map((item) => {
                  const certId = item.cert_id || item.id || item.report_id;
                  const isReport = !item.cert_id && (item.report_id || item.form_type);

                  return (
                    <tr key={certId} className="hover:bg-slate-50/75 transition-colors">
                      <td className="px-5 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">
                            {truncate(certId, 8)}
                          </span>
                          {item.filing_cik && (
                            <span className="text-xs text-slate-500">
                              CIK {item.filing_cik}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-5 py-4 whitespace-nowrap">
                        <StatusBadge status={item.status} />
                      </td>
                      <td className="px-5 py-4 whitespace-nowrap font-mono text-xs text-slate-700">
                        {item.expected_value !== undefined && item.expected_value !== null
                          ? item.expected_value.toLocaleString(undefined, { maximumFractionDigits: 4 })
                          : '-'}
                      </td>
                      <td className="px-5 py-4 whitespace-nowrap font-mono text-xs text-slate-900 font-medium">
                        {item.computed_value !== undefined && item.computed_value !== null
                          ? item.computed_value.toLocaleString(undefined, { maximumFractionDigits: 4 })
                          : '-'}
                      </td>
                      <td className="px-5 py-4 whitespace-nowrap text-xs">
                        {item.relative_error !== undefined && item.relative_error !== null ? (
                          <span
                            className={`font-mono font-medium ${
                              item.relative_error <= 0.002
                                ? 'text-emerald-600'
                                : item.relative_error <= 0.01
                                ? 'text-amber-600'
                                : 'text-rose-600'
                            }`}
                          >
                            {(item.relative_error * 100).toFixed(3)}%
                          </span>
                        ) : (
                          <span className="text-slate-400">-</span>
                        )}
                      </td>
                      <td className="px-5 py-4 whitespace-nowrap text-xs text-slate-500">
                        {item.issued_at || item.submitted_at
                          ? new Date(item.issued_at || item.submitted_at).toLocaleDateString(undefined, {
                              year: 'numeric',
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                            })
                          : 'N/A'}
                      </td>
                      <td className="px-5 py-4 whitespace-nowrap text-right text-xs">
                        {isReport ? (
                          <Link
                            to={`/reports/${certId}`}
                            className="inline-flex items-center gap-1 font-semibold text-blue-600 hover:text-blue-800"
                          >
                            <span>Report Details</span>
                            <ArrowUpRight className="w-3.5 h-3.5" />
                          </Link>
                        ) : (
                          <Link
                            to={`/certificates/${certId}`}
                            className="inline-flex items-center gap-1 font-semibold text-blue-600 hover:text-blue-800"
                          >
                            <span>View Certificate</span>
                            <ArrowUpRight className="w-3.5 h-3.5" />
                          </Link>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination controls */}
        {total > pageSize && (
          <div className="bg-slate-50 px-5 py-3 border-t border-slate-200 flex items-center justify-between">
            <span className="text-xs text-slate-500">
              Page <span className="font-semibold text-slate-700">{page}</span> of{' '}
              <span className="font-semibold text-slate-700">{totalPages}</span>
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className={`p-1.5 rounded border border-slate-300 text-slate-600 bg-white hover:bg-slate-100 ${
                  page === 1 ? 'opacity-40 cursor-not-allowed' : ''
                }`}
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className={`p-1.5 rounded border border-slate-300 text-slate-600 bg-white hover:bg-slate-100 ${
                  page >= totalPages ? 'opacity-40 cursor-not-allowed' : ''
                }`}
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
