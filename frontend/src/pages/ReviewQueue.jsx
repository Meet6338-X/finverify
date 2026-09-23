import React, { useState, useEffect } from 'react';
import { getLedger, submitReview } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import DiscrepancyTrace from '../components/DiscrepancyTrace';
import { 
  Inbox, 
  CheckCircle, 
  XCircle, 
  FileEdit, 
  AlertTriangle, 
  X, 
  HelpCircle,
  ArrowRight,
  ShieldAlert,
  UserCheck,
  History,
  CheckCircle2,
  RefreshCw
} from 'lucide-react';

const ReviewQueue = () => {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('unreviewed'); // 'unreviewed' | 'adjudicated'
  
  const [selectedCert, setSelectedCert] = useState(null);
  const [decision, setDecision] = useState('accepted');
  const [reviewerId, setReviewerId] = useState('auditor_finverify_01');
  const [annotation, setAnnotation] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    fetchQueue();
  }, []);

  const fetchQueue = async () => {
    setLoading(true);
    try {
      // Fetch both unverifiable and warnings
      const resUnverifiable = await getLedger({ status: 'unverifiable', page_size: 50 });
      const resWarnings = await getLedger({ status: 'pass_with_warning', page_size: 50 });
      const resFails = await getLedger({ status: 'fail', page_size: 50 });
      
      const items1 = resUnverifiable.items || [];
      const items2 = resWarnings.items || [];
      const items3 = resFails.items || [];
      
      const combined = [...items1, ...items2, ...items3];
      const unique = Array.from(new Map(combined.map(item => [item.cert_id, item])).values());
      setQueue(unique);
    } catch (error) {
      console.error('Failed to fetch review queue', error);
      setQueue([]);
    } finally {
      setLoading(false);
    }
  };

  const unreviewedItems = queue.filter(item => !item.reviewer_decision);
  const adjudicatedItems = queue.filter(item => !!item.reviewer_decision);

  const displayedItems = activeTab === 'unreviewed' ? unreviewedItems : adjudicatedItems;

  const handleReviewClick = (cert) => {
    setSelectedCert(cert);
    setDecision('accepted');
    setAnnotation('');
  };

  const handleCloseModal = () => {
    setSelectedCert(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (decision === 'rejected' && !annotation.trim()) {
      alert('Mandatory Requirement: You must provide detailed annotation notes explaining why this claim is being rejected.');
      return;
    }
    
    setSubmitting(true);
    try {
      await submitReview(selectedCert.cert_id, {
        reviewer_id: reviewerId,
        decision,
        annotation: annotation.trim() || null,
      });

      const effectiveStatus = decision === 'accepted' ? 'pass' : (decision === 'rejected' ? 'fail' : selectedCert.original_status || 'annotated');

      setNotification({
        type: 'success',
        message: `Decision "${decision.toUpperCase()}" successfully committed! Certificate ${selectedCert.cert_id.substring(0, 8)}... status updated to "${effectiveStatus.toUpperCase()}".`
      });

      // Update local state immediately
      setQueue(prev => prev.map(c => {
        if (c.cert_id === selectedCert.cert_id) {
          return {
            ...c,
            status: effectiveStatus,
            reviewer_decision: {
              decision,
              reviewer_id: reviewerId,
              annotation: annotation.trim() || null,
              decided_at: new Date().toISOString()
            }
          };
        }
        return c;
      }));

      handleCloseModal();
    } catch (error) {
      console.error('Failed to submit review', error);
      setNotification({
        type: 'error',
        message: 'Failed to record decision on ledger. Please check backend connectivity.'
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Inbox className="w-6 h-6 text-blue-600" />
            Human-in-the-Loop Review Queue
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Audit and adjudicate claims classified as unverifiable or passing with warnings.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchQueue}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 shadow-sm transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          {/* Tab switcher */}
          <div className="flex items-center bg-slate-200/75 p-1 rounded-lg">
            <button
              onClick={() => setActiveTab('unreviewed')}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                activeTab === 'unreviewed' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Inbox className="w-3.5 h-3.5 text-blue-600" />
              <span>Pending Action ({unreviewedItems.length})</span>
            </button>
            <button
              onClick={() => setActiveTab('adjudicated')}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                activeTab === 'adjudicated' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <History className="w-3.5 h-3.5 text-emerald-600" />
              <span>Adjudicated History ({adjudicatedItems.length})</span>
            </button>
          </div>
        </div>
      </div>

      {/* Notification banner */}
      {notification && (
        <div className={`p-4 rounded-xl text-sm flex items-center justify-between shadow-sm ${
          notification.type === 'success' ? 'bg-emerald-50 text-emerald-900 border border-emerald-200' : 'bg-rose-50 text-rose-900 border border-rose-200'
        }`}>
          <div className="flex items-center gap-2">
            {notification.type === 'success' ? <CheckCircle className="w-5 h-5 text-emerald-600" /> : <AlertTriangle className="w-5 h-5 text-rose-600" />}
            <span>{notification.message}</span>
          </div>
          <button onClick={() => setNotification(null)} className="text-slate-400 hover:text-slate-600">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Queue Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-slate-500">
            <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
            <p className="text-sm">Loading review items...</p>
          </div>
        ) : displayedItems.length === 0 ? (
          <div className="py-16 text-center text-slate-500 space-y-3">
            <div className="w-12 h-12 bg-emerald-50 text-emerald-600 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <p className="text-base font-semibold text-slate-800">
              {activeTab === 'unreviewed' ? 'Review Queue is Clear' : 'No Adjudicated Claims Yet'}
            </p>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              {activeTab === 'unreviewed'
                ? 'All claims have been automatically verified or adjudicated by auditors.'
                : 'Adjudicate unverifiable or warning claims to record decisions in this ledger history.'}
            </p>
          </div>
        ) : (
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th scope="col" className="px-5 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Cert ID
                </th>
                <th scope="col" className="px-5 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Status
                </th>
                <th scope="col" className="px-5 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Claim Statement
                </th>
                {activeTab === 'adjudicated' ? (
                  <th scope="col" className="px-5 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    Auditor Decision & Notes
                  </th>
                ) : (
                  <th scope="col" className="px-5 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    Expected / Computed
                  </th>
                )}
                <th scope="col" className="px-5 py-3 text-right text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Action
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white">
              {displayedItems.map((item) => (
                <tr key={item.cert_id} className="hover:bg-slate-50/75 transition-colors">
                  <td className="px-5 py-4 whitespace-nowrap font-mono text-xs text-blue-600 font-semibold">
                    {item.cert_id ? item.cert_id.substring(0, 8) + '...' : '-'}
                  </td>
                  <td className="px-5 py-4 whitespace-nowrap">
                    <StatusBadge status={item.status} />
                  </td>
                  <td className="px-5 py-4 text-slate-900 font-medium max-w-xs sm:max-w-md truncate">
                    {item.claim_text || 'Financial numerical statement'}
                  </td>
                  {activeTab === 'adjudicated' ? (
                    <td className="px-5 py-4 text-xs text-slate-700">
                      <div className="flex items-center gap-1.5 font-semibold text-emerald-700">
                        <CheckCircle className="w-3.5 h-3.5" />
                        <span className="uppercase">{item.reviewer_decision?.decision}</span>
                        <span className="text-slate-400 font-normal">by {item.reviewer_decision?.reviewer_id}</span>
                      </div>
                      {item.reviewer_decision?.annotation && (
                        <p className="text-[11px] text-slate-500 italic mt-0.5 max-w-sm truncate">
                          "{item.reviewer_decision.annotation}"
                        </p>
                      )}
                    </td>
                  ) : (
                    <td className="px-5 py-4 whitespace-nowrap font-mono text-xs text-slate-700">
                      {item.expected_value !== null ? item.expected_value : 'N/A'} / {item.computed_value !== null ? item.computed_value : 'N/A'}
                    </td>
                  )}
                  <td className="px-5 py-4 whitespace-nowrap text-right">
                    <button
                      onClick={() => handleReviewClick(item)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition-colors"
                    >
                      <UserCheck className="w-3.5 h-3.5" />
                      <span>{activeTab === 'adjudicated' ? 'Re-adjudicate' : 'Review Claim'}</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Review Modal / Drawer */}
      {selectedCert && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-6 border border-slate-200 max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div className="space-y-1">
                <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <span>Adjudicate Certificate</span>
                  <StatusBadge status={selectedCert.status} />
                </h3>
                <p className="text-xs font-mono text-slate-400">ID: {selectedCert.cert_id}</p>
              </div>
              <button
                onClick={handleCloseModal}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Claim details */}
            <div className="space-y-3">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Claim Under Review
              </span>
              <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 text-sm text-slate-800 italic">
                "{selectedCert.claim_text || 'Claim statement'}"
              </div>
            </div>

            {/* Discrepancy trace */}
            <div className="space-y-2">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Computation Graph & Source References
              </span>
              <DiscrepancyTrace trace={selectedCert.discrepancy_trace} />
            </div>

            {/* Review Decision Form */}
            <form onSubmit={handleSubmit} className="space-y-4 pt-2 border-t border-slate-100">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Reviewer Decision (Overrides Verification Status)
                </label>
                <div className="grid grid-cols-3 gap-3">
                  <label className={`p-3 rounded-lg border flex flex-col items-center gap-1.5 cursor-pointer text-center text-xs font-semibold transition-all ${
                    decision === 'accepted' ? 'border-emerald-500 bg-emerald-50 text-emerald-900 ring-2 ring-emerald-500/20' : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                  }`}>
                    <input
                      type="radio"
                      name="decision"
                      value="accepted"
                      checked={decision === 'accepted'}
                      onChange={() => setDecision('accepted')}
                      className="sr-only"
                    />
                    <CheckCircle className="w-5 h-5 text-emerald-600" />
                    <span>Accept (Pass)</span>
                  </label>

                  <label className={`p-3 rounded-lg border flex flex-col items-center gap-1.5 cursor-pointer text-center text-xs font-semibold transition-all ${
                    decision === 'rejected' ? 'border-rose-500 bg-rose-50 text-rose-900 ring-2 ring-rose-500/20' : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                  }`}>
                    <input
                      type="radio"
                      name="decision"
                      value="rejected"
                      checked={decision === 'rejected'}
                      onChange={() => setDecision('rejected')}
                      className="sr-only"
                    />
                    <XCircle className="w-5 h-5 text-rose-600" />
                    <span>Reject (Fail)</span>
                  </label>

                  <label className={`p-3 rounded-lg border flex flex-col items-center gap-1.5 cursor-pointer text-center text-xs font-semibold transition-all ${
                    decision === 'annotated' ? 'border-blue-500 bg-blue-50 text-blue-900 ring-2 ring-blue-500/20' : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                  }`}>
                    <input
                      type="radio"
                      name="decision"
                      value="annotated"
                      checked={decision === 'annotated'}
                      onChange={() => setDecision('annotated')}
                      className="sr-only"
                    />
                    <FileEdit className="w-5 h-5 text-blue-600" />
                    <span>Annotate Note</span>
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Reviewer Identifier
                </label>
                <input
                  type="text"
                  value={reviewerId}
                  onChange={(e) => setReviewerId(e.target.value)}
                  className="w-full text-xs font-mono p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Adjudication Notes {decision === 'rejected' && <span className="text-rose-500 font-bold">* (Mandatory on rejection)</span>}
                </label>
                <textarea
                  rows={3}
                  value={annotation}
                  onChange={(e) => setAnnotation(e.target.value)}
                  placeholder="State the audit rationale for overriding or annotating this certificate..."
                  className="w-full text-sm p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  required={decision === 'rejected'}
                />
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="px-4 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition-colors disabled:opacity-50"
                >
                  {submitting ? 'Recording on Ledger...' : 'Commit Decision to Ledger'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReviewQueue;
