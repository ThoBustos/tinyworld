// ## Interaction Detection System
// Handles proximity-based interactions with objects and NPCs

// ## Core responsibilities:
// - Detect when player is near interactable objects
// - Calculate interaction ranges and angles
// - Manage interaction states and cooldowns
// - Trigger appropriate UI prompts
// - Handle interaction input and validation

// ## Interaction types:
// - Proximity triggers (automatic when near)
// - Manual interactions (require player input)
// - Directional interactions (must face object)
// - Timed interactions (hold to complete)

// ## Usage example:
// const interaction = new InteractionSystem();
// interaction.registerObject(objectId, position, radius);
// const nearby = interaction.checkProximity(playerPos);
// interaction.triggerInteraction(objectId);