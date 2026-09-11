import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { OpportunityCard } from '../components/OpportunityCard';
import type { OpportunitySummary } from '../types';

const mockOpp: OpportunitySummary = {
  id: 'opp-101',
  title: 'Knight-Hennessy Scholars Program',
  provider_name: 'Stanford University',
  university_name: 'Stanford University',
  degree_level: 'GRADUATE',
  destination_country: 'US',
  academic_cycle: '2026-2027',
  verification_status: 'VERIFIED',
  funding_classification: 'FULL_FUNDING',
  funding_summary: 'Full tuition plus living stipend',
  earliest_deadline: '2026-10-14',
  deadline_type: 'SCHOLARSHIP_APPLICATION',
  deadline_status: 'UPCOMING',
  international_students_allowed: 'YES',
  requires_sat: 'NOT_APPLICABLE',
  requires_act: 'NOT_APPLICABLE',
  financial_need_required: 'NO',
  primary_source_url: 'https://knight-hennessy.stanford.edu',
};

describe('OpportunityCard Component', () => {
  it('renders opportunity title, provider, and verification badge', () => {
    const handleSelect = vi.fn();
    const handleToggleCompare = vi.fn();

    render(
      <OpportunityCard
        opportunity={mockOpp}
        onSelect={handleSelect}
        isCompared={false}
        onToggleCompare={handleToggleCompare}
      />
    );

    expect(screen.getByText('Knight-Hennessy Scholars Program')).toBeInTheDocument();
    expect(screen.getAllByText('Stanford University').length).toBeGreaterThan(0);
    expect(screen.getByText(/Verified Official/i)).toBeInTheDocument();
    expect(screen.getByText(/Full Funding/i)).toBeInTheDocument();
  });

  it('triggers onSelect when title or view details button is clicked', () => {
    const handleSelect = vi.fn();
    const handleToggleCompare = vi.fn();

    render(
      <OpportunityCard
        opportunity={mockOpp}
        onSelect={handleSelect}
        isCompared={false}
        onToggleCompare={handleToggleCompare}
      />
    );

    fireEvent.click(screen.getByText('Knight-Hennessy Scholars Program'));
    expect(handleSelect).toHaveBeenCalledWith('opp-101');

    fireEvent.click(screen.getByText(/View Details & Counselor Evaluation/i));
    expect(handleSelect).toHaveBeenCalledTimes(2);
  });

  it('triggers onToggleCompare when compare button is clicked', () => {
    const handleSelect = vi.fn();
    const handleToggleCompare = vi.fn();

    const { rerender } = render(
      <OpportunityCard
        opportunity={mockOpp}
        onSelect={handleSelect}
        isCompared={false}
        onToggleCompare={handleToggleCompare}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /Add to comparison/i }));
    expect(handleToggleCompare).toHaveBeenCalledWith('opp-101');

    rerender(
      <OpportunityCard
        opportunity={mockOpp}
        onSelect={handleSelect}
        isCompared={true}
        onToggleCompare={handleToggleCompare}
      />
    );

    expect(screen.getByText('Comparing')).toBeInTheDocument();
  });
});
