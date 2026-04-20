# Project Deep Dive: ProtEngine Labs Drug Discovery AI

---

## 1. PROJECT IDENTITY

**Project Name:** Drug Discovery AI (by ProtEngine Labs)  
**Purpose:** A multi-agent precision medicine AI pipeline designed for novel drug discovery. It processes genetic mutations, generates drug candidates, evaluates their efficacy, predicts selectivity, and outputs synthesis routes—all within a fast, 60-second computational process.  
**One-Line Summary:** A 22-agent AI platform orchestrating biological querying, molecular generation, docking, simulation, and synthesis pathing to discover novel cancer therapeutics from specific gene mutations.  
**Problem It Solves:** Dramatically reduces the time required to design potential drug candidates for specific genetic mutations (like cancer drug resistance, e.g., EGFR T790M). It integrates structural biology, computational chemistry, docking algorithms, and clinical context into a unified, rapid pipeline.  
**Intended User/Audience:** Computational biologists, bioinformaticians, medical researchers, and clinic workers evaluating cutting-edge AI pipelines for precision medicine.  
**Project Type:** Full-stack Monorepo (Web API + Web Dashboard App)

---

## 2. TECH STACK & DEPENDENCIES

### Backend Stack
- **Language:** Python 3.11/3.14 (via multiple `requirements.txt` environment configs)
- **Framework:** FastAPI 0.115 + Uvicorn 0.32.1 (Performance-focused ASGI framework for REST & SSE streaming)
- **AI/LLM Architecture:** LangChain 0.3.13, LangGraph 0.2.60 (Pipeline Orchestrator), LangSmith 0.1.147 (Observability)
- **LLM Providers:** OpenAI 1.59.3 (GPT-4o-mini), Groq 0.13.0 (Llama 3.3 70B), Together 1.3.11 (Mistral 7B)
- **Chemistry & Bio:** RDKit 2024.9.5 (Molecule Generation/ADMET), Biopython 1.84, PyRx Vina (subprocess docking executable), OpenBabel, Fpocket (System dependency)
- **Database Logic:** SQLAlchemy 2.0.36 (Asyncio), Asyncpg 0.30.0 (PostgreSQL driver)
- **Data/Math:** Numpy, Pillow (Images), ReportLab (PDFs)
- **Network / Async:** Requests, Httpx, SSE-Starlette

### Frontend Stack
- **Language:** TypeScript 5
- **Framework:** Next.js 16 (React 19.2.4) utilizing the App Router pattern
- **Styling:** Tailwind CSS v4, Radix UI Primitives, shadcn/ui components, `tw-animate-css`
- **Animations:** GSAP 3.12.7, Framer Motion 11.15.0
- **Data Visualization & 3D:** D3.js 7.9.0 (Force-directed graphs / Tree), Recharts 2.13.3 (ADMET Radar charts), NGL 2.4.0 (3D molecular viewer)
- **Linting & Formatting:** Biome 2.4.12 (Replaces ESLint + Prettier)
- **State Management & Data fetching:** Custom React Hooks (`useSSEStream`, `useAnalysis`)
- **Other utilities:** `clsx`, `tailwind-merge`, `lucide-react`, `sonner`

### Database & Cloud
- **Database Engine:** Neon PostgreSQL (Serverless PostgreSQL)
- **Cloud/External APIs:** PubMed NCBI, UniProt, RCSB PDB, PubChem, ClinicalTrials.gov v2

---

## 3. PROJECT STRUCTURE

```text
HF26-24/ (Monorepo root)
├── backend/                  # Python backend application
│   ├── agents/               # 22 LangGraph autonomous agents (Mutation, Planner, Docking...)
│   ├── routers/              # FastAPI specific controllers/routes
│   ├── pipeline/             # LangGraph state definitions and orchestrator engine
│   ├── utils/                # Helper systems (DB init, LLM fallback router, caching)
│   ├── data/                 # Caching and static reference sets
│   ├── evaluation/           # Benchmarking & QA testing scripts
│   └── main.py               # Uvicorn entry point
│
├── frontend/                 # Next.js web interface
│   ├── app/                  # Next.js App Router root
│   │   ├── analysis/         # Analysis dynamic route [sessionId] page
│   │   ├── components/       # Massive component library
│   │   │   ├── analysis/     # MoleculeCard, KnowledgeGraph, PipelineStatus, EvolutionTree
│   │   │   ├── layout/       # AppShell, Footer, NavBar
│   │   │   ├── settings/     # Config components
│   │   │   └── ui/           # Radix/shadcn UI atoms
│   │   ├── discoveries/      # Route: Saved pipeline runs
│   │   ├── settings/         # Route: App configurations
│   │   ├── hooks/            # Custom TS Hooks (useAnalysis, useSSEStream, etc.)
│   │   └── lib/              # api definitions, theme constants, types.ts
│   └── biome.json            # Fast Rust-based linter specification
│
├── README.md                 # Entry documentation
├── AGENTS.md                 # 22-agent pipeline architectural plan
├── CLAUDE.md                 # AI specific rules
└── skills/                   # Internal AI workspace skill commands
```

**Key Config Files:**
- `backend/requirements.txt`: Defines all production Python pip dependencies
- `frontend/package.json`: Main registry for NPM scripts, modules, and dev dependencies
- `frontend/next.config.ts`: Next.js config (typically holds redirects, rewrites, strict mode)
- `backend/.env`: Backend credentials, database connections, and LLM keys

---

## 4. ARCHITECTURE & DESIGN PATTERNS

- **System Architecture:** Separated Monolith / Microservices setup. The Next.js frontend acts as purely a presentation SPA/SSR client connecting to a FastAPI Python backend server. The AI pipeline is orchestrated using an **Event-Driven Agentic Pipeline** orchestrated by LangGraph.
- **Design Patterns:**
  - **Graph/State Machine Pattern:** The LangGraph pipeline operates linearly and cyclically on a shared memory object, feeding context from one agent to the next.
  - **Fallback Strategy Pattern:** Multi-LLM fallback architecture. (OpenAI → Groq → Together).
  - **Provider / Context Pattern:** React environment distributes Theme, State, and Pipeline contexts.
  - **Component Composition:** Frontend uses shadcn/ui to compose complex interfaces.
- **State Management:** Next.js manages component state locally with React Context/Hooks. Intensive streaming data is piped directly into state atoms using a specialized hook (`useSSEStream`) which parses Server-Sent Events from the FastAPI backend.

---

## 5. HOW IT RUNS

**Installation:**
1. **Database Setup:** Requires a Neon Postgres string set to `DATABASE_URL` in `backend/.env`.
2. **Backend:**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Frontend:**
   ```bash
   cd frontend
   npm install
   ```

**Running Locally:**
- Unix: Execute `./start.sh`
- Windows: Execute `start.bat`
*(Alternatively)*
- Backend: `uvicorn main:app --reload --port 8000`
- Frontend: `npm run dev` (starts on port 3000)

**Environment Variables Required:**
- **Backend:** `OPENAI_API_KEY`, `GROQ_API_KEY`, `TOGETHER_API_KEY`, `NCBI_API_KEY`, `LANGCHAIN_API_KEY` (LangSmith), `DATABASE_URL` (Neon PostgreSQL), `AUTO_SAVE_DISCOVERIES`.
- **Frontend:** `NEXT_PUBLIC_API_URL` (points to `:8000`), `NEXT_PUBLIC_APP_NAME`

---

## 6. ROUTING & NAVIGATION

### Frontend Routes (Next.js App Router)
- `/` - Landing Page (Hero, Demo, Inputs)
- `/analysis/[sessionId]` - Primary interactive workspace dashboard showing all pipeline tabs.
- `/discoveries` - Datatable library of previously completed and saved drug designs.
- `/settings` - Theme selection and API Key configurations.
- Auxiliary text pages: `/about-us`, `/privacy-policy`, `/terms-and-conditions`, `/research`

### Backend Routes (FastAPI)
All prefixed with `/api`
- `/api/analysis/*` - Endpoints related to initializing pipeline runs.
- `/api/stream/*` - SSE endpoint serving live log events from the 22 LangGraph agents.
- `/api/status/*` - Current pipeline state polling.
- `/api/molecules/*` - Fetch generated molecule data.
- `/api/search/*`, `/api/export/*`, `/api/benchmark/*`, `/api/themes/*`
- `/api/discoveries/*` - CRUD endpoints mapped to Neon PostgreSQL database.
- `/api/docked_poses/*`, `/api/structure/*` - Returns PDB caches and docking 3D coordinates.

---

## 7. API & NETWORK CALLS

**Internal Network:**
Frontend makes fetch calls and instantiates `EventSource` web APIs against `http://localhost:8000/api/stream...`.

**External Services Triggered:**
1. **PubMed / NCBI:** Fetching clinical context, literature, and active trial details.
2. **PubChem:** Compound analysis and baseline inhibitor searching.
3. **RCSB PDB / UniProt:** Retrieving generic sequence data, caching PDB structural files.
4. **ClinicalTrials.gov (v2 API):** Seeking matching context for patients.
5. **OpenAI / Groq / Together AI APIs:** Core inference for reasoning, extraction protocols, and bioisostere definitions.
6. **ESMFold API:** Protein structure prediction if PDB data lacks confidence.

---

## 8. DATA FLOW

1. **Intake:** User inputs a query (e.g., "EGFR T790M") via the Next.js `QueryInput.tsx`.
2. **Init:** Next.js sends POST `/api/analysis` to FastAPI.
3. **Execution Pipeline:** LangGraph begins running `PlannerAgent` → `Fetch` → `Pocket` → `Generate` → `Docking` → `Validate` → `Assess`. Real-time `yield` statements are sent via SSE to the frontend `useSSEStream` hook.
4. **Visualisation:** Data chunks hydrate the UI: NGL viewers build 3D proteins, D3 builds Evolution trees. Recharts updates ADMET polygons.
5. **Persistence:** On completion (or `AUTO_SAVE_DISCOVERIES=true`), Python writes the entire complex JSON graph to Neon PostgreSQL asynchronous via SQLAlchemy.

---

## 9. AUTHENTICATION & AUTHORIZATION

Currently designed as a single-tenant or open demo platform for Hackathons. Authentication/Authorization relies entirely on API key presence (`GROQ_API_KEY`) on the server to execute generation logic. 

---

## 10. DATABASE & STORAGE

**Database:** Neon (Serverless PostgreSQL) configured via async SQLAlchemy.
**Core Abstractions:**
- The database schema primarily stores Pipeline Output runs—a giant structured JSON artifact holding agent payloads, molecule structures, docking scores, metrics, and timestamps.
- **Cache Storage:** `backend/data/` acts as an ephemeral or permanent cache for fetched `.pdb` files from ESMFold/RCSB to avoid rate limiting and speed up the simulation.

---

## 11. UI & FRONTEND 

- **Component Philosophy:** Extremely granular and highly animated.
- **Library:** Next.js Server Components, heavily interspersed with `'use client'` interactive nodes.
- **Visuals:** Uses Tailwind CSS v4 and a custom `theme.ts` script for a modern, flat, amber "precision" theme styling.
- **Key Dashboards:**
  - `MoleculeCard.tsx`: Condenses Binding Affinity GNN scores, SA (Synthesis Accessibility), and Molecular data.
  - `MDValidation.tsx` / `SelectivityBadge.tsx`: Displays analytical matrices using clean numeric ± ranges.
  - `PipelineStatus.tsx`: Shows live waterfall status of all 22 agents via Framer Motion sequences.
  - `EvolutionTree.tsx`: Custom D3 topology showing how scaffolds mutated into final forms.
- **3D Viewer:** Built with NGL Viewer inside `MoleculeViewer3D.tsx`.

---

## 12. BUSINESS LOGIC

The core 22 algorithms dictate the system’s logic, executing sequentially or parallelized:
1. **Mutation Parsing & Planner:** Isolates gene, sets execution.
2. **Structural Prep & Pocket Detection (fpocket):** Calculates 3-Dimensional binding geometry.
3. **Generative Modeling & Docking (Vina/Gnina):** Proposes SMARTS scaffold hops and uses CPU-executed grid docking.
4. **Dual Selectivity Pipeline:** Docks against target versus 10 off-targets. Keeps compounds over a `3.2x` selectivity threshold.
5. **ADMET & Toxicity:** Filters out molecules failing "Rule of 5" or carrying risky toxophores.
6. **MD & GNN validation:** Molecular dynamics simulate energy stabilities (`MM-GBSA dg`).
7. **Synthesis Paths:** `ASKCOS` modeling is simulated/requested for creating lab synthesis recipes.
8. **Final Assembly:** Re-ranks leads using a confidence matrix: MIN(structure, docking, esm1v, gnn).

---

## 13. INTEGRATIONS & THIRD-PARTY SERVICES

- **LangSmith:** Enabled asynchronously. It logs LangGraph states, tracking LLM hallucinations and execution token counts.
- **RDKit Data:** Relies natively on RDKit's open binaries to transform strings to SVG elements and calculate lipophilicity.

---

## 14. SECURITY

- **CORS Config:** FastAPI middleware currently accepts `["*"]` due to its internal/development architecture. It must securely lockdown before a real-world prod push.
- **API Defense:** Minimal. No hard rate limiting configured at the Python app level (relies heavily on LLM provider rate limits).
- **Secrets Management:** Kept securely in `.env.local` / `.env` files.
- **Validation:** Pydantic is intensely applied to strict validation for both LLM output guarantees and HTTP inputs.

---

## 15. TESTING

- **Framework:** Custom Evaluation Suite & Python assertions.
- **Benchmark Script:** `evaluation.benchmark_runner.py` executes synthetic runs testing baseline accuracy of the multi-LLM router format.
- **Agent Validations:** Scripts such as `test_pocket_fix.py`, `test_variant_stress.py`, `test_production_docking.py`.
- **CI/CD:** Github Actions enabled. 
  - `backend-ci.yml`: Runs `ruff`, `mypy`, and python tests.
  - `frontend-ci.yml`: Runs Biome linter and TS Typechecks (`tsc --noEmit`).

---

## 16. DEPLOYMENT & INFRASTRUCTURE

- **Environment:** Expected to be deployed on serverless web edge networks (like Vercel for the frontend) and a managed Docker container service for the backend (due to Fpocket and 3D dependencies).
- **Database:** Managed via Neon serverless DB.
- **Local Dev:** `start.sh` easily spins up the dual VENV and NPM environments concurrently.

---

## 17. PERFORMANCE & OPTIMIZATION

- **ESMFold Caching:** Deep logic ensures expensive biological structure predictions (`mutant_pdb_path`) are cached persistently to `data/structure_cache/`.
- **Parallel Fetching:** Agents 3, 4, 5, 6 execute entirely async mapping across different biological public APIs.
- **Trimming Targets:** GNN filter artificially blocks molecules dropping processing from 30 variants to EXACTLY 2 variants prior to the heavy MD-Validation stage, saving hours of OpenMM compute cycles.
- **Frontend Optimization:** Framer Motion limits re-rendering logic. `biome` ensures tightly parsed AST optimizations.

---

## 18. KNOWN ISSUES, TODOS & TECH DEBT

- **Docking Dependencies:** Requires native OS installations of OpenBabel and Fpocket. The system uses fallbacks, but precision degrades if these native C++ apps are missing.
- **Security Debt:** FastAPI wide open `CORS = ["*"]`.
- **Testing:** No E2E Selenium/Cypress UI validations exist, relies heavily on back-end synthetic pipeline benchmarks.

---

## 19. SUMMARY & QUICK REFERENCE

**Summary:** 
Drug Discovery AI is a complex, LangGraph-backed biological pipeline that uses 22 sequential and parallel autonomous agents to transform a human gene mutation prompt into an optimized, docked, simulated, and synthesizable molecular drug lead within 90 seconds. It packages heavy computational logic into a consumer-grade, highly-animated Next.js workspace.

**Quick Start Execution:**
1. Clone the repo and navigate to `/backend`
2. Configure `.env` with `GROQ_API_KEY`
3. Run Unix script: `./start.sh`
4. Visit `localhost:3000`

**Key Files Cheat Sheet:**
- `AGENTS.md`: The philosophical and functional roadmap of the entire 22-agent AI pipeline.
- `backend/pipeline/`: Contains the LangGraph execution orchestrator that connects the agents.
- `backend/main.py`: The entry point for FastAPI routing and Streaming configurations.
- `frontend/app/analysis/[sessionId]/page.tsx`: The primary complex interactive dashboard rendering all discovery metrics.
- `frontend/hooks/useSSEStream.ts`: The bridge that allows the client to subscribe to the agentic process in real-time.
