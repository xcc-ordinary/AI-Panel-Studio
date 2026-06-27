/**
 * Global setup: ensure seed database exists.
 *
 * The seed script is idempotent. If the DB already has data, it's a no-op.
 * This just ensures the backend finds known test discussions on startup.
 */
import { execSync } from 'node:child_process';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const BACKEND_DIR = path.resolve(__dirname, '..', '..', '..', 'backend');

async function globalSetup() {
  const dataDir = path.join(BACKEND_DIR, 'data');
  fs.mkdirSync(dataDir, { recursive: true });

  console.log('[global-setup] Running seed script...');
  try {
    execSync(
      `.venv\\Scripts\\python -m scripts.seed`,
      { cwd: BACKEND_DIR, stdio: 'pipe', timeout: 30_000 },
    );
    console.log('[global-setup] Seed completed.');
  } catch (err) {
    console.warn('[global-setup] Seed warning (may already be seeded):', String(err).slice(0, 200));
  }
}

export default globalSetup;
