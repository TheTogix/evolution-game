import React, { useState } from 'react';
import { useGameEngine } from './hooks/useGameEngine';
import { Header } from './components/Header';
import { Footer } from './components/Footer';
import { ResourcePanel } from './components/ResourcePanel';
import { PopulationPanel } from './components/PopulationPanel';
import { EnvironmentDisplay } from './components/EnvironmentDisplay';
import { TechTree } from './components/TechTree';
import { PrestigePanel } from './components/PrestigePanel';
import { AchievementPanel } from './components/AchievementPanel';
import { Notification, EvolutionButton, GameStats } from './components/Utilities';

function App() {
  const {
    gameState,
    message,
    research,
    evolveSpecies,
    prestigeReset,
    changeEnvironment,
  } = useGameEngine();

  const [notificationMsg, setNotificationMsg] = useState<string>('');

  React.useEffect(() => {
    if (message) {
      setNotificationMsg(message);
    }
  }, [message]);

  const handleNewGame = () => {
    if (confirm('Are you sure you want to start a new game? Current progress will be lost.')) {
      localStorage.removeItem('evolutionGameSave');
      window.location.reload();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-bio-dark via-bio-darker to-black text-slate-100">
      <Header generation={gameState.generation} onReset={handleNewGame} />

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Top Section: Resources and Population */}
        <div className="mb-8">
          <ResourcePanel
            food={gameState.resources.food}
            energy={gameState.resources.energy}
            dna={gameState.resources.dna}
          />
          <PopulationPanel
            population={gameState.population}
            generation={gameState.generation}
          />
        </div>

        {/* Main Game Area */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Left Column: Evolution & Environment */}
          <div className="lg:col-span-1 space-y-6">
            <div>
              <EvolutionButton
                dna={gameState.resources.dna}
                onClick={evolveSpecies}
              />
            </div>
            <EnvironmentDisplay
              environment={gameState.environment}
              onChangeEnvironment={changeEnvironment}
            />
            <PrestigePanel
              prestigeLevel={gameState.prestige}
              generation={gameState.generation}
              onPrestige={prestigeReset}
            />
            <GameStats playtime={gameState.playtime} prestige={gameState.prestige} />
          </div>

          {/* Right Column: Technology Tree */}
          <div className="lg:col-span-2">
            <TechTree
              technologies={gameState.technologies}
              onResearch={research}
            />
          </div>
        </div>

        {/* Achievements Section */}
        <div className="mb-8">
          <AchievementPanel />
        </div>

        {/* Game Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-gradient-to-br from-slate-900/50 to-slate-950/50 border border-slate-700/50 rounded-lg p-6">
            <h3 className="text-xl font-bold text-bio-accent mb-3">How to Play</h3>
            <ul className="space-y-2 text-sm text-slate-300">
              <li>✓ Gather resources automatically over time</li>
              <li>✓ Manage your population with food and energy</li>
              <li>✓ Research technologies to progress faster</li>
              <li>✓ Evolve your species with DNA</li>
              <li>✓ Adapt to changing environments</li>
              <li>✓ Use prestige for permanent bonuses</li>
            </ul>
          </div>

          <div className="bg-gradient-to-br from-slate-900/50 to-slate-950/50 border border-slate-700/50 rounded-lg p-6">
            <h3 className="text-xl font-bold text-bio-accent mb-3">Game Features</h3>
            <ul className="space-y-2 text-sm text-slate-300">
              <li>🎮 Idle & Active gameplay</li>
              <li>💾 Auto-save every 30 seconds</li>
              <li>🌍 Multiple environments with unique challenges</li>
              <li>🧬 Deep evolution and prestige system</li>
              <li>🏆 Achievement tracking</li>
              <li>📈 Unlimited progression</li>
            </ul>
          </div>
        </div>
      </main>

      <Footer />

      {notificationMsg && (
        <Notification
          message={notificationMsg}
          onClose={() => setNotificationMsg('')}
        />
      )}
    </div>
  );
}

export default App;
