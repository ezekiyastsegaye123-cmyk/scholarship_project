import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { ApplicationTrackerPage } from '../pages/ApplicationTrackerPage';
import * as client from '../api/client';
import type { ApplicationRecord, OpportunitySummary } from '../types';

vi.mock('../api/client');

describe('ApplicationTrackerPage Component', () => {
  const mockOpportunity: OpportunitySummary = {
    id: 'opp-gates',
    title: 'Gates Cambridge Scholarship',
    slug: 'gates-cambridge-scholarship',
    provider_name: 'Bill & Melinda Gates Foundation',
    university_name: 'University of Cambridge',
    degree_level: 'POSTGRADUATE',
    destination_country: 'GB',
    academic_cycle: '2026-2027',
    verification_status: 'VERIFIED',
    funding_classification: 'FULL_FUNDING',
    funding_summary: 'Full cost of study plus maintenance',
    earliest_deadline: '2026-12-05',
    deadline_type: 'SCHOLARSHIP_APPLICATION',
    deadline_status: 'UPCOMING',
    international_students_allowed: 'YES',
    requires_sat: 'NOT_APPLICABLE',
    requires_act: 'NOT_APPLICABLE',
    financial_need_required: 'NO',
    primary_source_url: 'https://www.gatescambridge.org',
    freshness_level: 'FRESH',
    freshness_message: 'Verified',
    last_crawled_at: '2026-09-10T12:00:00Z',
  };

  const mockApp: ApplicationRecord = {
    id: 'app-1',
    opportunity_id: 'opp-gates',
    status: 'IN_PROGRESS',
    student_notes: 'Drafted research proposal, awaiting second reference letter.',
    target_academic_cycle: '2026-2027',
    planned_submission_date: '2026-11-20',
    actual_submission_date: null,
    created_at: '2026-09-11T10:00:00Z',
    updated_at: '2026-09-11T12:00:00Z',
    opportunity: mockOpportunity,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders application records with student notes clearly distinguished from official facts', async () => {
    vi.spyOn(client, 'fetchApplications').mockResolvedValue({
      items: [mockApp],
      total: 1,
      page: 1,
      page_size: 20,
      pages: 1,
    });

    render(
      <ApplicationTrackerPage
        onSelectOpportunity={vi.fn()}
        onGoToDiscover={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Gates Cambridge Scholarship')).toBeInTheDocument();
      expect(screen.getAllByText('In Progress').length).toBeGreaterThanOrEqual(1);
      // Section 23 requirement: student notes clearly labeled
      expect(screen.getByText(/Student-provided note/i)).toBeInTheDocument();
      expect(screen.getByText(/Never treated as official evidence/i)).toBeInTheDocument();
      expect(screen.getByText(/Drafted research proposal/i)).toBeInTheDocument();
    });
  });

  it('allows editing an application status and note', async () => {
    vi.spyOn(client, 'fetchApplications').mockResolvedValue({
      items: [mockApp],
      total: 1,
      page: 1,
      page_size: 20,
      pages: 1,
    });
    vi.spyOn(client, 'updateApplication').mockResolvedValue({
      ...mockApp,
      status: 'SUBMITTED',
      student_notes: 'Submitted online via portal on Nov 19.',
      actual_submission_date: '2026-11-19',
    });

    render(
      <ApplicationTrackerPage
        onSelectOpportunity={vi.fn()}
        onGoToDiscover={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Gates Cambridge Scholarship')).toBeInTheDocument();
    });

    // Click edit
    const editBtn = screen.getByRole('button', { name: /Edit Tracking/i });
    fireEvent.click(editBtn);

    // Change status
    const statusSelect = screen.getByDisplayValue('In Progress');
    fireEvent.change(statusSelect, { target: { value: 'SUBMITTED' } });

    // Save changes
    const saveBtn = screen.getByRole('button', { name: /Save Changes/i });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(client.updateApplication).toHaveBeenCalled();
    });
  });

  it('deletes an application record after confirmation', async () => {
    vi.spyOn(client, 'fetchApplications').mockResolvedValue({
      items: [mockApp],
      total: 1,
      page: 1,
      page_size: 20,
      pages: 1,
    });
    vi.spyOn(client, 'deleteApplication').mockResolvedValue({
      message: 'Deleted successfully',
      application_id: 'app-1',
    });
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(
      <ApplicationTrackerPage
        onSelectOpportunity={vi.fn()}
        onGoToDiscover={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Gates Cambridge Scholarship')).toBeInTheDocument();
    });

    const deleteBtn = screen.getByLabelText(/Delete application for Gates Cambridge Scholarship/i);
    fireEvent.click(deleteBtn);

    await waitFor(() => {
      expect(client.deleteApplication).toHaveBeenCalledWith('app-1');
      expect(screen.queryByText('Gates Cambridge Scholarship')).not.toBeInTheDocument();
    });
  });
});
