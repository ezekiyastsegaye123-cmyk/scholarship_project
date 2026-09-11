import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { SavedOpportunitiesPage } from '../pages/SavedOpportunitiesPage';
import * as client from '../api/client';
import type { SavedOpportunity, OpportunitySummary } from '../types';

vi.mock('../api/client');

describe('SavedOpportunitiesPage Component', () => {
  const mockOpportunity: OpportunitySummary = {
    id: 'opp-1',
    title: 'Rhodes Trust Scholarship',
    slug: 'rhodes-trust-scholarship',
    provider_name: 'Rhodes Trust',
    university_name: 'University of Oxford',
    degree_level: 'POSTGRADUATE',
    destination_country: 'GB',
    academic_cycle: '2026-2027',
    verification_status: 'VERIFIED',
    funding_classification: 'FULL_FUNDING',
    funding_summary: 'Full tuition and living stipend',
    earliest_deadline: '2026-10-01',
    deadline_type: 'SCHOLARSHIP_APPLICATION',
    deadline_status: 'UPCOMING',
    international_students_allowed: 'YES',
    requires_sat: 'NOT_APPLICABLE',
    requires_act: 'NOT_APPLICABLE',
    financial_need_required: 'NO',
    primary_source_url: 'https://www.rhodeshouse.ox.ac.uk',
    freshness_level: 'FRESH',
    freshness_message: 'Verified within last 14 days',
    last_crawled_at: '2026-09-10T12:00:00Z',
  };

  const mockSavedItem: SavedOpportunity = {
    id: 'saved-1',
    opportunity_id: 'opp-1',
    created_at: '2026-09-11T10:00:00Z',
    opportunity: mockOpportunity,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders empty state when no scholarships are saved', async () => {
    vi.spyOn(client, 'fetchSavedOpportunities').mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      pages: 1,
    });

    render(
      <SavedOpportunitiesPage
        onSelectOpportunity={vi.fn()}
        onGoToDiscover={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/No saved scholarships yet/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Explore Verified Scholarships/i })).toBeInTheDocument();
    });
  });

  it('renders list of saved scholarships with canonical facts and verification badges', async () => {
    vi.spyOn(client, 'fetchSavedOpportunities').mockResolvedValue({
      items: [mockSavedItem],
      total: 1,
      page: 1,
      page_size: 20,
      pages: 1,
    });

    render(
      <SavedOpportunitiesPage
        onSelectOpportunity={vi.fn()}
        onGoToDiscover={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Rhodes Trust Scholarship')).toBeInTheDocument();
      expect(screen.getByText('University of Oxford')).toBeInTheDocument();
      expect(screen.getByText(/Full Funding/i)).toBeInTheDocument();
    });
  });

  it('handles unsave action and removes scholarship from list', async () => {
    vi.spyOn(client, 'fetchSavedOpportunities').mockResolvedValue({
      items: [mockSavedItem],
      total: 1,
      page: 1,
      page_size: 20,
      pages: 1,
    });
    vi.spyOn(client, 'unsaveOpportunity').mockResolvedValue({
      message: 'Unsaved successfully',
      opportunity_id: 'opp-1',
    });

    render(
      <SavedOpportunitiesPage
        onSelectOpportunity={vi.fn()}
        onGoToDiscover={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Rhodes Trust Scholarship')).toBeInTheDocument();
    });

    const unsaveBtn = screen.getByLabelText(/Unsave Rhodes Trust Scholarship/i);
    fireEvent.click(unsaveBtn);

    await waitFor(() => {
      expect(client.unsaveOpportunity).toHaveBeenCalledWith('opp-1');
      expect(screen.queryByText('Rhodes Trust Scholarship')).not.toBeInTheDocument();
    });
  });

  it('calls onSelectOpportunity when View Details is clicked', async () => {
    const onSelect = vi.fn();
    vi.spyOn(client, 'fetchSavedOpportunities').mockResolvedValue({
      items: [mockSavedItem],
      total: 1,
      page: 1,
      page_size: 20,
      pages: 1,
    });

    render(
      <SavedOpportunitiesPage
        onSelectOpportunity={onSelect}
        onGoToDiscover={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Rhodes Trust Scholarship')).toBeInTheDocument();
    });

    const detailsBtn = screen.getByRole('button', { name: /View Details/i });
    fireEvent.click(detailsBtn);

    expect(onSelect).toHaveBeenCalledWith('opp-1');
  });
});
