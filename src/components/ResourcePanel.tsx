import React from 'react';
import { Droplet, Zap, Dna } from 'lucide-react';

interface ResourcePanelProps {
  food: number;
  energy: number;
  dna: number;
}

export const ResourcePanel: React.FC<ResourcePanelProps> = ({
  food,
  energy,
  dna,
}) => {
  const formatNumber = (num: number) => {
    if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
    return Math.floor(num).toString();
  };

  return (
    <div className="grid grid-cols-3 gap-4 mb-6">
      {/* Food */}
      <div className="bg-gradient-to-br from-green-900/40 to-green-950/40 border border-green-500/50 rounded-lg p-4 backdrop-blur-sm hover:border-green-400/80 transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-green-400 font-semibold">Food</span>
          <Droplet size={20} className="text-green-400" />
        </div>
        <div className="text-3xl font-bold text-green-300">{formatNumber(food)}</div>
        <div className="text-xs text-green-400/70 mt-1">+{Math.floor(food / 50)}/s</div>
      </div>

      {/* Energy */}
      <div className="bg-gradient-to-br from-yellow-900/40 to-yellow-950/40 border border-yellow-500/50 rounded-lg p-4 backdrop-blur-sm hover:border-yellow-400/80 transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-yellow-400 font-semibold">Energy</span>
          <Zap size={20} className="text-yellow-400" />
        </div>
        <div className="text-3xl font-bold text-yellow-300">{formatNumber(energy)}</div>
        <div className="text-xs text-yellow-400/70 mt-1">+{Math.floor(energy / 25)}/s</div>
      </div>

      {/* DNA */}
      <div className="bg-gradient-to-br from-purple-900/40 to-purple-950/40 border border-purple-500/50 rounded-lg p-4 backdrop-blur-sm hover:border-purple-400/80 transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-purple-400 font-semibold">DNA</span>
          <Dna size={20} className="text-purple-400" />
        </div>
        <div className="text-3xl font-bold text-purple-300">{formatNumber(dna)}</div>
        <div className="text-xs text-purple-400/70 mt-1">Evolution resource</div>
      </div>
    </div>
  );
};
