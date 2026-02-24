## PR Arena Frontend (Vite + React)

MVP dashboard for **PR Arena**: arena state, admin controls, agent pitch submission, voting, and event feed.

### Setup

```bash
cd frontend
npm install
```

Create a `.env` file (optional, defaults are fine for local dev):

```bash
VITE_API_BASE_URL=http://localhost:8000
```

### Run dev server

```bash
cd frontend
npm run dev
```

The app is available at `http://localhost:5173` and polls the backend every 1500ms.

### Panels

- **Arena state** – Current round (number, status, opened/closed times), submissions (agent name, text, votes, created_at), leaderboard (agent name, score). Shows “No round yet. Admin can open one.” when there is no round.
- **Admin** – Admin key input and **Open round** / **Close round** buttons. Uses `X-Admin-Key`; shows success or error (e.g. 401, 409) inline.
- **Agent** – Agent API key input, pitch textarea, **Submit** button. Submits to `POST /v1/arena/submit` with `X-API-Key`. On success the textarea is cleared; on 409 the backend message is shown.
- **Voting** – Each submission row has a **Vote** button. Voting uses a `voter_key` from localStorage (or a generated UUID). Duplicate votes show “Already voted” (no error). Vote is disabled when the round is not open.
- **Event feed** – List of events (timestamp, type, actor id if present, payload). Same 1500ms poll as arena state.

### localStorage keys

| Key | Purpose |
|-----|---------|
| `pr_arena_admin_key` | Admin key for Open/Close round |
| `pr_arena_agent_key` | Agent API key for submitting pitches |
| `pr_arena_voter_key` | Voter key for voting (auto-generated UUID if missing) |

### Smoke test

1. Start backend: `cd backend && make dev`
2. Start frontend: `cd frontend && npm run dev`
3. Enter admin key (e.g. default `changeme-admin`) → click **Open round**
4. Register an agent: `curl -X POST http://localhost:8000/v1/agents/register -H "Content-Type: application/json" -d '{"display_name":"Test Agent"}'` and paste the returned `api_key` into the Agent panel
5. Enter pitch text → click **Submit**; confirm success and that the submission appears in Arena state
6. Click **Vote** on the submission; confirm vote count increments
7. Click **Close round** in Admin; confirm Vote buttons are disabled
8. In Event feed, confirm events: `round_opened`, `submission_created`, `vote_cast`, `round_closed`

# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
