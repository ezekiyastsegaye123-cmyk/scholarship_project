import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { ProfilePage } from '../pages/ProfilePage';
import * as client from '../api/client';
import type { StudentProfile } from '../types';

vi.mock('../api/client');

const initialProfile: StudentProfile = {
  degree_level: 'UNDERGRADUATE',
  gpa: 3.75,
  gpa_scale: 4.0,
  citizenship_country: 'CA',
  country_of_residence: 'CA',
  us_state: null,
  intended_major: 'Biochemistry',
  sat_total: 1400,
  act_composite: null,
  toefl_total: null,
  ielts_overall: 8.0,
  financial_need_tier: 'MODERATE',
  has_leadership_experience: true,
  has_community_service: false,
  first_generation_college_student: true,
  prepared_components: ['TRANSCRIPT'],
  target_academic_cycle: '2026-2027',
};

describe('ProfilePage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders student privacy guarantee banner prominently', () => {
    render(
      <ProfilePage
        profile={initialProfile}
        onSaveProfile={vi.fn()}
        onGoToDiscover={vi.fn()}
      />
    );

    expect(screen.getByText(/Student Privacy Guarantee/i)).toBeInTheDocument();
    expect(screen.getByText(/Social Security Numbers, bank details/i)).toBeInTheDocument();
  });

  it('allows toggling preparation checklist and submitting validated profile', async () => {
    const handleSave = vi.fn();
    vi.spyOn(client, 'submitStudentProfile').mockResolvedValue({
      ...initialProfile,
      prepared_components: ['TRANSCRIPT', 'RECOMMENDATION'],
    });

    render(
      <ProfilePage
        profile={initialProfile}
        onSaveProfile={handleSave}
        onGoToDiscover={vi.fn()}
      />
    );

    const recCheckbox = screen.getByLabelText(/Letters of Recommendation Secured/i);
    expect(recCheckbox).not.toBeChecked();

    fireEvent.click(recCheckbox);
    expect(recCheckbox).toBeChecked();

    const submitBtn = screen.getByRole('button', { name: /Save & Apply Profile/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(handleSave).toHaveBeenCalled();
      expect(screen.getByText(/Profile validated and saved successfully/i)).toBeInTheDocument();
    });
  });
});
