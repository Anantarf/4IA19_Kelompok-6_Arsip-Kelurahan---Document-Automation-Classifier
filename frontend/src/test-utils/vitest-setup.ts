// Vitest setup: mock or stub global behaviors used by tests
// ensure that canvas import resolves to our stub
import './canvas-stub';

// JSDOM doesn't implement URL.createObjectURL; stub it for tests that use blobs
if (typeof (globalThis as any).URL?.createObjectURL !== 'function') {
  (globalThis as any).URL = {
    ...(globalThis as any).URL,
    createObjectURL: () => 'blob:mock',
    revokeObjectURL: () => {},
  };
}

// Removed require patch and uncaughtException suppression — happy-dom avoids loading the native canvas module.
// If future tests need a canvas stub, it can be imported explicitly in those tests.

// Optionally add helpers for DOM or global mocks here
// e.g., polyfill global.fetch if needed
