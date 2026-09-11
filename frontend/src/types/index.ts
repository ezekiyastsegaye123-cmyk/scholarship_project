export type TriState = 'YES' | 'NO' | 'UNKNOWN' | 'NOT_APPLICABLE' | 'CONFLICTING';

export type VerificationState =
  | 'VERIFIED'
  | 'PARTIALLY_VERIFIED'
  | 'CONFLICTING'
  | 'OUTDATED'
  | 'UNVERIFIED'
  | 'SOURCE_UNAVAILABLE'
  | 'QUARANTINED_FOR_REVIEW';

export type FundingClassification =
  | 'FULL_FUNDING'
  | 'FULL_TUITION'
  | 'PARTIAL_FUNDING'
  | 'STIPEND_ONLY'
  | 'FEES_ONLY'
  | 'UNKNOWN';

export type DeadlineType =
  | 'SCHOLARSHIP_APPLICATION'
  | 'UNIVERSITY_APPLICATION'
  | 'FINANCIAL_AID'
  | 'EARLY_ACTION'
  | 'EARLY_DECISION'
  | 'REGULAR_DECISION'
  | 'PRIORITY'
  | 'ROLLING'
  | 'NOMINATION'
  | 'DOCUMENT_SUBMISSION'
  | 'INTERNATIONAL_STUDENT';

export type EligibilityStatus =
  | 'ELIGIBLE'
  | 'INELIGIBLE'
  | 'NEEDS_INFORMATION'
  | 'GATED_UNVERIFIED'
  | 'NEEDS_REVIEW'
  | 'OUTDATED_CYCLE';

export type FreshnessLevel = 'FRESH' | 'MODERATE' | 'STALE' | 'UNVERIFIED';

export interface OpportunitySummary {
  id: string;
  title: string;
  provider_name: string;
  university_name: string | null;
  target_degree_level: string;
  degree_level?: string;
  destination_country: string;
  academic_cycle: string;
  verification_status: VerificationState;
  funding_classification: FundingClassification;
  funding_summary: string;
  earliest_deadline: string | null;
  deadline_type: DeadlineType | null;
  deadline_status: string;
  international_students_allowed: TriState;
  requires_sat: TriState;
  requires_act: TriState;
  financial_need_required: TriState;
  primary_source_url: string | null;
  freshness_level?: FreshnessLevel;
  freshness_message?: string;
  last_crawled_at?: string | null;
}

export interface PaginatedOpportunities {
  items: OpportunitySummary[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
  total_pages?: number;
}

export interface FundingComponent {
  id: string;
  component_type: string;
  amount_min: number | null;
  amount_max: number | null;
  currency: string;
  amount_period: string | null;
  percentage_tuition: number | null;
  description: string | null;
  source_evidence_snippet: string | null;
}

export interface AwardDetails {
  id: string;
  funding_classification: string;
  title: string;
  is_renewable: string;
  renewal_criteria: string | null;
  estimated_annual_value_usd: number | null;
  components: FundingComponent[];
}

export interface DeadlineRecord {
  id: string;
  deadline_date: string | null;
  deadline_type: string;
  is_exact_date: boolean;
  timezone: string | null;
  academic_cycle: string;
  varies_by_program: boolean;
  context_description: string | null;
  source_evidence_snippet: string | null;
}

export interface EligibilityRuleRecord {
  id: string;
  rule_id: string;
  kind: string;
  expression_json: Record<string, any>;
  description: string | null;
  source_evidence_snippet: string | null;
  is_verified: boolean;
}

export interface RequirementRecord {
  id: string;
  requirement_type: string;
  kind: string;
  name: string;
  description: string | null;
  source_evidence_snippet: string | null;
}

export interface ApplicationRequirementRecord {
  id: string;
  requirement_type: string;
  kind: string;
  title: string;
  description: string | null;
  instructions: string | null;
  submission_format: string | null;
  source_evidence_snippet: string | null;
}

export interface OfficialSourceRecord {
  id: string;
  url: string;
  source_domain: string;
  authority_tier: string;
  is_primary: boolean;
  page_title: string | null;
  extracted_text_snippet: string | null;
  last_crawled_at: string | null;
  last_http_status: number | null;
}

export interface DiscoverySourceRecord {
  id: string;
  url: string;
  source_name: string;
  authority_tier: string;
  discovery_notes: string | null;
  discovered_at: string | null;
}

export interface VerificationRecord {
  id: string;
  verification_state: string;
  verifier_identity: string;
  verification_method: string;
  evidence_url: string;
  evidence_quote: string;
  notes: string | null;
  verified_at: string | null;
}

export interface ConflictRecord {
  id: string;
  field_name: string;
  source_a_value: string;
  source_a_url: string;
  source_b_value: string;
  source_b_url: string;
  source_a_tier: string | null;
  source_b_tier: string | null;
  source_a_evidence: string | null;
  source_b_evidence: string | null;
  resolution_status: string;
  resolution_notes: string | null;
  resolved_at: string | null;
  recorded_at: string | null;
}

export interface VerificationHistoryRecord {
  id: string;
  scholarship_id: string;
  field_name: string;
  old_value: string | null;
  new_value: string | null;
  old_evidence_url: string | null;
  old_evidence_quote: string | null;
  new_evidence_url: string | null;
  new_evidence_quote: string | null;
  decision: string;
  reason: string;
  changed_at: string;
}

export interface OpportunityDetail extends OpportunitySummary {
  description: string | null;
  varies_by_program: boolean;
  requires_css_profile: TriState;
  fingerprint_sha256: string;
  award_details: AwardDetails | null;
  deadlines: DeadlineRecord[];
  eligibility_rules: EligibilityRuleRecord[];
  requirements: RequirementRecord[];
  application_requirements: ApplicationRequirementRecord[];
  official_sources: OfficialSourceRecord[];
  discovery_sources: DiscoverySourceRecord[];
  verification_records: VerificationRecord[];
  conflict_records: ConflictRecord[];
  verification_histories?: VerificationHistoryRecord[];
}

export interface StudentProfile {
  degree_level: string;
  gpa: number | null;
  gpa_scale: number;
  citizenship_country: string;
  country_of_residence: string;
  us_state: string | null;
  intended_major: string | null;
  sat_total: number | null;
  act_composite: number | null;
  toefl_total: number | null;
  ielts_overall: number | null;
  financial_need_tier: string | null;
  has_leadership_experience: boolean;
  has_community_service: boolean;
  first_generation_college_student: boolean;
  prepared_components: string[];
  target_academic_cycle: string;
}

export interface RuleEvaluationResult {
  rule_id: string;
  rule_kind?: string;
  kind?: string;
  satisfied?: boolean | null;
  status: string;
  field_name?: string;
  field?: string;
  comparison_operator?: string;
  expected_value?: any;
  actual_value?: any;
  is_verified?: boolean;
  explanation: string;
  evidence_snippet?: string | null;
}

export interface EligibilityEvaluationResult {
  opportunity_id?: string;
  opportunity_title?: string;
  verification_status?: string;
  is_gated: boolean;
  status: EligibilityStatus;
  rule_results?: RuleEvaluationResult[];
  satisfied_rules?: RuleEvaluationResult[];
  failed_rules?: RuleEvaluationResult[];
  unknown_rules?: RuleEvaluationResult[];
  conflicting_rules?: RuleEvaluationResult[];
  not_applicable_rules?: RuleEvaluationResult[];
  supplementary_rules?: RuleEvaluationResult[];
  explanation?: string;
  explanations?: string[];
  evaluation_contains_unverified_facts: boolean;
  evaluated_at: string;
}

export interface CounselorAssessmentResult {
  opportunity_id?: string;
  opportunity_title?: string;
  academic_cycle?: string;
  academic_alignment: string | { level: string; details?: string[] };
  geographic_alignment: string | { level: string; details?: string[] };
  funding_understanding?: string;
  funding_assessment?: {
    summary?: string;
    funding_classification?: string;
    details?: string[];
    [key: string]: any;
  };
  deadline_assessment?: {
    status?: string;
    summary?: string;
    earliest_deadline?: string | null;
    is_urgent?: boolean;
    explanation?: string;
    [key: string]: any;
  };
  application_readiness: string | { level: string; details?: string[] };
  strengths: string[];
  gaps: string[];
  uncertainties?: string[];
  unknowns?: string[];
  recommended_actions?: string[];
  recommended_next_steps?: string[];
  evaluated_at: string;
}

export interface OpportunityComparisonItem {
  opportunity_id: string;
  title?: string;
  opportunity_title?: string;
  provider?: string;
  provider_name?: string | null;
  university?: string | null;
  university_name?: string | null;
  funding_classification: string;
  verification_status: string;
  earliest_deadline: string | null;
  deadline_status: string;
  eligibility_status: string | null;
  academic_alignment: string | null;
  geographic_alignment: string | null;
  application_readiness: string | null;
  primary_source_url: string | null;
}

export interface ComparisonResponse {
  academic_cycle?: string;
  items?: OpportunityComparisonItem[];
  comparisons?: OpportunityComparisonItem[];
  ordering_rule?: string;
  total_compared?: number;
}

export type ApplicationStatus =
  | 'NOT_STARTED'
  | 'PLANNING'
  | 'IN_PROGRESS'
  | 'SUBMITTED'
  | 'WITHDRAWN'
  | 'DECISION_RECEIVED';

export interface StudentAccount {
  id: string;
  email: string;
  is_active: boolean;
  has_profile: boolean;
  created_at: string;
}

export interface AuthResponse {
  token: string;
  token_type: string;
  expires_at: string;
  account: StudentAccount;
}

export interface SavedOpportunity {
  id: string;
  opportunity_id: string;
  created_at: string;
  opportunity: OpportunitySummary;
}

export interface PaginatedSavedOpportunities {
  items: SavedOpportunity[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ApplicationRecord {
  id: string;
  opportunity_id: string;
  status: ApplicationStatus;
  student_notes: string | null;
  target_academic_cycle: string | null;
  planned_submission_date: string | null;
  actual_submission_date: string | null;
  created_at: string;
  updated_at: string;
  opportunity: OpportunitySummary;
}

export interface PaginatedApplications {
  items: ApplicationRecord[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ComparisonSelectionItem {
  id: string;
  opportunity_id: string;
  created_at: string;
  opportunity: OpportunitySummary;
}

export interface PersistentComparisonResponse {
  items: ComparisonSelectionItem[];
  count: number;
  max_limit: number;
}

export interface PersistentProfile {
  account_id: string;
  citizenship_country?: string | null;
  residence_country?: string | null;
  gpa?: number | null;
  gpa_scale?: number | null;
  current_education_level?: string | null;
  target_degree_level?: string | null;
  field_of_study?: string | null;
  has_sat?: string;
  sat_total?: number | null;
  has_act?: string;
  act_composite?: number | null;
  demonstrates_financial_need?: string;
  requires_visa?: string;
  is_first_generation?: string;
  gender?: string | null;
  race_ethnicity?: string | null;
  created_at: string;
  updated_at: string;
}

// ==============================================================================
// PHASE 5: AI COUNSELOR SCHEMAS
// ==============================================================================

export type EpistemicStatus =
  | 'GROUNDED'
  | 'PARTIALLY_GROUNDED'
  | 'INSUFFICIENT_INFORMATION'
  | 'CONFLICTING_INFORMATION';

export interface SourceCitation {
  title: string;
  url?: string | null;
  authority_tier?: string | null;
  verification_status?: string | null;
  evidence_quote?: string | null;
  is_primary: boolean;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface AICounselorRequest {
  opportunity_id: string;
  message: string;
  conversation_history?: ChatMessage[];
}

export interface AICounselorResponse {
  answer: string;
  epistemic_status: EpistemicStatus;
  warnings: string[];
  sources: SourceCitation[];
  known_facts: string[];
  unknowns: string[];
  next_steps: string[];
  disclaimer: string;
  is_fallback: boolean;
}
