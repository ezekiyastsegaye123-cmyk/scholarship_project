import type {
  OpportunityDetail,
  PaginatedOpportunities,
  StudentProfile,
  EligibilityEvaluationResult,
  CounselorAssessmentResult,
  ComparisonResponse,
  StudentAccount,
  AuthResponse,
  SavedOpportunity,
  PaginatedSavedOpportunities,
  ApplicationRecord,
  PaginatedApplications,
  ApplicationStatus,
  PersistentComparisonResponse,
  PersistentProfile,
} from '../types';

const API_BASE = '/api';

let authToken: string | null = typeof window !== 'undefined' ? localStorage.getItem('scholarship_auth_token') : null;

export function setAuthToken(token: string | null): void {
  authToken = token;
  if (typeof window !== 'undefined') {
    if (token) {
      localStorage.setItem('scholarship_auth_token', token);
    } else {
      localStorage.removeItem('scholarship_auth_token');
    }
  }
}

export function getAuthToken(): string | null {
  return authToken;
}

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
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options?.headers as Record<string, string>) || {}),
    };

    if (authToken && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${authToken}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      if (response.status === 401) {
        setAuthToken(null);
      }

      let errBody: any = null;
      try {
        errBody = await response.json();
      } catch {
        errBody = await response.text();
      }

      let userMessage = 'An unexpected error occurred while communicating with the service.';
      if (errBody && errBody.detail) {
        userMessage = typeof errBody.detail === 'string' ? errBody.detail : JSON.stringify(errBody.detail);
      } else if (response.status === 401) {
        userMessage = 'Authentication required. Please sign in to access your saved scholarships and applications.';
      } else if (response.status === 403) {
        userMessage = 'You do not have authorization to perform this operation.';
      } else if (response.status === 404) {
        userMessage = 'The requested resource could not be found.';
      } else if (response.status === 409) {
        userMessage = 'A conflicting record already exists.';
      } else if (response.status === 422) {
        userMessage = 'The submitted data is invalid. Please review required fields.';
      } else if (response.status >= 500) {
        userMessage = 'A server error occurred. Please try again shortly.';
      }

      throw new ApiError(userMessage, response.status, errBody);
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

// -----------------------------------------------------------------------------
// AUTHENTICATION
// -----------------------------------------------------------------------------

export async function authRegister(email: string, password: string): Promise<AuthResponse> {
  const data = await request<AuthResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  setAuthToken(data.token);
  return data;
}

export async function authLogin(email: string, password: string): Promise<AuthResponse> {
  const data = await request<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  setAuthToken(data.token);
  return data;
}

export async function authLogout(): Promise<{ message: string }> {
  try {
    const res = await request<{ message: string }>('/auth/logout', {
      method: 'POST',
    });
    setAuthToken(null);
    return res;
  } catch (err) {
    setAuthToken(null);
    return { message: 'Logged out successfully' };
  }
}

export async function authMe(): Promise<StudentAccount> {
  return request<StudentAccount>('/auth/me');
}

// -----------------------------------------------------------------------------
// PERSISTENT STUDENT PROFILE
// -----------------------------------------------------------------------------

export async function fetchPersistentProfile(): Promise<PersistentProfile> {
  return request<PersistentProfile>('/student-profile');
}

export async function updatePersistentProfile(profile: Partial<PersistentProfile>): Promise<PersistentProfile> {
  return request<PersistentProfile>('/student-profile', {
    method: 'PUT',
    body: JSON.stringify(profile),
  });
}

// -----------------------------------------------------------------------------
// SAVED OPPORTUNITIES
// -----------------------------------------------------------------------------

export async function fetchSavedOpportunities(
  page: number = 1,
  pageSize: number = 20
): Promise<PaginatedSavedOpportunities> {
  return request<PaginatedSavedOpportunities>(`/saved-opportunities?page=${page}&page_size=${pageSize}`);
}

export async function saveOpportunity(opportunityId: string): Promise<SavedOpportunity> {
  return request<SavedOpportunity>(`/saved-opportunities/${encodeURIComponent(opportunityId)}`, {
    method: 'POST',
  });
}

export async function unsaveOpportunity(opportunityId: string): Promise<{ message: string; opportunity_id: string }> {
  return request<{ message: string; opportunity_id: string }>(
    `/saved-opportunities/${encodeURIComponent(opportunityId)}`,
    {
      method: 'DELETE',
    }
  );
}

// -----------------------------------------------------------------------------
// APPLICATION TRACKER
// -----------------------------------------------------------------------------

export interface ApplicationCreatePayload {
  opportunity_id: string;
  status?: ApplicationStatus;
  student_notes?: string | null;
  target_academic_cycle?: string | null;
  planned_submission_date?: string | null;
  actual_submission_date?: string | null;
}

export interface ApplicationUpdatePayload {
  status?: ApplicationStatus;
  student_notes?: string | null;
  target_academic_cycle?: string | null;
  planned_submission_date?: string | null;
  actual_submission_date?: string | null;
}

export async function fetchApplications(
  page: number = 1,
  pageSize: number = 20,
  status?: ApplicationStatus
): Promise<PaginatedApplications> {
  const query = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  if (status) query.set('status', status);
  return request<PaginatedApplications>(`/applications?${query.toString()}`);
}

export async function createApplication(payload: ApplicationCreatePayload): Promise<ApplicationRecord> {
  return request<ApplicationRecord>('/applications', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateApplication(
  applicationId: string,
  payload: ApplicationUpdatePayload
): Promise<ApplicationRecord> {
  return request<ApplicationRecord>(`/applications/${encodeURIComponent(applicationId)}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export async function deleteApplication(applicationId: string): Promise<{ message: string; application_id: string }> {
  return request<{ message: string; application_id: string }>(
    `/applications/${encodeURIComponent(applicationId)}`,
    {
      method: 'DELETE',
    }
  );
}

// -----------------------------------------------------------------------------
// PERSISTENT COMPARISON SELECTION
// -----------------------------------------------------------------------------

export async function fetchComparisonSelections(): Promise<PersistentComparisonResponse> {
  return request<PersistentComparisonResponse>('/comparison');
}

export async function addComparisonSelection(opportunityId: string): Promise<PersistentComparisonResponse> {
  return request<PersistentComparisonResponse>(`/comparison/${encodeURIComponent(opportunityId)}`, {
    method: 'POST',
  });
}

export async function removeComparisonSelection(opportunityId: string): Promise<PersistentComparisonResponse> {
  return request<PersistentComparisonResponse>(`/comparison/${encodeURIComponent(opportunityId)}`, {
    method: 'DELETE',
  });
}

export async function clearComparisonSelections(): Promise<PersistentComparisonResponse> {
  return request<PersistentComparisonResponse>('/comparison', {
    method: 'DELETE',
  });
}

