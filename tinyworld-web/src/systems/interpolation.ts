// ## Entity Interpolation System
// Smooths entity movement between network updates

// ## Core responsibilities:
// - Interpolate entity positions between server updates
// - Handle network latency and jitter
// - Predict future positions based on velocity
// - Reconcile client prediction with server state
// - Smooth visual corrections to avoid snapping

// ## Techniques:
// - Linear interpolation for past positions
// - Extrapolation for current player movement
// - Hermite interpolation for smoother curves
// - Position buffer for handling out-of-order packets

// ## Usage example:
// const interpolator = new InterpolationSystem();
// interpolator.addSnapshot(entityId, position, timestamp);
// const smoothPosition = interpolator.getPosition(entityId, currentTime);