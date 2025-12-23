import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Navbar } from '@/components/Navbar';

const queryClient = new QueryClient();

const MockedNavbar = () => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      <Navbar />
    </BrowserRouter>
  </QueryClientProvider>
);

describe('Navbar', () => {
  it('renders brand name', () => {
    render(<MockedNavbar />);
    expect(screen.getByText('RecruitAI')).toBeInTheDocument();
  });
});
