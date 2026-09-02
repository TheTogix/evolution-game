import React from 'react';
import { Beaker, Lock, CheckCircle } from 'lucide-react';
import { Technology } from '../types/game';

interface TechTreeProps {
  technologies: Technology[];
  onResearch: (techId: string) => void;
}

export const TechTree: React.FC<TechTreeProps> = ({
  technologies,
  onResearch,
}) => {
  return (
    <div className="bg-gradient-to-br from-bio-dark/80 to-bio-darker/80 border border-bio-accent/30 rounded-lg p-6 backdrop-blur-md">
      <div className="flex items-center gap-2 mb-4">
        <Beaker className="text-bio-accent" size={24} />
        <h2 className="text-2xl font-bold text-bio-accent">Technology Tree</h2>
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {technologies.map((tech) => (
          <div
            key={tech.id}
            className={`p-4 rounded-lg border transition-all ${
              tech.unlocked
                ? 'bg-bio-accent/10 border-bio-accent/50 hover:border-bio-accent'
                : 'bg-slate-900/30 border-slate-700/50 hover:border-slate-600'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-lg text-white">{tech.name}</h3>
                  {tech.unlocked ? (
                    <CheckCircle size={18} className="text-bio-accent" />
                  ) : (
                    <Lock size={18} className="text-slate-500" />
                  )}
                </div>
                <p className="text-sm text-slate-300 mt-1">{tech.description}</p>
                {tech.unlocked && (
                  <div className="text-xs text-bio-accent mt-2">Level: {tech.level}</div>
                )}
              </div>
              {!tech.unlocked && (
                <button
                  onClick={() => onResearch(tech.id)}
                  className="ml-4 px-4 py-2 bg-gradient-to-r from-bio-accent to-bio-accent-dark text-bio-dark font-semibold rounded-lg hover:shadow-lg hover:shadow-bio-accent/50 transition-all whitespace-nowrap"
                >
                  Research
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
