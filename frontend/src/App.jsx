import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Dashboard from './pages/Dashboard';
import ReportDetail from './pages/ReportDetail';
import ReviewQueue from './pages/ReviewQueue';
import CertificateDetail from './pages/CertificateDetail';
import SubmitVerification from './pages/SubmitVerification';
import TamperVerifier from './pages/TamperVerifier';
import BenchmarkStudio from './pages/BenchmarkStudio';

function App() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans antialiased text-slate-900 selection:bg-blue-500 selection:text-white">
      <Navbar />

      <main className="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/reports/:reportId" element={<ReportDetail />} />
          <Route path="/review" element={<ReviewQueue />} />
          <Route path="/certificates/:certId" element={<CertificateDetail />} />
          <Route path="/submit" element={<SubmitVerification />} />
          <Route path="/verify" element={<TamperVerifier />} />
          <Route path="/benchmark" element={<BenchmarkStudio />} />
        </Routes>
      </main>

      <Footer />
    </div>
  );
}

export default App;
