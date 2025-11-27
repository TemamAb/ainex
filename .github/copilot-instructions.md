<!-- Copilot instructions for AI coding agents working on this repository -->
# Copilot Instructions — QuantumNex (concise)

Purpose: Help an AI coding assistant be immediately productive in this mixed-stack repo (TypeScript/Next/Vite, Node.js services, Python agents, Solidity contracts).

- **Big Picture:**
  - **Frontend:** `app/` contains a Next.js-style app (see `next.config.ts`, `app/page.tsx`, `layout.tsx`). Note: `package.json` currently defines Vite scripts (`dev`, `build`, `preview`) — confirm which dev server is authoritative before changing scripts.
  - **AI Agents (Python):** `core-logic/agents/` contains Python agents (e.g., `MultiAgentOrchestrator.py`, `DecisionAgent.py`). These communicate with Node bots/services.
  - **Bots & Node Services:** `bots/` contains JS services (scanner, executor, message-broker). `services/` and `infrastructure/` hold reusable TS/JS modules (e.g., `websocket-manager.js`, `rpc-optimizer.js`).
  - **Blockchain:** `contracts/` (Solidity) + `artifacts/contracts/`. Hardhat config is at `hardhat.config.js`.
  - **Deployment & Infra:** `docker-compose.yml`, `Dockerfile`, `deployment/` (Kubernetes YAML, deployment manager JS).

- **Typical data flow / integration points you should know:**
  - Agents (Python) -> publish messages to `bots/message-broker.js` or similar broker -> bots (JS) consume -> `execution/` and `contracts/` interactions via ethers/web3.
  - Cross-language integration is via message broker files and shared environment variables (see `bots/message-broker.js`, `infrastructure/websocket-manager.js`).

- **Essential files to inspect when changing behavior:**
  - `core-logic/agents/MultiAgentOrchestrator.py` — orchestrates agent behavior.
  - `bots/message-broker.js` — central IPC/queuing pattern connecting agents and bots.
  - `bots/executor-bot.js`, `bots/scanner-bot.js` — concrete bot implementations.
  - `deployment/deployment-manager.js` — deployment orchestration and environment assumptions.
  - `hardhat.config.js` and `contracts/*.sol` — smart contract build/test flow.
  - `requirements.txt` — Python dependencies for agents.
  - `package.json` — Node script surface; note `dev` runs `vite` here.

- **Local dev & run commands (discovered in repo):**
  - Install JS deps: `npm install`
  - Start frontend (per README/script): `npm run dev`
  - Install Python deps: `python -m venv .venv && .venv\Scripts\Activate.ps1; pip install -r requirements.txt` (Windows PowerShell example)
  - Run a Python agent (example): `python core-logic/agents/MultiAgentOrchestrator.py`
  - Run a bot (example): `node bots/scanner-bot.js`
  - Hardhat: install dev deps (if missing) then `npx hardhat compile` and `npx hardhat test`.
  - Docker: `docker-compose up --build` to run containerized stack.

- **Repo-specific conventions / patterns**
  - Mixed-language services: prefer not to change messaging interfaces in `bots/message-broker.js` without coordinating the Python agents in `core-logic/agents/`.
  - Solidity artifacts are placed in `artifacts/contracts/` — use Hardhat pipeline (`hardhat.config.js`) to regenerate.
  - Environment variables: README references `.env.local` and `GEMINI_API_KEY`; many services use `dotenv` so keep `.env`/`.env.local` in mind.
  - Frontend styling: Tailwind is configured (`tailwind.config.ts`) — update design tokens there.

- **When editing or adding features**
  - If you change an IPC/message schema, update both `bots/message-broker.js` and corresponding Python code in `core-logic/agents/`.
  - For contract changes: update `contracts/*.sol`, run `npx hardhat compile`, and update any deployment scripts under `deployment/`.
  - For new services: add npm script to `package.json` and document expected env vars in `README.md` or `deployment/environment-config.js`.

- **Quick grep patterns (useful examples):**
  - Find orchestrator: `rg "MultiAgentOrchestrator" -n`
  - Find message-broker usage: `rg "message-broker" -n`
  - List Python agents: `ls core-logic/agents`

- **What not to assume:**
  - Do not assume a single uniform build system — this repo mixes Next/Vite, Node, Python, and Hardhat.
  - Do not change runtime env var names — they are referenced across layers (frontend/backend/agents/deployment).

- **What to ask the human owner:**
  - Confirm which frontend dev server is primary (Next vs. Vite) and the canonical `npm` scripts to use.
  - Provide any missing runbook steps for orchestrating Python agents with Node bots in local dev.

If any section is unclear or you want more detail (examples of message payloads, common agent entrypoints to test, or a simple runbook), tell me which area to expand and I'll iterate.
