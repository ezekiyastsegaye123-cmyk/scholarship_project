import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import React from 'react';
import { DiscoverPage } from '../pages/DiscoverPage';
import * as client from '../api/client';
import type { PaginatedOpportunities } from '../types';

vi.mock('../api/client');

const mockPaginated: PaginatedOpportunities = {
  items: [
    {
      id: 'opp-1',
      title: 'Rhodes Scholarship',
      provider_name: 'Rhodes Trust',
      university_name: 'University of Oxford',
      degree_level: 'GRADUATE',
      destination_country: 'GB',
      academic_cycle: '2026-2027',
      verification_status: 'VERIFIED',
      funding_classification: 'FULL_FUNDING',
      funding_summary: 'Full tuition and living stipend',
      earliest_deadline: '2026-10-01',
      deadline_type: 'SCHOLARSHIP_APPLICATION',
      deadline_status: 'UPCOMING',
      international_students_allowed: 'YES',
      requires_sat: 'NO',
      requires_act: 'NO',
      financial_need_required: 'NO',
      primary_source_url: 'https://rhodeshouse.ox.ac.uk',
    },
  ],
  total: 1,
  page: 1,
  page_size: 9,
  pages: 1,
};

describe('DiscoverPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders search bar, filters, and loaded cards', async () => {
    vi.spyOn(client, 'fetchOpportunities').mockResolvedValue(mockPaginated);

    render(
      <DiscoverPage
        onSelectOpportunity={vi.fn()}
        comparedIds={[]}
        onToggleCompare={vi.fn()}
        onGoToCompare={vi.fn()}
      />
    );

    expect(screen.getByPlaceholderText(/Search scholarships by title/i)).toBeInTheDocument();
    expect(screen.getByText(/Loading Opportunities.../i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Rhodes Scholarship')).toBeInTheDocument();
    });

    expect(screen.getByText(/Showing/i)).toBeInTheDocument();
    expect(screen.getByText(/University of Oxford/i)).toBeInTheDocument();
  });

  it('displays empty state when no items return', async () => {
    vi.spyOn(client, 'fetchOpportunities').mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 9,
      pages: 0,
    });

    render(
      <DiscoverPage
        onSelectOpportunity={vi.fn()}
        comparedIds={[]}
        onToggleCompare={vi.fn()}
        onGoToCompare={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/No Matching Opportunities/i)).toBeInTheDocument();
    });
  });

  it('displays network error state when API fails', async () => {
    vi.spyOn(client, 'fetchOpportunities').mockRejectedValue(new Error('Backend connection refused'));

    render(
      <DiscoverPage
        onSelectOpportunity={vi.fn()}
        comparedIds={[]}
        onToggleCompare={vi.fn()}
        onGoToCompare={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Unable to Load Opportunities/i)).toBeInTheDocument();
      expect(screen.getByText(/Backend connection refused/i)).toBeInTheDocument();
    });
  });
});
