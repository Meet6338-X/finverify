import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getReport } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import DiscrepancyTrace from '../components/DiscrepancyTrace';
import { 
  ArrowLeft, 
  FileText, 
  Building2, 
  Calendar, 
  Cpu, 
  Download, 
  ChevronDown, 
  ChevronUp, 
  ExternalLink,
  ShieldCheck,
  AlertCircle
} from 'lucide-react';

const ReportDetail = () => {
  const { reportId } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedCert, setExpandedCert] = useState(null);

  useEffect(() => {
    const fetchReport = async () => {
      setLoading(true);
      try {
        const data = await getReport(reportId);
        setReport(data);
      } catch (error) {
        console.error('Failed to fetch report', error);
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
  }, [reportId]);

  if (loading) {
    return (
      <div className="py-20 text-center text-slate-500 space-y-2">
        <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
        <p className="text-sm">Loading report details...</p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="bg-white p-12 rounded-xl border border-slate-200 text-center space-y-4 max-w-lg mx-auto shadow-sm">
        <AlertCircle className="w-12 h-12 text-rose-500 mx-auto" />
        <h2 className="text-lg font-bold text-slate-900">Report Not Found</h2>
        <p className="text-sm text-slate-500">
          The requested verification report could not be found or has not completed processing yet.
        </p>
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 transition-colors shadow-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </Link>
      </div>
    );
  }

  // Parse summary stats from report summary payload or calculate
  const summary = report.summary || {};
  const certificates = report.certificates || [];
  const totalClaims = summary.total_claims || certificates.length;
  const passedClaims = summary.passed !== undefined ? summary.passed : certificates.filter(c => (c.status || '').toLowerCase() === 'pass').length;
  const failedClaims = summary.failed !== undefined ? summary.failed : certificates.filter(c => (c.status || '').toLowerCase() === 'fail').length;
  const warningClaims = summary.warnings !== undefined ? summary.warnings : certificates.filter(c => (c.status || '').toLowerCase().includes('warning')).length;
  const unverifiableClaims = summary.unverifiable !== undefined ? summary.unverifiable : certificates.filter(c => (c.status || '').toLowerCase() === 'unverifiable').length;

  const toggleExpand = (certId) => {
    setExpandedCert(expandedCert === certId ? null : certId);
  };

  return (
    <div className="space-y-6">
      {/* Top navigation */}
      <div className="flex items-center justify-between">
        <Link
          to="/"
          className="inline-flex items-center gap-1 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Ledger</span>
        </Link>
      </div>

      {/* Report Header Card */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-900">
                Verification Report
              </h1>
              <StatusBadge status={report.status} size="lg" />
            </div>
            <p className="text-xs font-mono text-slate-500">ID: {report.report_id}</p>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Calendar className="w-4 h-4 text-slate-400" />
            <span>
              Submitted:{' '}
              {report.submitted_at
                ? new Date(report.submitted_at).toLocaleString()
                : 'N/A'}
            </span>
          </div>
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
          <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-100">
            <span className="text-xs font-medium text-slate-500 flex items-center gap-1 mb-1">
              <Building2 className="w-3.5 h-3.5 text-slate-400" /> Subject SEC CIK
            </span>
            <span className="font-semibold text-slate-900 font-mono">{report.filing_cik}</span>
          </div>

          <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-100">
            <span className="text-xs font-medium text-slate-500 flex items-center gap-1 mb-1">
              <FileText className="w-3.5 h-3.5 text-slate-400" /> Filing Period / Form
            </span>
            <span className="font-semibold text-slate-900">
              {report.filing_period} ({report.form_type})
            </span>
          </div>

          <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-100">
            <span className="text-xs font-medium text-slate-500 flex items-center gap-1 mb-1">
              <Cpu className="w-3.5 h-3.5 text-slate-400" /> LLM Model Audited
            </span>
            <span className="font-semibold text-slate-900">{report.llm_model || 'Generic Model'}</span>
          </div>

          <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-100">
            <span className="text-xs font-medium text-slate-500 flex items-center gap-1 mb-1">
              <ShieldCheck className="w-3.5 h-3.5 text-slate-400" /> Signing Protocol
            </span>
            <span className="font-semibold text-slate-900">Ed25519 (RFC 8032)</span>
          </div>
        </div>
      </div>

      {/* Summary Stat Breakdown Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
          <p className="text-xs font-medium text-slate-500">Total Claims</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">{totalClaims}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
          <p className="text-xs font-medium text-emerald-600">Passed (≤0.2%)</p>
          <p className="text-2xl font-bold text-emerald-600 mt-1">{passedClaims}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
          <p className="text-xs font-medium text-amber-600">Warnings (≤1.0%)</p>
          <p className="text-2xl font-bold text-amber-600 mt-1">{warningClaims}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
          <p className="text-xs font-medium text-rose-600">Failed (&gt;1.0%)</p>
          <p className="text-2xl font-bold text-rose-600 mt-1">{failedClaims}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center col-span-2 sm:col-span-1">
          <p className="text-xs font-medium text-slate-600">Unverifiable</p>
          <p className="text-2xl font-bold text-slate-600 mt-1">{unverifiableClaims}</p>
        </div>
      </div>

      {/* Claims List Section */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <span>Audited Numerical Claims</span>
            <span className="px-2 py-0.5 rounded-full bg-slate-100 text-xs font-semibold text-slate-600">
              {certificates.length}
            </span>
          </h2>
        </div>

        {certificates.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">
            No claim certificates recorded for this report.
          </div>
        ) : (
          <div className="divide-y divide-slate-200">
            {certificates.map((cert) => {
              const isExpanded = expandedCert === cert.cert_id;

              return (
                <div key={cert.cert_id} className="transition-colors hover:bg-slate-50/50">
                  <div className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">
                          {cert.cert_id.substring(0, 8)}...
                        </span>
                        <StatusBadge status={cert.status} />
                        {cert.relative_error !== null && cert.relative_error !== undefined && (
                          <span className="text-xs font-mono text-slate-500">
                            Rel Error: {(cert.relative_error * 100).toFixed(3)}%
                          </span>
                        )}
                      </div>
                      <p className="text-sm font-medium text-slate-900">
                        {cert.claim_text || `Claim ${cert.claim_id.substring(0, 8)}...`}
                      </p>
                    </div>

                    <div className="flex items-center gap-3 self-end md:self-center">
                      <button
                        onClick={() => toggleExpand(cert.cert_id)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded text-xs font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors"
                      >
                        <span>{isExpanded ? 'Hide Trace' : 'Inspect Math'}</span>
                        {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      </button>

                      <Link
                        to={`/certificates/${cert.cert_id}`}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded text-xs font-semibold text-blue-600 bg-blue-50 hover:bg-blue-100 border border-blue-200 transition-colors"
                      >
                        <span>Full Certificate</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  </div>

                  {/* Expanded Trace Accordion */}
                  {isExpanded && (
                    <div className="px-5 pb-5 pt-1 bg-slate-50/70 border-t border-slate-100 space-y-4">
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                        <div className="bg-white p-2.5 rounded border border-slate-200">
                          <span className="text-slate-400 block">Claim Expected:</span>
                          <span className="font-semibold text-slate-900 font-mono">
                            {cert.expected_value !== null ? cert.expected_value : 'N/A'}
                          </span>
                        </div>
                        <div className="bg-white p-2.5 rounded border border-slate-200">
                          <span className="text-slate-400 block">Computed Truth:</span>
                          <span className="font-semibold text-slate-900 font-mono">
                            {cert.computed_value !== null ? cert.computed_value : 'N/A'}
                          </span>
                        </div>
                        <div className="bg-white p-2.5 rounded border border-slate-200">
                          <span className="text-slate-400 block">Relative Discrepancy:</span>
                          <span className="font-semibold text-slate-900 font-mono">
                            {cert.relative_error !== null ? (cert.relative_error * 100).toFixed(4) + '%' : 'N/A'}
                          </span>
                        </div>
                        <div className="bg-white p-2.5 rounded border border-slate-200">
                          <span className="text-slate-400 block">Issued Timestamp:</span>
                          <span className="font-semibold text-slate-900">
                            {cert.issued_at ? new Date(cert.issued_at).toLocaleTimeString() : 'N/A'}
                          </span>
                        </div>
                      </div>

                      {cert.discrepancy_trace && (
                        <DiscrepancyTrace trace={cert.discrepancy_trace} />
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportDetail;
