import React from 'react';
import { 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  HelpCircle, 
  Clock, 
  CheckCheck 
} from 'lucide-react';

const StatusBadge = ({ status, size = 'sm', showIcon = true }) => {
  const s = (status || 'pending').toLowerCase();
  
  let config = {
    bg: 'bg-blue-50 text-blue-700 border-blue-200',
    icon: Clock,
    label: status || 'Pending',
    dotColor: 'bg-blue-500',
  };

  switch (s) {
    case 'pass':
    case 'passed':
      config = {
        bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        icon: CheckCircle2,
        label: 'Pass',
        dotColor: 'bg-emerald-500',
      };
      break;
    case 'pass_with_warning':
    case 'warning':
      config = {
        bg: 'bg-amber-50 text-amber-700 border-amber-200',
        icon: AlertTriangle,
        label: 'Warning (≤1%)',
        dotColor: 'bg-amber-500',
      };
      break;
    case 'fail':
    case 'failed':
      config = {
        bg: 'bg-rose-50 text-rose-700 border-rose-200',
        icon: XCircle,
        label: 'Failed (>1%)',
        dotColor: 'bg-rose-500',
      };
      break;
    case 'unverifiable':
      config = {
        bg: 'bg-slate-100 text-slate-700 border-slate-300',
        icon: HelpCircle,
        label: 'Unverifiable',
        dotColor: 'bg-slate-400',
      };
      break;
    case 'partial':
      config = {
        bg: 'bg-purple-50 text-purple-700 border-purple-200',
        icon: CheckCheck,
        label: 'Partial Pass',
        dotColor: 'bg-purple-500',
      };
      break;
    default:
      config = {
        bg: 'bg-blue-50 text-blue-700 border-blue-200',
        icon: Clock,
        label: status || 'Pending',
        dotColor: 'bg-blue-500',
      };
  }

  const IconComponent = config.icon;
  const sizeClasses = size === 'lg' 
    ? 'px-3 py-1 text-sm gap-1.5' 
    : 'px-2.5 py-0.5 text-xs gap-1';

  return (
    <span className={`inline-flex items-center font-medium rounded-full border shadow-sm ${config.bg} ${sizeClasses}`}>
      {showIcon && <IconComponent className={size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} />}
      <span>{config.label}</span>
    </span>
  );
};

export default StatusBadge;
