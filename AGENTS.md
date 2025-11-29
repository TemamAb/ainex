# AGENTS.md — QuantumNex AI Agent Guidelines

## Build & Commands
```bash
# Frontend (Vite-based)
npm run dev          # Start dev server
npm run build        # Build for production
npm run preview      # Preview production build

# Smart Contracts (Hardhat)
npx hardhat compile  # Compile Solidity contracts
npx hardhat test     # Run contract tests

# Python Agents
python core-logic/agents/MultiAgentOrchestrator.py  # Run orchestrator

# Services
node bots/scanner-bot.js    # Start scanner bot
node bots/executor-bot.js   # Start executor bot
```

## Architecture
**Mixed-stack system:** TypeScript/Next/Vite frontend (`app/`), Node.js services (`bots/`, `services/`), Python AI agents (`core-logic/agents/`), Solidity contracts (`contracts/`).

**Data flow:** Python agents → message-broker → Node bots → blockchain (ethers.js/web3.js).

**Key files:**
- `app/components/Dashboard.tsx` — Main UI (React, Tailwind)
- `core-logic/agents/MultiAgentOrchestrator.py` — Agent orchestration
- `bots/message-broker.js` — IPC between agents & bots
- `hardhat.config.cjs` — Smart contract build config

## Code Style
- **TypeScript:** Target ES2022, JSX react-jsx. Path alias: `@/*` maps to root.
- **React:** Functional components + hooks, 'use client' directive for client-side. Tailwind for styling.
- **Imports:** Use `@/*` alias for local imports where possible. Named imports preferred.
- **Naming:** camelCase for variables/functions, PascalCase for components/types. Descriptive names (avoid abbreviations).
- **Error Handling:** Try-catch blocks for async; propagate errors via context/hooks. Use descriptive error messages.
- **Formatting:** ESLint + Next.js Web Vitals config enforced (see `eslint.config.mjs`).
- **Environment:** Load via `.env.local`; key vars include `GEMINI_API_KEY`, contract addresses.

**Note:** When modifying IPC schemas (message-broker), coordinate with Python agents. Update contracts → run `npx hardhat compile` → update deployment scripts.
