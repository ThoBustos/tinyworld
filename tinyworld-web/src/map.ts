import { Application, Container, Sprite, Texture, Assets, Rectangle } from 'pixi.js';

export interface TilemapData {
  width: number;
  height: number;
  tilewidth: number;
  tileheight: number;
  layers: Array<{
    data: number[];
    width: number;
    height: number;
    name: string;
  }>;
  tilesets: Array<{
    firstgid: number;
    source: string;
    image?: string;
    tilecount?: number;
    columns?: number;
  }>;
}

export interface MapData {
  container: Container;
  width: number;
  height: number;
}

export async function loadMap(app: Application): Promise<MapData> {
  const mapContainer = new Container();
  
  // Load tilemap JSON
  const mapData: TilemapData = await fetch('/assets/tilemaps/philoagents-town.json')
    .then(res => res.json());
  
  // Load tileset texture - using the main tileset
  const tilesetTexture = await Assets.load('/assets/tilesets/tuxmon-sample-32px-extruded.png');
  
  // Tilemap properties - ensure we use the correct values
  const tileWidth = mapData.tilewidth || 32;
  const tileHeight = mapData.tileheight || 32;
  const mapWidth = mapData.width;    // Should be 40
  const mapHeight = mapData.height;  // Should be 40
  
  console.log(`Map dimensions: ${mapWidth}x${mapHeight} tiles, ${tileWidth}x${tileHeight}px per tile`);
  
  // Use the correct column count from tilemap data (24 columns)
  const tilesetColumns = 24; // Fixed: use actual columns from tilemap
  
  // Create separate containers for below and above player layers
  const belowPlayerContainer = new Container();
  const abovePlayerContainer = new Container();
  
  // Render each layer
  for (const layer of mapData.layers) {
    if (layer.data) {
      const layerContainer = new Container();
      const isAbovePlayer = layer.name === 'Above Player';
      
      for (let y = 0; y < mapHeight; y++) {
        for (let x = 0; x < mapWidth; x++) {
          const tileIndex = layer.data[y * mapWidth + x];
          
          // Skip empty tiles
          if (tileIndex === 0) continue;
          
          // Adjust for Tiled's 1-based indexing
          const tileId = tileIndex - 1;
          
          // Calculate source rectangle in tileset (accounting for extrusion)
          const srcX = (tileId % tilesetColumns) * 34 + 1; // +1 to skip extrusion
          const srcY = Math.floor(tileId / tilesetColumns) * 34 + 1;
          
          // Create texture from tileset region
          const tileTexture = new Texture({
            source: tilesetTexture.source,
            frame: new Rectangle(srcX, srcY, 32, 32)
          });
          
          // Create and position sprite
          const sprite = new Sprite(tileTexture);
          sprite.x = x * tileWidth;
          sprite.y = y * tileHeight;
          
          layerContainer.addChild(sprite);
        }
      }
      
      // Add layer to appropriate container
      if (isAbovePlayer) {
        abovePlayerContainer.addChild(layerContainer);
      } else {
        belowPlayerContainer.addChild(layerContainer);
      }
    }
  }
  
  // Add both containers to map (below player first, then above)
  mapContainer.addChild(belowPlayerContainer);
  // Note: abovePlayerContainer would be added after entities in scene.ts if needed
  
  // Calculate actual world dimensions (40 tiles * 32px = 1280x1280)
  const worldWidth = mapWidth * tileWidth;
  const worldHeight = mapHeight * tileHeight;
  
  console.log(`World size: ${worldWidth}x${worldHeight}px`);
  
  return {
    container: mapContainer,
    width: worldWidth,
    height: worldHeight
  };
}