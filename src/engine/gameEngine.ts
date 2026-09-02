import { GameState, Resource, Technology } from '../types/game';

const INITIAL_RESOURCES: Resource = {
  food: 100,
  energy: 50,
  dna: 0,
};

const INITIAL_TECHNOLOGIES: Technology[] = [
  {
    id: 'photosynthesis',
    name: 'Photosynthesis',
    description: 'Convert sunlight into energy',
    cost: { food: 50, energy: 0, dna: 10 },
    unlocked: false,
    level: 0,
  },
  {
    id: 'mobility',
    name: 'Mobility',
    description: 'Gain ability to move and hunt',
    cost: { food: 100, energy: 50, dna: 25 },
    unlocked: false,
    level: 0,
  },
  {
    id: 'tool-use',
    name: 'Tool Use',
    description: 'Create and use tools',
    cost: { food: 200, energy: 150, dna: 50 },
    unlocked: false,
    level: 0,
  },
  {
    id: 'agriculture',
    name: 'Agriculture',
    description: 'Cultivate food sources',
    cost: { food: 300, energy: 200, dna: 75 },
    unlocked: false,
    level: 0,
  },
  {
    id: 'civilization',
    name: 'Civilization',
    description: 'Build organized societies',
    cost: { food: 500, energy: 400, dna: 150 },
    unlocked: false,
    level: 0,
  },
];

export class GameEngine {
  private state: GameState;

  constructor() {
    this.state = {
      resources: { ...INITIAL_RESOURCES },
      creatures: [],
      population: 10,
      generation: 1,
      environment: {
        temperature: 20,
        humidity: 50,
        oxygen: 21,
        type: 'plains',
      },
      technologies: JSON.parse(JSON.stringify(INITIAL_TECHNOLOGIES)),
      playtime: 0,
      prestige: 0,
      achievements: [],
    };
  }

  getState(): GameState {
    return this.state;
  }

  // Resource generation
  produceResources(): void {
    const multiplier = 1 + this.state.population * 0.05;
    this.state.resources.food += 10 * multiplier;
    this.state.resources.energy += 5 * multiplier;
    this.state.resources.dna += 2 * multiplier;
  }

  // Population dynamics
  updatePopulation(): void {
    const foodAvailable = this.state.resources.food >= this.state.population * 2;
    const energyAvailable = this.state.resources.energy >= this.state.population;

    if (foodAvailable && energyAvailable) {
      this.state.population = Math.min(this.state.population + 2, 1000);
      this.state.resources.food -= this.state.population * 2;
      this.state.resources.energy -= this.state.population;
    } else {
      this.state.population = Math.max(this.state.population - 1, 1);
    }
  }

  // Environment changes
  changeEnvironment(): void {
    const environments: Array<'plains' | 'forest' | 'tundra' | 'desert' | 'ocean'> = [
      'plains',
      'forest',
      'tundra',
      'desert',
      'ocean',
    ];
    const randomEnv = environments[Math.floor(Math.random() * environments.length)];
    this.state.environment.type = randomEnv;

    // Adjust stats based on environment
    switch (randomEnv) {
      case 'plains':
        this.state.environment.temperature = 20;
        this.state.environment.humidity = 50;
        break;
      case 'forest':
        this.state.environment.temperature = 18;
        this.state.environment.humidity = 80;
        break;
      case 'tundra':
        this.state.environment.temperature = -10;
        this.state.environment.humidity = 40;
        break;
      case 'desert':
        this.state.environment.temperature = 40;
        this.state.environment.humidity = 10;
        break;
      case 'ocean':
        this.state.environment.temperature = 15;
        this.state.environment.humidity = 100;
        break;
    }
  }

  // Technology research
  researchTechnology(techId: string): boolean {
    const tech = this.state.technologies.find((t) => t.id === techId);
    if (!tech) return false;

    const canAfford =
      this.state.resources.food >= tech.cost.food &&
      this.state.resources.energy >= tech.cost.energy &&
      this.state.resources.dna >= tech.cost.dna;

    if (canAfford) {
      this.state.resources.food -= tech.cost.food;
      this.state.resources.energy -= tech.cost.energy;
      this.state.resources.dna -= tech.cost.dna;
      tech.unlocked = true;
      tech.level += 1;

      // Bonus resource generation on unlock
      this.state.resources.dna += 25;
      return true;
    }
    return false;
  }

  // Evolution progression
  evolve(): void {
    this.state.generation += 1;
    this.state.resources.dna = Math.max(0, this.state.resources.dna - 50);
  }

  // Prestige system
  prestige(): void {
    const prestigeGain = Math.floor(Math.sqrt(this.state.generation));
    this.state.prestige += prestigeGain;
    this.resetGame();
  }

  private resetGame(): void {
    this.state.resources = { ...INITIAL_RESOURCES };
    this.state.creatures = [];
    this.state.population = 10 + this.state.prestige;
    this.state.generation = 1;
    this.state.technologies = JSON.parse(JSON.stringify(INITIAL_TECHNOLOGIES));
  }

  // Disaster events
  triggerDisaster(): string {
    const disasters = [
      'meteor',
      'disease',
      'famine',
      'volcanic-eruption',
    ];
    const disaster = disasters[Math.floor(Math.random() * disasters.length)];

    switch (disaster) {
      case 'meteor':
        this.state.population = Math.floor(this.state.population * 0.7);
        return '☄️ Meteor Strike! Population reduced by 30%';
      case 'disease':
        this.state.population = Math.floor(this.state.population * 0.8);
        return '🦠 Disease Outbreak! Population reduced by 20%';
      case 'famine':
        this.state.resources.food = Math.floor(this.state.resources.food * 0.5);
        return '🌾 Famine! Food supplies halved';
      case 'volcanic-eruption':
        this.state.resources.energy = Math.floor(this.state.resources.energy * 0.6);
        return '🌋 Volcanic Eruption! Energy reduced by 40%';
      default:
        return 'Unknown disaster';
    }
  }

  // Autosave game state
  saveGame(): string {
    return JSON.stringify(this.state);
  }

  loadGame(data: string): void {
    try {
      this.state = JSON.parse(data);
    } catch (e) {
      console.error('Failed to load game', e);
    }
  }
}
