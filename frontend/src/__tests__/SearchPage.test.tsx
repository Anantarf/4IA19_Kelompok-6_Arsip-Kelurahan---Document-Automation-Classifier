import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import SearchPage from '../pages/SearchPage';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const qc = new QueryClient();

test('renders search page inputs', () => {
  render(
    <MemoryRouter>
      <QueryClientProvider client={qc}>
        <SearchPage />
      </QueryClientProvider>
    </MemoryRouter>,
  );

  expect(screen.getByPlaceholderText('Cari dokumen...')).toBeInTheDocument();
});
