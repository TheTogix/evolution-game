import React from 'react';
import { Github, Heart } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-gradient-to-r from-bio-dark to-bio-darker border-t border-bio-accent/20 mt-12 py-6">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <span>Made with</span>
            <Heart size={16} className="text-bio-danger" />
            <span>by</span>
            <a
              href="https://github.com/TheTogix"
              target="_blank"
              rel="noopener noreferrer"
              className="text-bio-accent hover:text-bio-accent-dark transition-colors font-semibold"
            >
              TheTogix
            </a>
          </div>
          <a
            href="https://github.com/TheTogix/evolution-game"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 bg-bio-accent/10 border border-bio-accent/50 rounded-lg hover:bg-bio-accent/20 transition-all text-bio-accent font-semibold"
          >
            <Github size={18} />
            View Source
          </a>
        </div>
        <div className="text-center text-xs text-slate-500 mt-4">
          Game progress is automatically saved every 30 seconds
        </div>
      </div>
    </footer>
  );
};
