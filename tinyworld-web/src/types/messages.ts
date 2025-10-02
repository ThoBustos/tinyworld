// ## WebSocket Message Type Definitions
// Defines all message types exchanged between client and server

// ## Message categories:
// - Movement messages (position updates, velocity changes)
// - Interaction messages (object interactions, NPC dialogs)
// - State sync messages (world state, entity spawning)
// - System messages (connection, errors, pings)

// ## Design principles:
// - All messages have a 'type' discriminator field
// - Include timestamps for lag compensation
// - Use minimal data for frequent messages (positions)
// - Include validation for critical operations

// ## Example types:
// PositionUpdate, EntitySpawn, InteractionRequest,
// StateSync, ChatMessage, SystemNotification