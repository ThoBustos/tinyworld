# Render Loop & Animation
*Date: September 27, 2025*

## What it is
The client-side loop that draws frames at 60 FPS using requestAnimationFrame.

## PixiJS Ticker
- Automatically uses requestAnimationFrame
- Provides delta time for smooth animations
- Runs at monitor refresh rate (usually 60fps)

## Basic Loop Structure
```typescript
app.ticker.add((ticker) => {
    // ticker.deltaTime = time since last frame
    updatePositions(ticker.deltaTime);
    updateAnimations(ticker.deltaTime);
});
```

## Animation Example
```typescript
let time = 0;
app.ticker.add(() => {
    time += 0.02;
    // Gentle sway animation
    house.scale.y = 1 + Math.sin(time) * 0.02;
});
```