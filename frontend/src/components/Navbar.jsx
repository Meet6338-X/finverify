import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import { 
  ShieldCheck, 
  LayoutDashboard, 
  Inbox, 
  PlusCircle, 
  KeyRound, 
  BarChart3,
  Cpu
} from 'lucide-react';

const Navbar = () => {
  const navItemClass = ({ isActive }) =>
    `inline-flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
      isActive
        ? 'bg-blue-50 text-blue-700 shadow-sm border border-blue-100 font-semibold'
        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
    }`;

  return (
    <header className="bg-white border-b border-slate-200 shadow-sm sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          
          {/* Brand Logo */}
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-2 group">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md group-hover:scale-105 transition-transform">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <span className="text-xl font-bold bg-gradient-to-r from-slate-900 via-blue-950 to-blue-700 bg-clip-text text-transparent">
                  FinVerify
                </span>
                <span className="hidden sm:inline-block ml-1.5 px-1.5 py-0.2 text-[10px] uppercase font-bold tracking-wider bg-blue-100 text-blue-700 rounded">
                  v1.0
                </span>
              </div>
            </Link>

            {/* Navigation links */}
            <nav className="hidden md:flex items-center space-x-1">
              <NavLink to="/" className={navItemClass}>
                <LayoutDashboard className="w-4 h-4" />
                <span>Dashboard</span>
              </NavLink>
              <NavLink to="/review" className={navItemClass}>
                <Inbox className="w-4 h-4" />
                <span>Review Queue</span>
              </NavLink>
              <NavLink to="/submit" className={navItemClass}>
                <PlusCircle className="w-4 h-4" />
                <span>New Audit</span>
              </NavLink>
              <NavLink to="/verify" className={navItemClass}>
                <KeyRound className="w-4 h-4" />
                <span>Offline Verifier</span>
              </NavLink>
              <NavLink to="/benchmark" className={navItemClass}>
                <Cpu className="w-4 h-4 text-indigo-600" />
                <span className="flex items-center gap-1">
                  <span>Benchmark Studio</span>
                  <span className="px-1 py-0.2 text-[9px] font-extrabold bg-indigo-100 text-indigo-700 rounded uppercase tracking-wider">
                    USP
                  </span>
                </span>
              </NavLink>
            </nav>
          </div>

          {/* Right actions */}
          <div className="flex items-center gap-3">
            <Link
              to="/submit"
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition-colors"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Verify Filing</span>
            </Link>
          </div>

        </div>
      </div>
    </header>
  );
};

export default Navbar;
