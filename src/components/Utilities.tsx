import React from 'react';
import { AlertCircle, Volume2, VolumeX } from 'lucide-react';

interface NotificationProps {
  message: string;
  onClose: () => void;
}

export const Notification: React.FC<NotificationProps> = ({ message, onClose }) => {
  React.useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className="fixed top-4 right-4 bg-gradient-to-r from-bio-accent to-bio-accent-dark border border-bio-accent/80 rounded-lg p-4 shadow-lg shadow-bio-accent/50 animate-slide-in text-bio-dark font-semibold flex items-center gap-2 z-50">
      <AlertCircle size={20} />
      {message}
    </div>
  );
};

interface EvolutionButtonProps {
  dna: number;
  onClick: () => void;
}

export const EvolutionButton: React.FC<EvolutionButtonProps> = ({ dna, onClick }) => {
  const canEvolve = dna >= 50;

  return (
    <button
      onClick={onClick}
      disabled={!canEvolve}
      className={`w-full py-4 rounded-lg font-bold text-lg transition-all mb-4 ${
        canEvolve
          ? 'bg-gradient-to-r from-bio-accent to-bio-accent-dark text-bio-dark hover:shadow-lg hover:shadow-bio-accent/50 cursor-pointer'
          : 'bg-slate-700/50 text-slate-400 cursor-not-allowed'
      }`}
    >
      🧬 Evolve Species {canEvolve ? '✓' : `(${dna}/50 DNA)`}
    </button>
  );
};

interface StatsProps {
  playtime: number;
  prestige: number;
}

export const GameStats: React.FC<StatsProps> = ({ playtime, prestige }) => {
  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  return (
    <div className="bg-gradient-to-br from-slate-900/50 to-slate-950/50 border border-slate-700/50 rounded-lg p-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="text-xs text-slate-400 mb-1">Playtime</div>
          <div className="text-lg font-semibold text-slate-200">{formatTime(playtime)}</div>
        </div>
        <div>
          <div className="text-xs text-slate-400 mb-1">Prestige Level</div>
          <div className="text-lg font-semibold text-bio-purple">{prestige}</div>
        </div>
      </div>
    </div>
  );
};
