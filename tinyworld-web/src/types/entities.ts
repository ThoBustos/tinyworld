// ## Entity Type Definitions
// Shared types for all game entities

// ## Entity types:
// - Base Entity interface (id, position, type)
// - Player entity (extends base with inventory, stats)
// - NPC entity (extends base with AI state, dialogue)
// - Interactive object (doors, flowers, chests)
// - Projectile entity (for future combat)

// ## Design principles:
// - Keep in sync with backend entity models
// - Use discriminated unions for entity variants
// - Include render-specific properties (sprite, animation)
// - Separate logical state from visual representation

// ## Example interfaces:
// Entity, Player, NPC, InteractiveObject,
// Position, Velocity, EntityState