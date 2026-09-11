import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { AICounselorPanel } from '../components/AICounselorPanel';
import * as client from '../api/client';
import type { AICounselorResponse } from '../types';

vi.mock('../api/client');

describe('AICounselorPanel Component', () => {
  const mockOpportunityId = 'opp-xyz-456';
  const mockOpportunityTitle = 'Gates Millennium Fellowship';

  const mockSuccessResponse: AICounselorResponse = {
    answer: 'You satisfy the GPA criteria of 3.8 minimum with your Canadian degree.',
    epistemic_status: 'GROUNDED',
    warnings: [],
    sources: [
      {
        title: 'Gates Foundation Official Eligibility Guidelines',
        url: 'https://example.org/guidelines',
        authority_tier: 'OFFICIAL_PROVIDER',
        verification_status: 'VERIFIED',
        evidence_quote: 'Minimum 3.8 GPA required for undergraduate awards.',
        is_primary: true,
      },
    ],
    known_facts: ['GPA 3.8 minimum requirement satisfied.'],
    unknowns: [],
    next_steps: ['Submit official transcript before deadline.'],
    disclaimer: 'AI guidance explains verified scholarship facts.',
    is_fallback: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders counselor panel header, disclaimer, and suggested question chips', () => {
    render(
      <AICounselorPanel
        opportunityId={mockOpportunityId}
        opportunityTitle={mockOpportunityTitle}
        isAuthenticated={true}
      />
    );

    expect(screen.getByText(/AI Scholarship Counselor/i)).toBeInTheDocument();
    expect(screen.getByText(/Suggested Questions for Gates Millennium Fellowship/i)).toBeInTheDocument();
    expect(screen.getByText(/Why am I eligible for this scholarship\?/i)).toBeInTheDocument();
    expect(screen.getByText(/Does this cover living expenses/i)).toBeInTheDocument();
  });

  it('triggers onOpenAuthModal when unauthenticated user attempts to ask question', () => {
    const onOpenAuthModal = vi.fn();
    render(
      <AICounselorPanel
        opportunityId={mockOpportunityId}
        opportunityTitle={mockOpportunityTitle}
        isAuthenticated={false}
        onOpenAuthModal={onOpenAuthModal}
      />
    );

    expect(screen.getByText(/Sign in with your student account/i)).toBeInTheDocument();
    const signInBtn = screen.getByRole('button', { name: /^Sign In$/i });
    fireEvent.click(signInBtn);
    expect(onOpenAuthModal).toHaveBeenCalledTimes(1);
  });

  it('sends question via askAICounselor and renders grounded response and sources', async () => {
    vi.spyOn(client, 'askAICounselor').mockResolvedValueOnce(mockSuccessResponse);

    render(
      <AICounselorPanel
        opportunityId={mockOpportunityId}
        opportunityTitle={mockOpportunityTitle}
        isAuthenticated={true}
      />
    );

    const promptBtn = screen.getByText(/Why am I eligible for this scholarship\?/i);
    fireEvent.click(promptBtn);

    await waitFor(() => {
      expect(client.askAICounselor).toHaveBeenCalledWith(
        mockOpportunityId,
        'Why am I eligible for this scholarship?',
        []
      );
    });

    await waitFor(() => {
      expect(screen.getByText(/You satisfy the GPA criteria/i)).toBeInTheDocument();
      expect(screen.getByText(/Fully Grounded in Official Facts/i)).toBeInTheDocument();
      expect(screen.getByText(/Gates Foundation Official Eligibility Guidelines/i)).toBeInTheDocument();
      expect(screen.getByText(/Minimum 3.8 GPA required for undergraduate awards./i)).toBeInTheDocument();
    });
  });

  it('handles rate limit error (429) gracefully with clear user warning', async () => {
    vi.spyOn(client, 'askAICounselor').mockRejectedValueOnce({ status: 429, message: 'Rate limit exceeded' });

    render(
      <AICounselorPanel
        opportunityId={mockOpportunityId}
        opportunityTitle={mockOpportunityTitle}
        isAuthenticated={true}
      />
    );

    const promptBtn = screen.getByText(/Why am I eligible for this scholarship\?/i);
    fireEvent.click(promptBtn);

    await waitFor(() => {
      expect(screen.getByText(/Rate limit reached: Please wait a moment/i)).toBeInTheDocument();
    });
  });

  it('renders fallback engine badge when response is marked as fallback', async () => {
    const fallbackResponse: AICounselorResponse = {
      ...mockSuccessResponse,
      is_fallback: true,
    };
    vi.spyOn(client, 'askAICounselor').mockResolvedValueOnce(fallbackResponse);

    render(
      <AICounselorPanel
        opportunityId={mockOpportunityId}
        opportunityTitle={mockOpportunityTitle}
        isAuthenticated={true}
      />
    );

    const promptBtn = screen.getByText(/Why am I eligible for this scholarship\?/i);
    fireEvent.click(promptBtn);

    await waitFor(() => {
      expect(screen.getByText(/Fallback Engine/i)).toBeInTheDocument();
    });
  });
});
