import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { submitVerification, getJobStatus } from '../api/client';
import { 
  Send, 
  FileText, 
  Sparkles, 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  Layers, 
  ShieldCheck, 
  Database,
  ArrowRight,
  HelpCircle,
  TrendingUp,
  AlertTriangle
} from 'lucide-react';

const PRESETS = [
  {
    tag: 'PASS',
    tagColor: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    title: 'Apple Inc. (AAPL 10-K)',
    subtitle: 'Gross Margin (Exact Mathematical Pass)',
    data: {
      content_format: 'text',
      content: 'In fiscal 2025, Apple reported gross margin of 42.32% based on total net revenues of $4.82B and cost of goods sold of $2.78B.',
      filing_cik: '0000320193',
      filing_period: '2025-Q4',
      form_type: '10-K',
      llm_model: 'gpt-4o'
    }
  },
  {
    tag: 'FAIL',
    tagColor: 'bg-rose-100 text-rose-800 border-rose-200',
    title: 'Tesla Inc. (TSLA 10-K)',
    subtitle: 'Operating Margin (Synthetic Arithmetic Hallucination)',
    data: {
      content_format: 'text',
      content: 'Operating margin expanded significantly to 21.0% in 2024 based on total revenues of $96.77B, cost of revenues of $79.11B, and operating expenses of $8.77B.',
      filing_cik: '0001318605',
      filing_period: '2024-Q4',
      form_type: '10-K',
      llm_model: 'llama-3.3-70b-rag'
    }
  },
  {
    tag: 'PASS',
    tagColor: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    title: 'Microsoft Corp. (MSFT 10-Q)',
    subtitle: 'Diluted EPS Verification',
    data: {
      content_format: 'text',
      content: 'Microsoft reported diluted EPS of $3.23 for the quarter with net income reaching $24.10B against 7.46B diluted shares outstanding.',
      filing_cik: '0000789019',
      filing_period: '2025-Q2',
      form_type: '10-Q',
      llm_model: 'claude-3.7-sonnet'
    }
  },
  {
    tag: 'PASS',
    tagColor: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    title: 'Alphabet Inc. (GOOGL 10-K)',
    subtitle: 'Net Profit Margin Verification',
    data: {
      content_format: 'text',
      content: 'Alphabet delivered net margin of 27.70% with net income of $88.2B on total revenues of $318.4B.',
      filing_cik: '0001652044',
      filing_period: '2024-Q4',
      form_type: '10-K',
      llm_model: 'gemini-1.5-pro'
    }
  },
  {
    tag: 'PASS',
    tagColor: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    title: 'Nvidia Corp. (NVDA 10-K)',
    subtitle: 'Year-over-Year (YoY) Revenue Growth',
    data: {
      content_format: 'text',
      content: 'Nvidia revenue grew by 122.0% reaching $60.9B up from $27.43B reported in the prior year.',
      filing_cik: '0001045810',
      filing_period: '2025-Q4',
      form_type: '10-K',
      llm_model: 'deepseek-r1'
    }
  },
  {
    tag: 'UNVERIFIABLE',
    tagColor: 'bg-slate-100 text-slate-800 border-slate-300',
    title: 'Review Queue Demo (Target)',
    subtitle: 'Missing Footnote Claim (Requires Human Review)',
    data: {
      content_format: 'text',
      content: 'Adjusted EBITDA reached $14.5B with estimated synthetic synergies of $2.3B across undisclosed business lines.',
      filing_cik: '0000320193',
      filing_period: '2025-Q4',
      form_type: '10-K',
      llm_model: 'mistral-large'
    }
  }
];

const SubmitVerification = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    content: '',
    content_format: 'text',
    filing_cik: '',
    filing_period: '',
    form_type: '10-K',
    llm_model: ''
  });
  
  const [jobId, setJobId] = useState(null);
  const [reportId, setReportId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleLoadPreset = (presetData) => {
    setFormData(presetData);
    setJobId(null);
    setJobStatus(null);
    setErrorMessage(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.content.trim()) {
      alert('Please provide financial text content to verify.');
      return;
    }

    setLoading(true);
    setErrorMessage(null);
    setJobId(null);
    setJobStatus('submitting');

    try {
      const res = await submitVerification(formData);
      setJobId(res.job_id);
      setReportId(res.report_id);
      setJobStatus('running');
      pollStatus(res.job_id, res.report_id);
    } catch (error) {
      console.error('Submission failed', error);
      setErrorMessage('Failed to initiate verification workflow. Please ensure FastAPI and Temporal worker are online.');
      setLoading(false);
      setJobStatus(null);
    }
  };

  const pollStatus = (id, repId) => {
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts++;
      try {
        const res = await getJobStatus(id);
        const st = (res.status || '').toLowerCase();
        setJobStatus(st);

        if (st === 'completed' || st === 'running_completed' || st === 'terminated') {
          clearInterval(interval);
          setLoading(false);
        } else if (st === 'failed' || st === 'timed_out' || attempts > 60) {
          clearInterval(interval);
          setLoading(false);
          if (st === 'failed') setErrorMessage('Workflow activity execution failed.');
        }
      } catch (err) {
        if (attempts > 30) {
          clearInterval(interval);
          setLoading(false);
        }
      }
    }, 1500);
  };

  const charCount = (formData.content || '').length;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
          Submit Financial Content for Audit
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Extract numerical claims, link SEC EDGAR XBRL ground truth, and re-execute symbolically.
        </p>
      </div>

      {/* Demo Presets Bar */}
      <div className="space-y-2">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-blue-600" />
          Click-to-Load Financial Presets (All Scenarios)
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          {PRESETS.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleLoadPreset(preset.data)}
              className="p-3 bg-white hover:bg-blue-50/50 rounded-xl border border-slate-200 hover:border-blue-300 text-left transition-all shadow-2xs group relative"
            >
              <div className="flex items-center justify-between gap-1 mb-1">
                <span className="font-semibold text-xs text-slate-900 group-hover:text-blue-600">
                  {preset.title}
                </span>
                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border uppercase tracking-wider ${preset.tagColor}`}>
                  {preset.tag}
                </span>
              </div>
              <div className="text-[11px] text-slate-500">
                {preset.subtitle}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Submission Form */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-6">
        <form onSubmit={handleSubmit} className="space-y-5">
          
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Content Ingestion Format
              </label>
              <select
                name="content_format"
                value={formData.content_format}
                onChange={handleChange}
                className="w-full text-sm p-2.5 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              >
                <option value="text">Plain Text / Markdown</option>
                <option value="json">Structured JSON</option>
                <option value="csv">Financial CSV Export</option>
                <option value="pdf">Analyst PDF Note</option>
                <option value="docx">Word Report (.docx)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                SEC Filing CIK
              </label>
              <input
                type="text"
                name="filing_cik"
                required
                placeholder="e.g. 0000320193"
                value={formData.filing_cik}
                onChange={handleChange}
                className="w-full text-sm font-mono p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Filing Period & Form
              </label>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="text"
                  name="filing_period"
                  required
                  placeholder="2025-Q4"
                  value={formData.filing_period}
                  onChange={handleChange}
                  className="w-full text-sm font-mono p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
                <select
                  name="form_type"
                  value={formData.form_type}
                  onChange={handleChange}
                  className="w-full text-sm p-2.5 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                >
                  <option value="10-K">10-K (Annual)</option>
                  <option value="10-Q">10-Q (Quarterly)</option>
                  <option value="8-K">8-K (Current)</option>
                </select>
              </div>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-medium text-slate-700">
                LLM Commentary Text / Numerical Claims
              </label>
              <span className={`text-xs ${charCount > 100000 ? 'text-rose-600 font-bold' : 'text-slate-400'}`}>
                {charCount.toLocaleString()} / 100,000 chars
              </span>
            </div>
            <textarea
              name="content"
              rows={7}
              required
              value={formData.content}
              onChange={handleChange}
              placeholder="Paste AI-generated financial analysis commentary containing numerical derivations, ratios, growth rates, or sums..."
              className="w-full text-sm font-mono p-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Audited LLM Model Family (Optional)
            </label>
            <input
              type="text"
              name="llm_model"
              placeholder="e.g. gpt-4o, claude-3.7-sonnet, deepseek-r1"
              value={formData.llm_model}
              onChange={handleChange}
              className="w-full text-sm p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>

          {errorMessage && (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-900 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-xs text-slate-500">
              Deterministic SymPy/NumPy re-execution • Ed25519 tamper-proof signing
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 shadow-md transition-colors disabled:opacity-50"
            >
              <Send className={`w-4 h-4 ${loading ? 'animate-bounce' : ''}`} />
              <span>{loading ? 'Executing Temporal Pipeline...' : 'Start Verification Workflow'}</span>
            </button>
          </div>
        </form>

        {/* Live Workflow Status Tracker */}
        {(jobId || loading) && (
          <div className="mt-6 p-5 bg-slate-50 rounded-xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Temporal Distributed Pipeline
                </span>
                <p className="text-xs font-mono text-slate-500">Job: {jobId || 'Initializing...'}</p>
              </div>

              <div className="flex items-center gap-2">
                <span className={`px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wider ${
                  jobStatus === 'completed'
                    ? 'bg-emerald-100 text-emerald-800'
                    : jobStatus === 'failed'
                    ? 'bg-rose-100 text-rose-800'
                    : 'bg-blue-100 text-blue-800 animate-pulse'
                }`}>
                  {jobStatus || 'Pending'}
                </span>
              </div>
            </div>

            {/* Pipeline Stage Indicators */}
            <div className="grid grid-cols-4 gap-2 text-center text-xs">
              <div className="p-2 rounded bg-white border border-slate-200">
                <span className="font-semibold block text-slate-700">1. Ingestion</span>
                <span className="text-[10px] text-slate-400">Norm & Regex</span>
              </div>
              <div className="p-2 rounded bg-white border border-slate-200">
                <span className="font-semibold block text-slate-700">2. SEC EDGAR</span>
                <span className="text-[10px] text-slate-400">XBRL Linking</span>
              </div>
              <div className="p-2 rounded bg-white border border-slate-200">
                <span className="font-semibold block text-slate-700">3. Re-executor</span>
                <span className="text-[10px] text-slate-400">SymPy Exact</span>
              </div>
              <div className="p-2 rounded bg-white border border-slate-200">
                <span className="font-semibold block text-slate-700">4. Ed25519</span>
                <span className="text-[10px] text-slate-400">Ledger Signing</span>
              </div>
            </div>

            {/* Navigate button when complete */}
            {(jobStatus === 'completed' || reportId) && (
              <div className="pt-2 flex justify-end">
                <button
                  type="button"
                  onClick={() => navigate(`/reports/${reportId}`)}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 shadow-sm transition-colors"
                >
                  <span>View Verified Report</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default SubmitVerification;
