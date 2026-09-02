import React from 'react';
import { Menu, Settings, RotateCw, Save } from 'lucide-react';

interface HeaderProps {
  generation: number;
  onReset: () => void;
}

export const Header: React.FC<HeaderProps> = ({ generation, onReset }) => {
  const [showMenu, setShowMenu] = React.useState(false);

  return (
    <header className="bg-gradient-to-r from-bio-dark to-bio-darker border-b border-bio-accent/30 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="text-4xl">🧬</div>
          <div>
            <h1 className="text-3xl font-bold text-bio-accent">Evolution</h1>
            <p className="text-xs text-bio-accent/70">Simulate Life & Progress</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-sm text-slate-400">Generation</div>
            <div className="text-2xl font-bold text-bio-accent">{generation}</div>
          </div>
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-2 hover:bg-bio-accent/10 rounded-lg transition-colors text-bio-accent"
          >
            <Menu size={24} />
          </button>
        </div>
      </div>

      {showMenu && (
        <div className="border-t border-bio-accent/20 bg-bio-darker/95 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-6 py-3 flex gap-3">
            <button className="flex items-center gap-2 px-4 py-2 bg-bio-accent/10 border border-bio-accent/50 rounded-lg hover:bg-bio-accent/20 transition-all text-bio-accent font-semibold">
              <Save size={18} />
              Save Game
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg hover:bg-slate-700/50 transition-all text-slate-300 font-semibold">
              <Settings size={18} />
              Settings
            </button>
            <button
              onClick={onReset}
              className="flex items-center gap-2 px-4 py-2 bg-bio-danger/10 border border-bio-danger/50 rounded-lg hover:bg-bio-danger/20 transition-all text-bio-danger font-semibold"
            >
              <RotateCw size={18} />
              New Game
            </button>
          </div>
        </div>
      )}
    </header>
  );
};
