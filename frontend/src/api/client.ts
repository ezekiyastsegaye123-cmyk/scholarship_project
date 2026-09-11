import type {
  OpportunityDetail,
  PaginatedOpportunities,
  StudentProfile,
  EligibilityEvaluationResult,
  CounselorAssessmentResult,
  ComparisonResponse,
} from '../types';

const API_BASE = '/api';

export interface OpportunityFilterParams {
  search?: string;
  degree_level?: string;
  international_allowed?: boolean;
  funding_classification?: string;
  verification_status?: string;
  deadline_status?: string;
  page?: number;
  page_size?: number;
}

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      let errBody: any = null;
      try {
        errBody = await response.json();
      } catch {
        errBody = await response.text();
      }
      throw new ApiError(
        (errBody && errBody.detail) || `API request failed with HTTP ${response.status}`,
        response.status,
        errBody
      );
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(
      error instanceof Error ? error.message : 'Network error occurred while connecting to the scholarship service',
      0,
      null
    );
  }
}

export async function fetchOpportunities(params: OpportunityFilterParams = {}): Promise<PaginatedOpportunities> {
  const query = new URLSearchParams();
  if (params.search) query.set('search', params.search);
  if (params.degree_level) query.set('degree_level', params.degree_level);
  if (params.international_allowed !== undefined) {
    query.set('international_allowed', String(params.international_allowed));
  }
  if (params.funding_classification) {
    query.set('funding_classification', params.funding_classification);
  }
  if (params.verification_status) {
    query.set('verification_status', params.verification_status);
  }
  if (params.deadline_status) {
    query.set('deadline_status', params.deadline_status);
  }
  if (params.page) query.set('page', String(params.page));
  if (params.page_size) query.set('page_size', String(params.page_size));

  const qs = query.toString();
  return request<PaginatedOpportunities>(`/opportunities${qs ? `?${qs}` : ''}`);
}

export async function fetchOpportunityDetail(id: string): Promise<OpportunityDetail> {
  return request<OpportunityDetail>(`/opportunities/${encodeURIComponent(id)}`);
}

export async function submitStudentProfile(profile: StudentProfile): Promise<StudentProfile> {
  return request<StudentProfile>('/student-profile', {
    method: 'POST',
    body: JSON.stringify(profile),
  });
}

export async function evaluateOpportunity(
  id: string,
  profile: StudentProfile,
  allowPartiallyVerified: boolean = false
): Promise<EligibilityEvaluationResult> {
  return request<EligibilityEvaluationResult>(`/opportunities/${encodeURIComponent(id)}/evaluate`, {
    method: 'POST',
    body: JSON.stringify({
      student_profile: profile,
      allow_partially_verified: allowPartiallyVerified,
      target_academic_cycle: profile.target_academic_cycle || '2026-2027',
    }),
  });
}

export async function counselOpportunity(
  id: string,
  profile: StudentProfile,
  referenceDate: string = '2026-11-01'
): Promise<CounselorAssessmentResult> {
  return request<CounselorAssessmentResult>(`/opportunities/${encodeURIComponent(id)}/counsel`, {
    method: 'POST',
    body: JSON.stringify({
      student_profile: profile,
      reference_date: referenceDate,
      target_academic_cycle: profile.target_academic_cycle || '2026-2027',
    }),
  });
}

export async function compareOpportunities(
  opportunityIds: string[],
  profile?: StudentProfile | null
): Promise<ComparisonResponse> {
  return request<ComparisonResponse>('/compare', {
    method: 'POST',
    body: JSON.stringify({
      opportunity_ids: opportunityIds,
      student_profile: profile || null,
      target_academic_cycle: profile?.target_academic_cycle || '2026-2027',
    }),
  });
}
