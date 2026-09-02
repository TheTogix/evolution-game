import React from 'react';
import { Zap, Award, Target } from 'lucide-react';

interface AchievementProps {
  name: string;
  description: string;
  progress: number;
}

const AchievementCard: React.FC<AchievementProps> = ({
  name,
  description,
  progress,
}) => (
  <div className="bg-slate-800/40 border border-slate-700/50 rounded-lg p-3 hover:border-bio-accent/50 transition-all">
    <div className="flex items-start gap-3">
      <Award className="text-bio-accent flex-shrink-0 mt-1" size={20} />
      <div className="flex-1">
        <h4 className="font-semibold text-white">{name}</h4>
        <p className="text-xs text-slate-400 mt-1">{description}</p>
        <div className="bg-slate-900/50 rounded-full h-2 mt-2">
          <div
            className="bg-gradient-to-r from-bio-accent to-bio-accent-dark h-2 rounded-full transition-all"
            style={{ width: `${Math.min(progress * 100, 100)}%` }}
          />
        </div>
      </div>
    </div>
  </div>
);

export const AchievementPanel: React.FC = () => {
  const achievements: AchievementProps[] = [
    {
      name: '🌱 First Steps',
      description: 'Reach generation 1',
      progress: 1,
    },
    {
      name: '🔬 Scientist',
      description: 'Unlock 3 technologies',
      progress: 0.5,
    },
    {
      name: '👑 Prestige Master',
      description: 'Reach prestige level 5',
      progress: 0.3,
    },
    {
      name: '🌍 Adaptor',
      description: 'Survive in all environments',
      progress: 0.6,
    },
  ];

  return (
    <div className="bg-gradient-to-br from-bio-dark/80 to-bio-darker/80 border border-bio-accent/30 rounded-lg p-6 backdrop-blur-md">
      <div className="flex items-center gap-2 mb-4">
        <Target className="text-bio-accent" size={24} />
        <h2 className="text-2xl font-bold text-bio-accent">Achievements</h2>
      </div>
      <div className="space-y-3">
        {achievements.map((achievement, idx) => (
          <AchievementCard key={idx} {...achievement} />
        ))}
      </div>
    </div>
  );
};
