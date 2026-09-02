import { useState, useEffect } from 'react';
import { GameEngine } from '../engine/gameEngine';
import { GameState } from '../types/game';

const AUTOSAVE_INTERVAL = 30000; // 30 seconds
const GAME_TICK = 2000; // 2 seconds

export const useGameEngine = () => {
  const [engine] = useState(() => new GameEngine());
  const [gameState, setGameState] = useState<GameState>(engine.getState());
  const [message, setMessage] = useState<string>('');

  // Game loop
  useEffect(() => {
    const gameLoop = setInterval(() => {
      engine.produceResources();
      engine.updatePopulation();

      // Random disaster (5% chance)
      if (Math.random() < 0.05) {
        const disasterMsg = engine.triggerDisaster();
        setMessage(disasterMsg);
        setTimeout(() => setMessage(''), 3000);
      }

      setGameState({ ...engine.getState() });
    }, GAME_TICK);

    return () => clearInterval(gameLoop);
  }, [engine]);

  // Autosave
  useEffect(() => {
    const autoSave = setInterval(() => {
      const saveData = engine.saveGame();
      localStorage.setItem('evolutionGameSave', saveData);
    }, AUTOSAVE_INTERVAL);

    return () => clearInterval(autoSave);
  }, [engine]);

  // Load game on mount
  useEffect(() => {
    const savedData = localStorage.getItem('evolutionGameSave');
    if (savedData) {
      engine.loadGame(savedData);
      setGameState({ ...engine.getState() });
    }
  }, [engine]);

  const research = (techId: string) => {
    const success = engine.researchTechnology(techId);
    if (success) {
      setMessage(`✨ Technology unlocked!`);
      setTimeout(() => setMessage(''), 2000);
    } else {
      setMessage(`❌ Not enough resources!`);
      setTimeout(() => setMessage(''), 2000);
    }
    setGameState({ ...engine.getState() });
  };

  const evolveSpecies = () => {
    if (gameState.resources.dna >= 50) {
      engine.evolve();
      setMessage('🧬 Evolution Complete!');
      setTimeout(() => setMessage(''), 2000);
      setGameState({ ...engine.getState() });
    } else {
      setMessage('❌ Not enough DNA!');
      setTimeout(() => setMessage(''), 2000);
    }
  };

  const prestigeReset = () => {
    engine.prestige();
    setMessage('👑 Prestige Reset! New run started with bonuses.');
    setTimeout(() => setMessage(''), 3000);
    setGameState({ ...engine.getState() });
  };

  const changeEnvironment = () => {
    engine.changeEnvironment();
    setGameState({ ...engine.getState() });
  };

  return {
    gameState,
    message,
    research,
    evolveSpecies,
    prestigeReset,
    changeEnvironment,
  };
};
