import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import nacl from 'tweetnacl';
import naclUtil from 'tweetnacl-util';
import { getPublicKey } from '../api/client';
import { 
  KeyRound, 
  CheckCircle2, 
  XCircle, 
  ShieldCheck, 
  Sparkles, 
  Lock, 
  FileCode,
  AlertTriangle,
  RefreshCw,
  Copy,
  Check
} from 'lucide-react';

const SAMPLE_PAYLOAD = {
  claim_id: "c_9f21a300-4b12-4211-9a71-6e3a79d01244",
  status: "pass",
  expected_value: 0.423236,
  computed_value: 0.4232365,
  relative_error: 0.000001,
  discrepancy_trace: [
    {
      step_name: "gross_margin",
      formula: "(rev - cogs) / rev",
      computed_value: 0.4232365,
      source_reference: "us-gaap:Revenues"
    }
  ],
  source_refs: [
    "edgar://CIK0000320193/10-K/2025-Q4#us-gaap:Revenues"
  ],
  timestamp: "2026-08-19T10:14:02Z"
};

const TamperVerifier = () => {
  const location = useLocation();
  const [certJson, setCertJson] = useState('');
  const [signatureHex, setSignatureHex] = useState('');
  const [publicKeyHex, setPublicKeyHex] = useState('');
  const [verificationResult, setVerificationResult] = useState(null);
  const [canonicalOutput, setCanonicalOutput] = useState('');
  const [errorDetails, setErrorDetails] = useState(null);
  const [loadingKey, setLoadingKey] = useState(false);

  // Auto-fetch system public key on load
  useEffect(() => {
    fetchSystemKey();
  }, []);

  // Prepopulate if navigated from CertificateDetail
  useEffect(() => {
    if (location.state) {
      if (location.state.certificateJson) setCertJson(location.state.certificateJson);
      if (location.state.signature) setSignatureHex(location.state.signature);
      if (location.state.publicKey) setPublicKeyHex(location.state.publicKey);
    }
  }, [location.state]);

  const fetchSystemKey = async () => {
    setLoadingKey(true);
    try {
      const res = await getPublicKey();
      if (res && res.public_key) {
        setPublicKeyHex(res.public_key);
      }
    } catch (err) {
      console.warn('Could not auto-fetch server public key:', err);
    } finally {
      setLoadingKey(false);
    }
  };

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

  const uint8ArrayToHex = (arr) => {
    return Array.from(arr).map(b => b.toString(16).padStart(2, '0')).join('');
  };

  // Generate a live demo keypair & signed sample
  const handleLoadValidSample = () => {
    const keyPair = nacl.sign.keyPair();
    const pubHex = uint8ArrayToHex(keyPair.publicKey);
    
    const canonicalStr = canonicalize(SAMPLE_PAYLOAD);
    const msgBytes = naclUtil.decodeUTF8(canonicalStr);
    const sigBytes = nacl.sign.detached(msgBytes, keyPair.secretKey);
    const sigHex = uint8ArrayToHex(sigBytes);

    setCertJson(JSON.stringify(SAMPLE_PAYLOAD, null, 2));
    setSignatureHex(sigHex);
    setPublicKeyHex(pubHex);
    setVerificationResult(null);
    setErrorDetails(null);
  };

  const handleLoadTamperedSample = () => {
    const keyPair = nacl.sign.keyPair();
    const pubHex = uint8ArrayToHex(keyPair.publicKey);
    
    // Sign original
    const canonicalStr = canonicalize(SAMPLE_PAYLOAD);
    const msgBytes = naclUtil.decodeUTF8(canonicalStr);
    const sigBytes = nacl.sign.detached(msgBytes, keyPair.secretKey);
    const sigHex = uint8ArrayToHex(sigBytes);

    // Tamper with value (e.g. change 0.423236 to 0.999999)
    const tampered = { ...SAMPLE_PAYLOAD, expected_value: 0.999999 };

    setCertJson(JSON.stringify(tampered, null, 2));
    setSignatureHex(sigHex);
    setPublicKeyHex(pubHex);
    setVerificationResult(null);
    setErrorDetails(null);
  };

  const handleVerify = () => {
    setErrorDetails(null);
    setVerificationResult(null);
    try {
      if (!certJson.trim()) {
        setErrorDetails('Please enter certificate JSON payload.');
        return;
      }
      if (!signatureHex.trim()) {
        setErrorDetails('Please provide Ed25519 signature hex string.');
        return;
      }
      if (!publicKeyHex.trim()) {
        setErrorDetails('Please provide Ed25519 public verification key hex string.');
        return;
      }

      let parsedObj;
      try {
        parsedObj = JSON.parse(certJson);
      } catch (err) {
        setErrorDetails(`Invalid JSON Syntax: ${err.message}`);
        return;
      }

      // If object has cert_payload_json inside it, use that
      const payloadToVerify = parsedObj.cert_payload_json || parsedObj;
      
      // Remove signature and other top-level wrapper fields if present
      const cleanPayload = { ...payloadToVerify };
      delete cleanPayload.signature;
      delete cleanPayload.cert_id;
      delete cleanPayload.issued_at;
      delete cleanPayload.qr_code_url;
      delete cleanPayload.claim_text;
      delete cleanPayload.original_status;
      delete cleanPayload.reviewer_decision;

      const canonicalString = canonicalize(cleanPayload);
      setCanonicalOutput(canonicalString);

      const messageUint8 = naclUtil.decodeUTF8(canonicalString);
      const sigUint8 = hexToUint8Array(signatureHex);
      const pubKeyUint8 = hexToUint8Array(publicKeyHex);

      if (sigUint8.length !== 64) {
        setErrorDetails(`Invalid signature byte length: expected 64 bytes (128 hex chars), got ${sigUint8.length} bytes.`);
        setVerificationResult(false);
        return;
      }

      if (pubKeyUint8.length !== 32) {
        setErrorDetails(`Invalid public key byte length: expected 32 bytes (64 hex chars), got ${pubKeyUint8.length} bytes.`);
        setVerificationResult(false);
        return;
      }

      const isValid = nacl.sign.detached.verify(messageUint8, sigUint8, pubKeyUint8);
      setVerificationResult(isValid);
    } catch (error) {
      console.error('Verification error:', error);
      setErrorDetails(`Cryptographic Verification Error: ${error.message}`);
      setVerificationResult(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <KeyRound className="w-6 h-6 text-blue-600" />
          Offline Standalone Tamper Verifier
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Zero-backend verification. Validate Ed25519 digital signatures and canonical JSON representation directly in your browser.
        </p>
      </div>

      {/* Demo Presets Bar */}
      <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
          <Sparkles className="w-4 h-4 text-blue-600" />
          <span>Interactive Cryptographic Verification Presets:</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleLoadValidSample}
            className="px-3 py-1.5 bg-white border border-slate-300 hover:border-emerald-500 text-xs font-semibold text-slate-700 hover:text-emerald-700 rounded-lg shadow-2xs transition-colors"
          >
            Load Valid Sample
          </button>
          <button
            type="button"
            onClick={handleLoadTamperedSample}
            className="px-3 py-1.5 bg-white border border-slate-300 hover:border-rose-500 text-xs font-semibold text-slate-700 hover:text-rose-700 rounded-lg shadow-2xs transition-colors"
          >
            Load Tampered Sample
          </button>
        </div>
      </div>

      {/* Form */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-5">
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Certificate JSON Payload
          </label>
          <textarea
            rows={8}
            value={certJson}
            onChange={(e) => setCertJson(e.target.value)}
            placeholder="Paste canonical certificate JSON or payload..."
            className="w-full text-xs font-mono p-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Ed25519 Digital Signature (Hex - 128 chars)
            </label>
            <input
              type="text"
              value={signatureHex}
              onChange={(e) => setSignatureHex(e.target.value)}
              placeholder="e.g. 2b7f701702af..."
              className="w-full text-xs font-mono p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Ed25519 Public Key (Hex - 64 chars)
              </label>
              <button
                type="button"
                onClick={fetchSystemKey}
                className="text-[11px] text-blue-600 hover:underline flex items-center gap-1 font-semibold"
              >
                <RefreshCw className={`w-3 h-3 ${loadingKey ? 'animate-spin' : ''}`} />
                <span>Fetch Server Key</span>
              </button>
            </div>
            <input
              type="text"
              value={publicKeyHex}
              onChange={(e) => setPublicKeyHex(e.target.value)}
              placeholder="e.g. e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
              className="w-full text-xs font-mono p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
        </div>

        {errorDetails && (
          <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span>{errorDetails}</span>
          </div>
        )}

        <div className="pt-2 flex justify-end">
          <button
            type="button"
            onClick={handleVerify}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 shadow-md transition-colors"
          >
            <ShieldCheck className="w-4 h-4" />
            <span>Verify Signature Offline</span>
          </button>
        </div>

        {/* Verification Result Card */}
        {verificationResult !== null && (
          <div className={`p-6 rounded-2xl border transition-all ${
            verificationResult
              ? 'bg-emerald-50/80 border-emerald-300 text-emerald-950'
              : 'bg-rose-50/80 border-rose-300 text-rose-950'
          }`}>
            <div className="flex items-center gap-3">
              {verificationResult ? (
                <CheckCircle2 className="w-8 h-8 text-emerald-600 flex-shrink-0" />
              ) : (
                <XCircle className="w-8 h-8 text-rose-600 flex-shrink-0" />
              )}
              <div>
                <h3 className="text-base font-bold">
                  {verificationResult
                    ? 'Cryptographically Valid: Authentic & Untampered'
                    : 'Tamper Detected: Signature Invalid / Payload Modified'}
                </h3>
                <p className="text-xs opacity-80 mt-0.5">
                  {verificationResult
                    ? 'The Ed25519 signature is authentic and mathematically corresponds to this canonical JSON payload and public key.'
                    : 'The signature does not match this payload. Even a single character or whitespace modification invalidates the cryptographic proof.'}
                </p>
              </div>
            </div>

            {canonicalOutput && (
              <div className="mt-4 pt-4 border-t border-slate-200/50 space-y-1">
                <span className="text-[11px] font-semibold uppercase tracking-wider block opacity-75">
                  Canonicalized Byte Sequence (RFC 8785):
                </span>
                <pre className="p-2.5 bg-black/10 rounded-lg text-[11px] font-mono break-all whitespace-pre-wrap select-all">
                  {canonicalOutput}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default TamperVerifier;
