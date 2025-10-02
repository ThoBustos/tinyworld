# PixiJS Setup Guide
*Date: September 27, 2025*

## What it is
PixiJS is a 2D WebGL renderer that makes drawing sprites and animations fast and easy.

## Installation & Setup
1. Install with yarn: `yarn add pixi.js`
2. Import Application from pixi.js
3. Initialize with fullscreen settings
4. Append canvas to DOM

## Fullscreen Configuration
```typescript
const app = new Application();
await app.init({
    resizeTo: window,      // Auto-resize to window
    background: '#88c070', // Grassy green
    antialias: true
});
document.body.appendChild(app.canvas);
```

## Key Concepts
- **Application**: Main PixiJS instance
- **Stage**: Root container for all graphics
- **Canvas**: HTML5 canvas element for rendering