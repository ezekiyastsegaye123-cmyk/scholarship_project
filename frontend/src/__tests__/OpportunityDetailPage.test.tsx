import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import React from 'react';
import { OpportunityDetailPage } from '../pages/OpportunityDetailPage';
import * as client from '../api/client';
import type { OpportunityDetail, StudentProfile, EligibilityEvaluationResult, CounselorAssessmentResult } from '../types';

vi.mock('../api/client');

const mockStudent: StudentProfile = {
  degree_level: 'UNDERGRADUATE',
  gpa: 3.9,
  gpa_scale: 4.0,
  citizenship_country: 'US',
  country_of_residence: 'US',
  us_state: 'CA',
  intended_major: 'Physics',
  sat_total: 1520,
  act_composite: null,
  toefl_total: null,
  ielts_overall: null,
  financial_need_tier: 'LOW',
  has_leadership_experience: true,
  has_community_service: true,
  first_generation_college_student: false,
  prepared_components: ['TRANSCRIPT', 'RECOMMENDATION', 'ESSAY'],
  target_academic_cycle: '2026-2027',
};

const mockDetail: OpportunityDetail = {
  id: 'opp-202',
  title: 'Robertson Scholars Leadership Program',
  provider_name: 'Robertson Scholars Program',
  university_name: 'Duke University',
  target_degree_level: 'UNDERGRADUATE',
  destination_country: 'US',
  academic_cycle: '2026-2027',
  verification_status: 'VERIFIED',
  funding_classification: 'FULL_FUNDING',
  funding_summary: 'Full tuition, room, board, and mandatory fees',
  earliest_deadline: '2026-11-15',
  deadline_type: 'SCHOLARSHIP_APPLICATION',
  deadline_status: 'UPCOMING',
  international_students_allowed: 'YES',
  requires_sat: 'NOT_APPLICABLE',
  requires_act: 'NOT_APPLICABLE',
  financial_need_required: 'NO',
  primary_source_url: 'https://robertsonscholars.org',
  description: 'Comprehensive undergraduate leadership scholarship at Duke and UNC-Chapel Hill.',
  varies_by_program: false,
  requires_css_profile: 'NO',
  fingerprint_sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
  award_details: {
    id: 'aw-1',
    funding_classification: 'FULL_FUNDING',
    title: 'Robertson Full Award',
    is_renewable: 'YES',
    renewal_criteria: 'Maintain 3.3 GPA',
    estimated_annual_value_usd: 85000,
    components: [
      {
        id: 'fc-1',
        component_type: 'TUITION',
        amount_min: 65000,
        amount_max: 65000,
        currency: 'USD',
        amount_period: 'ANNUAL',
        percentage_tuition: 100,
        description: 'Full tuition covered',
        source_evidence_snippet: 'Covers full tuition at Duke or UNC',
      },
    ],
  },
  deadlines: [
    {
      id: 'dl-1',
      deadline_date: '2026-11-15',
      deadline_type: 'SCHOLARSHIP_APPLICATION',
      is_exact_date: true,
      timezone: 'America/New_York',
      academic_cycle: '2026-2027',
      varies_by_program: false,
      context_description: 'Final application deadline',
      source_evidence_snippet: 'Application deadline is November 15, 2026',
    },
  ],
  eligibility_rules: [
    {
      id: 'er-1',
      rule_id: 'RULE_CITIZENSHIP',
      kind: 'REQUIRED',
      expression_json: { field: 'citizenship_country', op: 'in', value: ['US', 'INTL'] },
      description: 'Open to US and International applicants',
      source_evidence_snippet: 'All students eligible regardless of nationality',
      is_verified: true,
    },
  ],
  requirements: [],
  application_requirements: [
    {
      id: 'ar-1',
      requirement_type: 'ESSAY',
      kind: 'REQUIRED',
      title: 'Leadership Essay',
      description: '500-word essay on collaborative leadership',
      instructions: 'Submit via application portal',
      submission_format: 'PDF',
      source_evidence_snippet: 'Two short essays required',
    },
  ],
  official_sources: [
    {
      id: 'os-1',
      url: 'https://robertsonscholars.org',
      source_domain: 'robertsonscholars.org',
      authority_tier: 'OFFICIAL_PROVIDER',
      is_primary: true,
      page_title: 'Robertson Scholars Home',
      extracted_text_snippet: 'Official program overview',
      last_crawled_at: '2026-09-01T12:00:00Z',
      last_http_status: 200,
    },
  ],
  discovery_sources: [],
  verification_records: [
    {
      id: 'vr-1',
      verification_state: 'VERIFIED',
      verifier_identity: 'Institutional Auditor',
      verification_method: 'MANUAL_OFFICIAL_CONFIRMATION',
      evidence_url: 'https://robertsonscholars.org',
      evidence_quote: 'Verified against published policies',
      notes: 'Confirmed for 2026-2027 cycle',
      verified_at: '2026-09-01T12:00:00Z',
    },
  ],
  conflict_records: [],
};

const mockEvalResult: EligibilityEvaluationResult = {
  opportunity_id: 'opp-202',
  verification_status: 'VERIFIED',
  is_gated: false,
  status: 'ELIGIBLE',
  rule_results: [
    {
      rule_id: 'RULE_CITIZENSHIP',
      rule_kind: 'REQUIRED',
      satisfied: true,
      status: 'SATISFIED',
      field_name: 'citizenship_country',
      comparison_operator: 'in',
      expected_value: ['US', 'INTL'],
      actual_value: 'US',
      is_verified: true,
      explanation: 'Applicant is a US citizen.',
      evidence_snippet: 'All students eligible regardless of nationality',
    },
  ],
  explanation: 'All required criteria are satisfied.',
  evaluation_contains_unverified_facts: false,
  evaluated_at: '2026-11-01T00:00:00Z',
};

const mockCounselResult: CounselorAssessmentResult = {
  opportunity_id: 'opp-202',
  academic_cycle: '2026-2027',
  academic_alignment: 'STRONG',
  geographic_alignment: 'STRONG',
  funding_understanding: 'STRONG',
  deadline_assessment: {
    status: 'UPCOMING',
    earliest_deadline: '2026-11-15',
    is_urgent: false,
    explanation: 'Application deadline is in 14 days.',
  },
  application_readiness: 'MODERATE',
  strengths: ['Academic GPA exceeds requirements', 'Citizenship is explicitly accepted'],
  gaps: [],
  uncertainties: [],
  recommended_actions: ['Submit leadership essay draft for review'],
  evaluated_at: '2026-11-01T00:00:00Z',
};

describe('OpportunityDetailPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders opportunity detail overview and primary official link', async () => {
    vi.spyOn(client, 'fetchOpportunityDetail').mockResolvedValue(mockDetail);

    render(
      <OpportunityDetailPage
        opportunityId="opp-202"
        onBack={vi.fn()}
        studentProfile={mockStudent}
        isCompared={false}
        onToggleCompare={vi.fn()}
        onGoToProfile={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Robertson Scholars Leadership Program')).toBeInTheDocument();
    });

    expect(screen.getByText(/Duke University/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /View Official Source/i })).toHaveAttribute(
      'href',
      'https://robertsonscholars.org'
    );
  });

  it('runs eligibility evaluation and renders rule breakdown', async () => {
    vi.spyOn(client, 'fetchOpportunityDetail').mockResolvedValue(mockDetail);
    vi.spyOn(client, 'evaluateOpportunity').mockResolvedValue(mockEvalResult);

    render(
      <OpportunityDetailPage
        opportunityId="opp-202"
        onBack={vi.fn()}
        studentProfile={mockStudent}
        isCompared={false}
        onToggleCompare={vi.fn()}
        onGoToProfile={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Robertson Scholars Leadership Program')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Check Eligibility/i }));

    await waitFor(() => {
      expect(screen.getByText(/All required criteria are satisfied/i)).toBeInTheDocument();
      expect(screen.getByText('RULE_CITIZENSHIP')).toBeInTheDocument();
      expect(screen.getAllByText(/Satisfied/i).length).toBeGreaterThan(0);
    });
  });

  it('renders funding tab and emphasizes Full Tuition != Full Funding principle', async () => {
    vi.spyOn(client, 'fetchOpportunityDetail').mockResolvedValue(mockDetail);

    render(
      <OpportunityDetailPage
        opportunityId="opp-202"
        onBack={vi.fn()}
        studentProfile={mockStudent}
        isCompared={false}
        onToggleCompare={vi.fn()}
        onGoToProfile={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Robertson Scholars Leadership Program')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('tab', { name: /Funding Breakdown/i }));

    expect(screen.getByText(/Full Tuition is NOT Full Funding/i)).toBeInTheDocument();
    expect(screen.getByText(/Full tuition covered/i)).toBeInTheDocument();
  });

  it('runs counselor assessment and displays qualitative quadrant', async () => {
    vi.spyOn(client, 'fetchOpportunityDetail').mockResolvedValue(mockDetail);
    vi.spyOn(client, 'counselOpportunity').mockResolvedValue(mockCounselResult);

    render(
      <OpportunityDetailPage
        opportunityId="opp-202"
        onBack={vi.fn()}
        studentProfile={mockStudent}
        isCompared={false}
        onToggleCompare={vi.fn()}
        onGoToProfile={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Robertson Scholars Leadership Program')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Counselor Assessment/i }));

    await waitFor(() => {
      expect(screen.getByText(/Strengths/i)).toBeInTheDocument();
      expect(screen.getByText('Academic GPA exceeds requirements')).toBeInTheDocument();
      expect(screen.getByText('Submit leadership essay draft for review')).toBeInTheDocument();
    });
  });
});
