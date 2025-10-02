import { Application, Container } from 'pixi.js';
import { loadMap, MapData } from './map';
import { createCharacter, CharacterData } from './character';

export interface SceneLayers {
  world: Container;      // Main container that camera moves
  map: Container;        // Map tiles layer
  entities: Container;   // Characters, NPCs, objects
  ui: Container;        // UI elements (fixed position)
}

export interface Scene {
  layers: SceneLayers;
  mapData: MapData;
  character: CharacterData;
  worldWidth: number;
  worldHeight: number;
}

export async function buildScene(app: Application): Promise<Scene> {
  // Create layer hierarchy
  const layers: SceneLayers = {
    world: new Container(),
    map: new Container(),
    entities: new Container(),
    ui: new Container()
  };
  
  // Set up container hierarchy
  app.stage.addChild(layers.world);  // Camera will move this
  app.stage.addChild(layers.ui);     // UI stays fixed
  
  layers.world.addChild(layers.map);
  layers.world.addChild(layers.entities);
  
  // Load map into map layer
  console.log('Loading map...');
  const mapData = await loadMap(app);
  layers.map.addChild(mapData.container);
  
  // Create character in entities layer
  console.log('Creating character...');
  // Spawn at actual center of map (40 tiles * 32px / 2 = 640)
  const character = await createCharacter(app, 'socrates', 640, 640);
  
  // Remove character from stage if it was added there
  if (character.sprite.parent) {
    character.sprite.parent.removeChild(character.sprite);
  }
  
  // Add character to entities layer
  layers.entities.addChild(character.sprite);
  
  // Set world dimensions from map
  const worldWidth = mapData.width;
  const worldHeight = mapData.height;
  
  console.log(`World dimensions: ${worldWidth}x${worldHeight}`);
  console.log(`Character spawned at: ${character.x}, ${character.y}`);
  
  return {
    layers,
    mapData,
    character,
    worldWidth,
    worldHeight
  };
}