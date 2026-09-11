import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import React from 'react';
import { ComparePage } from '../pages/ComparePage';
import * as client from '../api/client';
import type { ComparisonResponse, StudentProfile } from '../types';

vi.mock('../api/client');

const mockProfile: StudentProfile = {
  degree_level: 'UNDERGRADUATE',
  gpa: 3.9,
  gpa_scale: 4.0,
  citizenship_country: 'US',
  country_of_residence: 'US',
  us_state: 'NY',
  intended_major: 'Economics',
  sat_total: 1500,
  act_composite: null,
  toefl_total: null,
  ielts_overall: null,
  financial_need_tier: null,
  has_leadership_experience: true,
  has_community_service: true,
  first_generation_college_student: false,
  prepared_components: ['TRANSCRIPT'],
  target_academic_cycle: '2026-2027',
};

const mockComparison: ComparisonResponse = {
  academic_cycle: '2026-2027',
  comparisons: [
    {
      opportunity_id: 'opp-1',
      title: 'Opportunity Alpha',
      provider: 'Foundation A',
      university: 'University A',
      funding_classification: 'FULL_FUNDING',
      verification_status: 'VERIFIED',
      earliest_deadline: '2026-11-01',
      deadline_status: 'UPCOMING',
      eligibility_status: 'ELIGIBLE',
      academic_alignment: 'STRONG',
      geographic_alignment: 'STRONG',
      application_readiness: 'MODERATE',
      primary_source_url: 'https://alpha.org',
    },
    {
      opportunity_id: 'opp-2',
      title: 'Opportunity Beta',
      provider: 'Foundation B',
      university: null,
      funding_classification: 'FULL_TUITION',
      verification_status: 'PARTIALLY_VERIFIED',
      earliest_deadline: '2026-12-01',
      deadline_status: 'UPCOMING',
      eligibility_status: 'NEEDS_INFORMATION',
      academic_alignment: 'MODERATE',
      geographic_alignment: 'UNKNOWN',
      application_readiness: 'LIMITED',
      primary_source_url: 'https://beta.org',
    },
  ],
};

describe('ComparePage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders empty state when no opportunities are selected', () => {
    render(
      <ComparePage
        opportunityIds={[]}
        studentProfile={mockProfile}
        onRemoveFromCompare={vi.fn()}
        onClearAll={vi.fn()}
        onGoToDiscover={vi.fn()}
        onSelectOpportunity={vi.fn()}
      />
    );

    expect(screen.getByText(/No Scholarships Selected for Comparison/i)).toBeInTheDocument();
  });

  it('renders comparison matrix and enforces ethical non-ranking principles', async () => {
    vi.spyOn(client, 'compareOpportunities').mockResolvedValue(mockComparison);

    render(
      <ComparePage
        opportunityIds={['opp-1', 'opp-2']}
        studentProfile={mockProfile}
        onRemoveFromCompare={vi.fn()}
        onClearAll={vi.fn()}
        onGoToDiscover={vi.fn()}
        onSelectOpportunity={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Opportunity Alpha')).toBeInTheDocument();
      expect(screen.getByText('Opportunity Beta')).toBeInTheDocument();
    });

    expect(screen.getByText(/Ethical Comparison Principle/i)).toBeInTheDocument();
    expect(screen.getByText(/We do not compute synthetic composite scores/i)).toBeInTheDocument();

    expect(screen.getByText(/Foundation A/i)).toBeInTheDocument();
    expect(screen.getByText(/Foundation B/i)).toBeInTheDocument();
  });

  it('calls onRemoveFromCompare when remove button is clicked', async () => {
    const handleRemove = vi.fn();
    vi.spyOn(client, 'compareOpportunities').mockResolvedValue(mockComparison);

    render(
      <ComparePage
        opportunityIds={['opp-1', 'opp-2']}
        studentProfile={mockProfile}
        onRemoveFromCompare={handleRemove}
        onClearAll={vi.fn()}
        onGoToDiscover={vi.fn()}
        onSelectOpportunity={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Opportunity Alpha')).toBeInTheDocument();
    });

    const removeBtn = screen.getByRole('button', { name: /Remove Opportunity Alpha/i });
    fireEvent.click(removeBtn);

    expect(handleRemove).toHaveBeenCalledWith('opp-1');
  });
});
