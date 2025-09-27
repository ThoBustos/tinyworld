# TinyWorld Web

PixiJS frontend for the TinyWorld simulation.

## Setup from Scratch

### Prerequisites
- Node.js 18+ and yarn
- Or use [nvm](https://github.com/nvm-sh/nvm) to manage Node versions

### Install Node.js
```bash
# With nvm (recommended)
nvm install 20
nvm use 20

# Or download from https://nodejs.org/
```

### Install Dependencies
```bash
# From the web directory
cd web

# Install all packages
yarn install
```

### Run Development Server
```bash
# Start Vite dev server with hot reload
yarn dev

# Opens at http://localhost:5173
```

### Environment Variables
Copy `.env.example` to `.env` for local development:
```bash
cp .env.example .env
```

## Project Structure
```
web/
├── src/
│   ├── main.ts         # Entry point
│   ├── World.ts        # World renderer
│   ├── Character.ts    # Character class
│   └── types.ts        # TypeScript types
├── public/             # Static assets
├── index.html          # HTML entry
├── package.json        # Dependencies
├── tsconfig.json       # TypeScript config
└── vite.config.ts      # Vite bundler config
```

## Available Scripts
```bash
# Development
yarn dev             # Start dev server

# Production
yarn build           # Build for production
yarn preview         # Preview production build
```

## Development Notes
- Vite proxy is configured to forward `/api` and `/ws` to the backend at `localhost:8000`
- TypeScript is configured with strict mode
- Path alias `@/` points to `src/` directory