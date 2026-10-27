import { spawn } from 'node:child_process';
const child = spawn(process.execPath, ['scripts/dev.mjs'], { stdio: ['ignore', 'pipe', 'pipe'] });
let logs = '';
child.stdout.on('data', (b) => (logs += b));
child.stderr.on('data', (b) => (logs += b));
const exited = new Promise((resolve) => child.on('exit', resolve));
try {
  let boot;
  for (let i = 0; i < 60; i++) {
    try {
      const response = await fetch('http://127.0.0.1:4321/api/bootstrap');
      if (response.ok) {
        boot = await response.json();
        break;
      }
    } catch {
      /* Startup can take a moment. */
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  if (!boot) throw new Error(logs);
  const query = {
    schemaVersion: '0.2',
    context: boot.context,
    selection: { entityType: 'human', filters: [], links: [] },
    order: 'entity_id_asc',
    pageSize: 24,
  };
  const response = await fetch('http://127.0.0.1:4321/api/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Origin: 'http://127.0.0.1:4321' },
    body: JSON.stringify({ query }),
  });
  const data = await response.json();
  if (response.status !== 200 || data.total.value !== 132) throw new Error(JSON.stringify(data));
  if (!(await fetch('http://127.0.0.1:4321/')).ok) throw new Error('Frontend unavailable');
  console.log('PASS: development frontend and proxied POST; 132 matches.');
} finally {
  child.kill('SIGTERM');
  const timer = setTimeout(() => {
    child.kill('SIGKILL');
    process.exitCode = 1;
    console.error('Development server failed to stop');
  }, 5000);
  await exited;
  clearTimeout(timer);
}
