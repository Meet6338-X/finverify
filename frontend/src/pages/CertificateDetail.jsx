import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import nacl from 'tweetnacl';
import naclUtil from 'tweetnacl-util';
import { getCertificate, downloadCertificatePdf, getPublicKey } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import DiscrepancyTrace from '../components/DiscrepancyTrace';
import { 
  ArrowLeft, 
  Download, 
  Copy, 
  Check, 
  ShieldCheck, 
  Lock, 
  KeyRound, 
  ExternalLink, 
  QrCode,
  FileCheck,
  Calendar,
  AlertCircle,
  UserCheck,
  CheckCircle2,
  XCircle,
  Sparkles
} from 'lucide-react';

const CertificateDetail = () => {
  const { certId } = useParams();
  const navigate = useNavigate();
  const [cert, setCert] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [copiedSig, setCopiedSig] = useState(false);
  const [cryptoValid, setCryptoValid] = useState(null);
  const [serverPubKey, setServerPubKey] = useState('');

  const canonicalize = (obj) => {
    if (obj === null || typeof obj !== 'object') {
      return JSON.stringify(obj);
    }
    if (Array.isArray(obj)) {
      return '[' + obj.map(canonicalize).join(',') + ']';
    }
    const keys = Object.keys(obj).sort();
    let res = '{';
    for (let i = 0; i < keys.length; i++) {
      if (i > 0) res += ',';
      res += JSON.stringify(keys[i]) + ':' + canonicalize(obj[keys[i]]);
    }
    res += '}';
    return res;
  };

  const hexToUint8Array = (hexString) => {
    if (!hexString) return new Uint8Array();
    const cleanHex = hexString.replace(/^0x/, '').trim();
    const bytes = new Uint8Array(Math.ceil(cleanHex.length / 2));
    for (let i = 0; i < bytes.length; i++) {
      bytes[i] = parseInt(cleanHex.substr(i * 2, 2), 16);
    }
    return bytes;
  };

  useEffect(() => {
    const fetchCertAndVerify = async () => {
      setLoading(true);
      try {
        const [certData, pubKeyData] = await Promise.all([
          getCertificate(certId),
          getPublicKey().catch(() => ({ public_key: '' }))
        ]);
        
        setCert(certData);
        setServerPubKey(pubKeyData.public_key || '');

        // Verify cryptographic signature in browser
        if (certData && certData.signature && pubKeyData.public_key) {
          try {
            const payload = certData.cert_payload_json || {
              claim_id: certData.claim_id,
              status: certData.original_status || certData.status,
              expected_value: certData.expected_value,
              computed_value: certData.computed_value,
              relative_error: certData.relative_error,
              discrepancy_trace: certData.discrepancy_trace,
              source_refs: certData.source_refs,
              timestamp: certData.issued_at
            };

            const canonicalStr = canonicalize(payload);
            const msgBytes = naclUtil.decodeUTF8(canonicalStr);
            const sigBytes = hexToUint8Array(certData.signature);
            const pubBytes = hexToUint8Array(pubKeyData.public_key);

            if (sigBytes.length === 64 && pubBytes.length === 32) {
              const isValid = nacl.sign.detached.verify(msgBytes, sigBytes, pubBytes);
              setCryptoValid(isValid);
            } else {
              setCryptoValid(false);
            }
          } catch (e) {
            console.warn('In-page verification failed:', e);
            setCryptoValid(false);
          }
        }
      } catch (error) {
        console.error('Failed to fetch certificate', error);
      } finally {
        setLoading(false);
      }
    };
    fetchCertAndVerify();
  }, [certId]);

  const handleDownloadPdf = async () => {
    setDownloading(true);
    try {
      const blob = await downloadCertificatePdf(certId);
      const url = window.URL.createObjectURL(new Blob([blob], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `finverify_cert_${certId.substring(0, 8)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (error) {
      console.error('Failed to download PDF certificate', error);
      alert('Failed to download PDF. Please ensure backend services are active.');
    } finally {
      setDownloading(false);
    }
  };

  const handleCopyJson = () => {
    if (!cert) return;
    const payload = cert.cert_payload_json || cert;
    const jsonStr = JSON.stringify(payload, null, 2);
    navigator.clipboard.writeText(jsonStr);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCopySignature = () => {
    if (!cert || !cert.signature) return;
    navigator.clipboard.writeText(cert.signature);
    setCopiedSig(true);
    setTimeout(() => setCopiedSig(false), 2000);
  };

  const handleVerifyOffline = () => {
    if (!cert) return;
    const payload = cert.cert_payload_json || cert;
    navigate('/verify', {
      state: {
        certificateJson: JSON.stringify(payload, null, 2),
        signature: cert.signature || '',
        publicKey: serverPubKey || ''
      }
    });
  };

  if (loading) {
    return (
      <div className="py-20 text-center text-slate-500 space-y-2">
        <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
        <p className="text-sm">Retrieving cryptographic certificate from ledger...</p>
      </div>
    );
  }

  if (!cert) {
    return (
      <div className="bg-white p-12 rounded-xl border border-slate-200 text-center space-y-4 max-w-lg mx-auto shadow-sm">
        <AlertCircle className="w-12 h-12 text-rose-500 mx-auto" />
        <h2 className="text-lg font-bold text-slate-900">Certificate Not Found</h2>
        <p className="text-sm text-slate-500">
          The requested verification certificate could not be located on the append-only ledger.
        </p>
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 transition-colors shadow-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Ledger</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Navigation header */}
      <div className="flex items-center justify-between">
        <Link
          to="/"
          className="inline-flex items-center gap-1 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Ledger</span>
        </Link>

        <div className="flex items-center gap-2">
          <button
            onClick={handleCopyJson}
            className="inline-flex items-center gap-1 px-3 py-1.5 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 shadow-sm transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied JSON!' : 'Copy Payload JSON'}</span>
          </button>

          <button
            onClick={handleVerifyOffline}
            className="inline-flex items-center gap-1 px-3 py-1.5 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 shadow-sm transition-colors"
          >
            <KeyRound className="w-3.5 h-3.5 text-blue-600" />
            <span>Open in Standalone Verifier</span>
          </button>

          <button
            onClick={handleDownloadPdf}
            disabled={downloading}
            className="inline-flex items-center gap-1 px-3.5 py-1.5 rounded-lg text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition-colors disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            <span>{downloading ? 'Generating PDF...' : 'Download PDF'}</span>
          </button>
        </div>
      </div>

      {/* Main Certificate Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-md overflow-hidden">
        {/* Certificate banner */}
        <div className="bg-gradient-to-r from-slate-900 via-blue-950 to-indigo-950 p-6 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-6 h-6 text-emerald-400" />
              <h1 className="text-xl font-bold tracking-tight">
                Proof-Carrying Verification Certificate
              </h1>
            </div>
            <p className="text-xs text-slate-300 font-mono">
              Certificate ID: {cert.cert_id}
            </p>
          </div>
          <div className="flex items-center gap-3">
            {cryptoValid !== null && (
              <span className={`px-2.5 py-1 rounded-full text-xs font-bold flex items-center gap-1 border ${
                cryptoValid
                  ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                  : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
              }`}>
                {cryptoValid ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> : <AlertCircle className="w-3.5 h-3.5 text-amber-400" />}
                <span>{cryptoValid ? 'Signature Authentic' : 'Legacy Key Session'}</span>
              </span>
            )}
            <StatusBadge status={cert.status} size="lg" />
          </div>
        </div>

        {/* Reviewer Decision Notice if Adjudicated */}
        {cert.reviewer_decision && (
          <div className="bg-blue-50/80 border-b border-blue-200 px-6 py-3.5 flex items-center justify-between text-xs text-blue-950">
            <div className="flex items-center gap-2 font-medium">
              <UserCheck className="w-4 h-4 text-blue-600 flex-shrink-0" />
              <span>
                Adjudicated by <strong className="font-semibold">{cert.reviewer_decision.reviewer_id}</strong> with decision: <span className="uppercase font-bold text-blue-700">{cert.reviewer_decision.decision}</span>
              </span>
            </div>
            {cert.reviewer_decision.annotation && (
              <span className="italic text-slate-600 max-w-sm truncate">
                "{cert.reviewer_decision.annotation}"
              </span>
            )}
          </div>
        )}

        {/* Certificate Body */}
        <div className="p-6 space-y-6">
          {/* Claim statement */}
          <div className="space-y-1.5">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Audited Claim Statement
            </span>
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-900 italic">
              "{cert.claim_text || 'Financial numerical statement extracted from LLM commentary.'}"
            </div>
          </div>

          {/* Numerical Verification Comparison */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-xs font-medium text-slate-500 block mb-1">Expected (LLM Claimed)</span>
              <span className="text-2xl font-bold font-mono text-slate-900">
                {cert.expected_value !== null && cert.expected_value !== undefined
                  ? cert.expected_value.toLocaleString(undefined, { maximumFractionDigits: 6 })
                  : 'N/A'}
              </span>
            </div>

            <div className="p-4 rounded-xl bg-blue-50/50 border border-blue-100">
              <span className="text-xs font-medium text-blue-700 block mb-1">Computed (EDGAR Symbolic Ground Truth)</span>
              <span className="text-2xl font-bold font-mono text-blue-900">
                {cert.computed_value !== null && cert.computed_value !== undefined
                  ? cert.computed_value.toLocaleString(undefined, { maximumFractionDigits: 6 })
                  : 'N/A'}
              </span>
            </div>

            <div className={`p-4 rounded-xl border ${
              cert.relative_error === null || cert.relative_error === undefined
                ? 'bg-slate-50 border-slate-200'
                : cert.relative_error <= 0.002
                ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                : cert.relative_error <= 0.01
                ? 'bg-amber-50 border-amber-200 text-amber-900'
                : 'bg-rose-50 border-rose-200 text-rose-900'
            }`}>
              <span className="text-xs font-medium block mb-1">Relative Discrepancy</span>
              <span className="text-2xl font-bold font-mono">
                {cert.relative_error !== null && cert.relative_error !== undefined
                  ? `${(cert.relative_error * 100).toFixed(4)}%`
                  : 'N/A'}
              </span>
            </div>
          </div>

          {/* Discrepancy Trace */}
          <div className="space-y-2">
            <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Step-by-Step Re-Execution Graph
            </span>
            <DiscrepancyTrace trace={cert.discrepancy_trace} />
          </div>

          {/* Source References */}
          {cert.source_refs && cert.source_refs.length > 0 && (
            <div className="space-y-2">
              <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                SEC EDGAR Ground Truth References
              </span>
              <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5">
                {cert.source_refs.map((ref, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-xs font-mono text-blue-700">
                    <FileCheck className="w-3.5 h-3.5 text-blue-500 flex-shrink-0" />
                    <span className="break-all">{ref}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Cryptographic Signature & Ledger Metadata */}
          <div className="border-t border-slate-200 pt-5 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-slate-500" />
                Cryptographic Integrity Metadata
              </span>

              <button
                onClick={handleCopySignature}
                className="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-600 hover:text-blue-800"
              >
                {copiedSig ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                <span>{copiedSig ? 'Copied 128-Char Hex!' : 'Copy 128-Char Signature Hex'}</span>
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                <span className="text-slate-400 block text-[10px] uppercase font-sans font-semibold mb-0.5">
                  Algorithm & Standard
                </span>
                <span className="text-slate-800 font-medium">Ed25519 (RFC 8032) / Canonical JSON (RFC 8785)</span>
              </div>

              <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                <span className="text-slate-400 block text-[10px] uppercase font-sans font-semibold mb-0.5">
                  Issued UTC Timestamp
                </span>
                <span className="text-slate-800 font-medium">
                  {cert.issued_at ? new Date(cert.issued_at).toUTCString() : 'N/A'}
                </span>
              </div>

              <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-200 sm:col-span-2 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400 text-[10px] uppercase font-sans font-semibold">
                    Ed25519 Digital Signature Hex (128 characters / 64 bytes)
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">
                    Length: {cert.signature ? cert.signature.length : 0} chars
                  </span>
                </div>
                <div className="text-slate-800 font-mono text-xs break-all select-all p-2 bg-white rounded border border-slate-200">
                  {cert.signature || 'Unsigned'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CertificateDetail;
