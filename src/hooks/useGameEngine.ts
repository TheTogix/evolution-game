import { useState, useEffect, useCallback } from 'react';
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

      // Random disaster (2% chance per tick)
      if (Math.random() < 0.02) {
        const disasterMsg = engine.triggerDisaster();
        setMessage(disasterMsg);
        setTimeout(() => setMessage(''), 3000);
      }

      // Random environment change (1% chance per tick)
      if (Math.random() < 0.01) {
        engine.changeEnvironment();
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
      console.log('Game auto-saved');
    }, AUTOSAVE_INTERVAL);

    return () => clearInterval(autoSave);
  }, [engine]);

  // Load game on mount
  useEffect(() => {
    const savedData = localStorage.getItem('evolutionGameSave');
    if (savedData) {
      try {
        engine.loadGame(savedData);
        setGameState({ ...engine.getState() });
        setMessage('✅ Game loaded successfully!');
        setTimeout(() => setMessage(''), 2000);
      } catch (e) {
        console.error('Failed to load game:', e);
        localStorage.removeItem('evolutionGameSave');
      }
    }
  }, [engine]);

  const research = useCallback(
    (techId: string) => {
      const success = engine.researchTechnology(techId);
      if (success) {
        setMessage('✨ Technology unlocked!');
        setTimeout(() => setMessage(''), 2000);
      } else {
        setMessage('❌ Not enough resources!');
        setTimeout(() => setMessage(''), 2000);
      }
      setGameState({ ...engine.getState() });
    },
    [engine]
  );

  const evolveSpecies = useCallback(() => {
    if (gameState.resources.dna >= 50) {
      engine.evolve();
      setMessage('🧬 Evolution Complete!');
      setTimeout(() => setMessage(''), 2000);
      setGameState({ ...engine.getState() });
    } else {
      setMessage('❌ Not enough DNA!');
      setTimeout(() => setMessage(''), 2000);
    }
  }, [gameState.resources.dna, engine]);

  const prestigeReset = useCallback(() => {
    if (gameState.generation >= 5) {
      if (confirm('Are you sure? Your progress will reset but you\'ll gain permanent bonuses!')) {
        engine.prestige();
        setMessage('👑 Prestige Reset! New run started with bonuses.');
        setTimeout(() => setMessage(''), 3000);
        setGameState({ ...engine.getState() });
      }
    }
  }, [gameState.generation, engine]);

  const changeEnvironment = useCallback(() => {
    engine.changeEnvironment();
    setMessage('🌍 Environment changed!');
    setTimeout(() => setMessage(''), 2000);
    setGameState({ ...engine.getState() });
  }, [engine]);

  return {
    gameState,
    message,
    research,
    evolveSpecies,
    prestigeReset,
    changeEnvironment,
  };
};
