import React from 'react';
import { Crown, AlertCircle } from 'lucide-react';

interface PrestigePanelProps {
  prestigeLevel: number;
  generation: number;
  onPrestige: () => void;
}

export const PrestigePanel: React.FC<PrestigePanelProps> = ({
  prestigeLevel,
  generation,
  onPrestige,
}) => {
  const prestigeGain = Math.floor(Math.sqrt(generation));
  const canPrestige = generation > 5;

  return (
    <div className="bg-gradient-to-br from-bio-purple/20 to-pink-900/20 border border-bio-purple/50 rounded-lg p-6 backdrop-blur-sm">
      <div className="flex items-center gap-2 mb-4">
        <Crown className="text-bio-purple" size={24} />
        <h3 className="text-xl font-bold text-bio-purple">Prestige</h3>
      </div>

      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-slate-300">Current Level:</span>
          <span className="text-2xl font-bold text-bio-purple">{prestigeLevel}</span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-slate-300">Gain on Reset:</span>
          <span className="text-lg font-semibold text-bio-accent">+{prestigeGain}</span>
        </div>

        <div className="bg-slate-900/50 border border-slate-700/50 rounded-lg p-3 mt-4">
          <div className="flex gap-2 text-xs text-slate-300">
            <AlertCircle size={16} className="flex-shrink-0 mt-0.5" />
            <span>
              Reset your progress to gain permanent bonuses for future runs. Unlocks at generation 5.
            </span>
          </div>
        </div>

        <button
          onClick={onPrestige}
          disabled={!canPrestige}
          className={`w-full py-3 rounded-lg font-bold transition-all mt-4 ${
            canPrestige
              ? 'bg-gradient-to-r from-bio-purple to-pink-600 text-white hover:shadow-lg hover:shadow-bio-purple/50 cursor-pointer'
              : 'bg-slate-700/50 text-slate-400 cursor-not-allowed'
          }`}
        >
          {canPrestige ? 'Prestige Now' : `Unlock at Gen 5 (${generation}/5)`}
        </button>
      </div>
    </div>
  );
};
