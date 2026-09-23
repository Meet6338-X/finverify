import React from 'react';
import { Shield, Lock, FileCheck } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="bg-white border-t border-slate-200 mt-auto py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-xs text-slate-500 flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-blue-600" />
          <span className="font-semibold text-slate-700">FinVerify Audit Engine</span>
          <span>— Proof-Carrying Numerical Verification for Financial LLMs</span>
        </div>
        <div className="flex items-center gap-4 text-slate-500">
          <span className="flex items-center gap-1">
            <Lock className="w-3.5 h-3.5 text-slate-400" /> Ed25519 Signed Certificates
          </span>
          <span>•</span>
          <span className="flex items-center gap-1">
            <FileCheck className="w-3.5 h-3.5 text-slate-400" /> SEC EDGAR XBRL Ground Truth
          </span>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
