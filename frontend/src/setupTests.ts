import React from 'react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock axios globally to prevent real HTTP calls during tests
vi.mock('axios', () => {
  const get = vi.fn().mockResolvedValue({ data: [], headers: {} });
  const post = vi.fn().mockResolvedValue({ data: {} });
  const patch = vi.fn().mockResolvedValue({ data: {} });
  const instance: any = {
    get,
    post,
    patch,
    create: () => instance,
    defaults: { headers: {} },
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  };
  return {
    default: instance,
    create: () => instance,
    get,
    post,
    patch,
  };
});

// Stub react-pdf to avoid async state updates and act warnings in tests
vi.mock('react-pdf', () => {
  return {
    pdfjs: { GlobalWorkerOptions: { workerSrc: '' } },
    Document: ({ children }: any) =>
      React.createElement('div', { 'data-testid': 'mock-document' }, children),
    Page: ({ pageNumber }: any) =>
      React.createElement('div', { 'data-testid': `mock-page-${pageNumber ?? '0'}` }),
  };
});
