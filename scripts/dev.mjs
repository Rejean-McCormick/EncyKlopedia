import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';
import path from 'node:path';
const require = createRequire(import.meta.url);
const astroRoot = path.dirname(require.resolve('astro/package.json'));
const api = spawn(process.execPath, ['server/index.mjs'], {
  stdio: 'inherit',
  env: { ...process.env, PORT: '4322', KONSTELLATION_DEV_ORIGIN: 'http://localhost:4321' },
});
// Launch Node directly (not an npm wrapper) so termination reaches both servers.
// Keep Astro in the foreground: this process owns both child lifecycles.
const web = spawn(
  process.execPath,
  [path.join(astroRoot, 'bin/astro.mjs'), 'dev', '--host', '127.0.0.1', '--ignore-lock'],
  { stdio: 'inherit' },
);
let stopping = false;
function stop() {
  if (stopping) return;
  stopping = true;
  api.kill('SIGTERM');
  web.kill('SIGTERM');
}
process.on('SIGINT', stop);
process.on('SIGTERM', stop);
for (const child of [api, web]) {
  child.on('error', (error) => {
    console.error(error.message);
    process.exitCode = 1;
    stop();
  });
  child.on('exit', (code) => {
    if (!stopping && code) process.exitCode = code;
    stop();
  });
}
