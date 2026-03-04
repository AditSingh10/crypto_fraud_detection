import React from 'react';

const navItems = [
  { name: 'Live Monitor', active: true },
  { name: 'Alerts', active: false },
  { name: 'Entity Explorer', active: false },
  { name: 'Model Performance', active: false },
  { name: 'System Metrics', active: false },
];

export const Sidebar: React.FC = () => {
  return (
    <div className="w-64 bg-slate-900 text-slate-300 flex flex-col border-r border-slate-800 shrink-0">
      <div className="h-14 flex items-center px-4 font-semibold text-white border-b border-slate-800 tracking-tight">
        Risk Monitor
      </div>
      <nav className="flex-1 py-4">
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.name}>
              <a
                href="#"
                className={`block px-4 py-2 text-sm ${
                  item.active 
                    ? 'bg-slate-800 text-white font-medium' 
                    : 'hover:bg-slate-800 hover:text-white transition-colors'
                }`}
              >
                {item.name}
              </a>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
};
