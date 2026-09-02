import React from 'react';
import { Users, Zap } from 'lucide-react';

interface PopulationPanelProps {
  population: number;
  generation: number;
}

export const PopulationPanel: React.FC<PopulationPanelProps> = ({
  population,
  generation,
}) => {
  return (
    <div className="grid grid-cols-2 gap-4 mb-6">
      {/* Population */}
      <div className="bg-gradient-to-br from-bio-accent/20 to-bio-accent-dark/20 border border-bio-accent/50 rounded-lg p-4 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-2">
          <span className="text-bio-accent font-semibold">Population</span>
          <Users size={20} className="text-bio-accent" />
        </div>
        <div className="text-3xl font-bold text-bio-accent">{population}</div>
        <div className="w-full bg-bio-accent/10 rounded-full h-2 mt-2">
          <div
            className="bg-gradient-to-r from-bio-accent to-bio-accent-dark h-2 rounded-full transition-all duration-300"
            style={{ width: `${Math.min((population / 1000) * 100, 100)}%` }}
          />
        </div>
      </div>

      {/* Generation */}
      <div className="bg-gradient-to-br from-bio-purple/20 to-blue-900/20 border border-bio-purple/50 rounded-lg p-4 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-2">
          <span className="text-bio-purple font-semibold">Generation</span>
          <Zap size={20} className="text-bio-purple" />
        </div>
        <div className="text-3xl font-bold text-bio-purple">{generation}</div>
        <div className="text-xs text-bio-purple/70 mt-2">Progress: Gen {generation} / ∞</div>
      </div>
    </div>
  );
};
