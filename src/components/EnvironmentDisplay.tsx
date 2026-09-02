import React from 'react';
import { Cloud, Thermometer, Droplets, Wind } from 'lucide-react';
import { Environment } from '../types/game';

interface EnvironmentDisplayProps {
  environment: Environment;
  onChangeEnvironment: () => void;
}

const getEnvironmentColor = (type: string) => {
  switch (type) {
    case 'plains':
      return 'from-green-500/20 to-green-600/20 border-green-500/50';
    case 'forest':
      return 'from-emerald-600/20 to-green-700/20 border-emerald-500/50';
    case 'tundra':
      return 'from-blue-400/20 to-cyan-500/20 border-blue-400/50';
    case 'desert':
      return 'from-orange-500/20 to-yellow-500/20 border-orange-500/50';
    case 'ocean':
      return 'from-blue-600/20 to-blue-700/20 border-blue-500/50';
    default:
      return 'from-slate-500/20 to-slate-600/20 border-slate-500/50';
  }
};

const getEnvironmentEmoji = (type: string) => {
  switch (type) {
    case 'plains':
      return '🌾';
    case 'forest':
      return '🌲';
    case 'tundra':
      return '❄️';
    case 'desert':
      return '🏜️';
    case 'ocean':
      return '🌊';
    default:
      return '🌍';
  }
};

export const EnvironmentDisplay: React.FC<EnvironmentDisplayProps> = ({
  environment,
  onChangeEnvironment,
}) => {
  return (
    <div
      className={`bg-gradient-to-br ${getEnvironmentColor(
        environment.type
      )} border rounded-lg p-6 backdrop-blur-sm`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-4xl">{getEnvironmentEmoji(environment.type)}</span>
          <div>
            <h3 className="text-2xl font-bold text-white capitalize">
              {environment.type}
            </h3>
            <p className="text-sm text-slate-300">Current Environment</p>
          </div>
        </div>
        <button
          onClick={onChangeEnvironment}
          className="px-4 py-2 bg-bio-accent/20 border border-bio-accent/50 text-bio-accent rounded-lg hover:bg-bio-accent/30 transition-all font-semibold"
        >
          Change
        </button>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="flex items-center gap-2">
          <Thermometer size={18} className="text-orange-400" />
          <div>
            <div className="text-xs text-slate-300">Temperature</div>
            <div className="font-semibold text-white">{environment.temperature}°C</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Droplets size={18} className="text-blue-400" />
          <div>
            <div className="text-xs text-slate-300">Humidity</div>
            <div className="font-semibold text-white">{environment.humidity}%</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Wind size={18} className="text-cyan-400" />
          <div>
            <div className="text-xs text-slate-300">Oxygen</div>
            <div className="font-semibold text-white">{environment.oxygen}%</div>
          </div>
        </div>
      </div>
    </div>
  );
};
