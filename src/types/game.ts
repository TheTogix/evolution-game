// Game state types
export interface Resource {
  food: number;
  energy: number;
  dna: number;
}

export interface Creature {
  id: string;
  name: string;
  species: string;
  generation: number;
  traits: Trait[];
  health: number;
  age: number;
}

export interface Trait {
  id: string;
  name: string;
  description: string;
  bonus: number;
  icon: string;
}

export interface Environment {
  temperature: number;
  humidity: number;
  oxygen: number;
  type: 'plains' | 'forest' | 'tundra' | 'desert' | 'ocean';
}

export interface Technology {
  id: string;
  name: string;
  description: string;
  cost: Resource;
  unlocked: boolean;
  level: number;
}

export interface GameState {
  resources: Resource;
  creatures: Creature[];
  population: number;
  generation: number;
  environment: Environment;
  technologies: Technology[];
  playtime: number;
  prestige: number;
  achievements: Achievement[];
}

export interface Achievement {
  id: string;
  name: string;
  description: string;
  unlocked: boolean;
  progress: number;
}
