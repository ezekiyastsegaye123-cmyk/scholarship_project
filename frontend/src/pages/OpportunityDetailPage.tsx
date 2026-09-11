import React, { useState, useEffect } from 'react';
import type {
  OpportunityDetail,
  StudentProfile,
  EligibilityEvaluationResult,
  CounselorAssessmentResult,
} from '../types';
import { fetchOpportunityDetail, evaluateOpportunity, counselOpportunity } from '../api/client';
import {
  VerificationBadge,
  FundingBadge,
  EligibilityBadge,
  TriStateBadge,
  FreshnessBadge,
} from '../components/StatusBadges';
import {
  ArrowLeft,
  ExternalLink,
  ShieldCheck,
  AlertTriangle,
  FileText,
  Calendar,
  DollarSign,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Sparkles,
  Building2,
  GraduationCap,
  Scale,
  Loader2,
} from 'lucide-react';

interface OpportunityDetailPageProps {
  opportunityId: string;
  onBack: () => void;
  studentProfile: StudentProfile;
  isCompared: boolean;
  onToggleCompare: (id: string) => void;
  onGoToProfile: () => void;
}

export const OpportunityDetailPage: React.FC<OpportunityDetailPageProps> = ({
  opportunityId,
  onBack,
  studentProfile,
  isCompared,
  onToggleCompare,
  onGoToProfile,
}) => {
  const [opp, setOpp] = useState<OpportunityDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Assessment states
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [evalResult, setEvalResult] = useState<EligibilityEvaluationResult | null>(null);
  const [evalError, setEvalError] = useState<string | null>(null);
  const [allowPartiallyVerified, setAllowPartiallyVerified] = useState<boolean>(false);

  const [counseling, setCounseling] = useState<boolean>(false);
  const [counselResult, setCounselResult] = useState<CounselorAssessmentResult | null>(null);
  const [counselError, setCounselError] = useState<string | null>(null);

  // Active tab in detail view
  const [activeTab, setActiveTab] = useState<'overview' | 'eligibility' | 'funding' | 'deadlines' | 'counselor' | 'verification'>('overview');

  useEffect(() => {
    let isMounted = true;
    async function loadDetail() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchOpportunityDetail(opportunityId);
        if (isMounted) setOpp(data);
      } catch (err) {
        if (isMounted) setError(err instanceof Error ? err.message : 'Failed to load opportunity');
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadDetail();
    return () => {
      isMounted = false;
    };
  }, [opportunityId]);

  const handleRunEvaluation = async () => {
    setEvaluating(true);
    setEvalError(null);
    try {
      const res = await evaluateOpportunity(opportunityId, studentProfile, allowPartiallyVerified);
      setEvalResult(res);
      setActiveTab('eligibility');
    } catch (err) {
      setEvalError(err instanceof Error ? err.message : 'Evaluation failed');
    } finally {
      setEvaluating(false);
    }
  };

  const handleRunCounselor = async () => {
    setCounseling(true);
    setCounselError(null);
    try {
      const res = await counselOpportunity(opportunityId, studentProfile, '2026-11-01');
      setCounselResult(res);
      setActiveTab('counselor');
    } catch (err) {
      setCounselError(err instanceof Error ? err.message : 'Counseling failed');
    } finally {
      setCounseling(false);
    }
  };

  if (loading) {
    return (
      <div className="page-container state-container loading-state">
        <Loader2 className="w-8 h-8 animate-spin text-brand mx-auto mb-3" />
        <h4 className="font-semibold text-gray-700">Loading Opportunity Details...</h4>
        <p className="text-sm text-gray-500">Checking verified sources and funding records.</p>
      </div>
    );
  }

  if (error || !opp) {
    return (
      <div className="page-container state-container error-state">
        <AlertTriangle className="w-8 h-8 text-red-500 mx-auto mb-3" />
        <h4 className="font-semibold text-red-700">Could Not Load Opportunity</h4>
        <p className="text-sm text-red-600 mb-4">{error || 'Opportunity not found'}</p>
        <button type="button" className="btn-secondary" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-1 inline" /> Back to Discover
        </button>
      </div>
    );
  }

  const primarySource = opp.official_sources.find((s) => s.is_primary) || opp.official_sources[0];

  return (
    <div className="page-container detail-page-container">
      {/* Back and Action Header */}
      <div className="detail-top-nav">
        <button type="button" className="btn-back" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-1 inline" /> Back to Discover
        </button>
        <div className="detail-top-actions">
          <button
            type="button"
            className={`btn-compare-action ${isCompared ? 'active' : ''}`}
            onClick={() => onToggleCompare(opp.id)}
          >
            <Scale className="w-4 h-4 mr-1.5 inline" />
            {isCompared ? 'In Comparison' : 'Add to Comparison'}
          </button>
          {primarySource && (
            <a
              href={primarySource.url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary"
            >
              View Official Source <ExternalLink className="w-3.5 h-3.5 ml-1 inline" />
            </a>
          )}
        </div>
      </div>

      {/* Main Opportunity Header */}
      <section className="detail-header-card">
        <div className="detail-meta-badges">
          <VerificationBadge state={opp.verification_status} />
          <FreshnessBadge level={opp.freshness_level} message={opp.freshness_message} />
          <FundingBadge classification={opp.funding_classification} />
          <span className="badge badge-neutral">Cycle: {opp.academic_cycle}</span>
        </div>

        <h1 className="detail-title">{opp.title}</h1>

        <div className="detail-entities-row">
          <span className="detail-entity">
            <Building2 className="w-4 h-4 inline mr-1 text-gray-500" />
            Provider: <strong>{opp.provider_name}</strong>
          </span>
          {opp.university_name && (
            <span className="detail-entity">
              <GraduationCap className="w-4 h-4 inline mr-1 text-gray-500" />
              University: <strong>{opp.university_name}</strong>
            </span>
          )}
          <span className="detail-entity">
            Degree Level: <strong>{opp.degree_level.replace('_', ' ')}</strong>
          </span>
          <span className="detail-entity">
            Country: <strong>{opp.destination_country}</strong>
          </span>
        </div>

        {/* Quick evaluation bar */}
        <div className="quick-eval-card">
          <div className="quick-eval-info">
            <h4 className="quick-eval-heading">
              <Sparkles className="w-4 h-4 mr-1.5 text-brand inline" />
              Counselor & Eligibility Engine
            </h4>
            <p className="quick-eval-desc">
              Run deterministic Phase 1 evaluation against your current student profile ({studentProfile.citizenship_country}, GPA {studentProfile.gpa ?? 'Unset'}).
            </p>
          </div>
          <div className="quick-eval-buttons">
            <button
              type="button"
              className="btn-primary"
              disabled={evaluating}
              onClick={handleRunEvaluation}
            >
              {evaluating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-1 animate-spin inline" /> Evaluating...
                </>
              ) : (
                'Check Eligibility'
              )}
            </button>
            <button
              type="button"
              className="btn-secondary"
              disabled={counseling}
              onClick={handleRunCounselor}
            >
              {counseling ? (
                <>
                  <Loader2 className="w-4 h-4 mr-1 animate-spin inline" /> Assessing...
                </>
              ) : (
                'Counselor Assessment'
              )}
            </button>
            <button type="button" className="btn-text" onClick={onGoToProfile}>
              Edit Profile
            </button>
          </div>
        </div>

        {evalError && (
          <div className="alert-box error-alert mt-3">
            <AlertTriangle className="w-4 h-4 text-red-600 inline mr-2" />
            <span>Eligibility Evaluation Error: {evalError}</span>
          </div>
        )}

        {counselError && (
          <div className="alert-box error-alert mt-3">
            <AlertTriangle className="w-4 h-4 text-red-600 inline mr-2" />
            <span>Counselor Assessment Error: {counselError}</span>
          </div>
        )}
      </section>

      {/* Tabs Navigation */}
      <div className="detail-tabs-bar" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'overview'}
          className={`tab-btn ${activeTab === 'overview' ? 'tab-btn-active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <FileText className="w-4 h-4 mr-1.5 inline" /> Overview
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'eligibility'}
          className={`tab-btn ${activeTab === 'eligibility' ? 'tab-btn-active' : ''}`}
          onClick={() => setActiveTab('eligibility')}
        >
          <CheckCircle2 className="w-4 h-4 mr-1.5 inline" />
          Eligibility {evalResult && <span className="tab-pill">{evalResult.status}</span>}
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'funding'}
          className={`tab-btn ${activeTab === 'funding' ? 'tab-btn-active' : ''}`}
          onClick={() => setActiveTab('funding')}
        >
          <DollarSign className="w-4 h-4 mr-1.5 inline" />
          Funding Breakdown
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'deadlines'}
          className={`tab-btn ${activeTab === 'deadlines' ? 'tab-btn-active' : ''}`}
          onClick={() => setActiveTab('deadlines')}
        >
          <Calendar className="w-4 h-4 mr-1.5 inline" />
          Deadlines
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'counselor'}
          className={`tab-btn ${activeTab === 'counselor' ? 'tab-btn-active' : ''}`}
          onClick={() => setActiveTab('counselor')}
        >
          <Sparkles className="w-4 h-4 mr-1.5 inline" />
          Counselor Report {counselResult && <span className="tab-pill">Ready</span>}
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'verification'}
          className={`tab-btn ${activeTab === 'verification' ? 'tab-btn-active' : ''}`}
          onClick={() => setActiveTab('verification')}
        >
          <ShieldCheck className="w-4 h-4 mr-1.5 inline" />
          Evidence & Verification
          {opp.conflict_records.length > 0 && <span className="tab-pill-warning">Conflicts</span>}
        </button>
      </div>

      {/* Tab Panels */}
      <div className="tab-content-panel">
        {/* TAB 1: OVERVIEW */}
        {activeTab === 'overview' && (
          <div className="tab-pane">
            <div className="pane-section">
              <h3 className="section-title">Opportunity Description</h3>
              <p className="description-text">
                {opp.description || 'No detailed description published.'}
              </p>
            </div>

            <div className="pane-section">
              <h3 className="section-title">Key Epistemic Indicators</h3>
              <div className="flags-grid">
                <div className="flag-card">
                  <span className="flag-label">International Students Allowed</span>
                  <TriStateBadge value={opp.international_students_allowed} label="Status" />
                </div>
                <div className="flag-card">
                  <span className="flag-label">Financial Need Requirement</span>
                  <TriStateBadge value={opp.financial_need_required} label="Need Required" />
                </div>
                <div className="flag-card">
                  <span className="flag-label">Requires SAT</span>
                  <TriStateBadge value={opp.requires_sat} label="SAT" />
                </div>
                <div className="flag-card">
                  <span className="flag-label">Requires ACT</span>
                  <TriStateBadge value={opp.requires_act} label="ACT" />
                </div>
                <div className="flag-card">
                  <span className="flag-label">Requires CSS Profile</span>
                  <TriStateBadge value={opp.requires_css_profile} label="CSS Profile" />
                </div>
                <div className="flag-card">
                  <span className="flag-label">Varies by Program</span>
                  <span className="badge badge-neutral">{opp.varies_by_program ? 'Yes' : 'No'}</span>
                </div>
              </div>
            </div>

            {opp.application_requirements.length > 0 && (
              <div className="pane-section">
                <h3 className="section-title">Application Requirements Checklist</h3>
                <ul className="checklist-items">
                  {opp.application_requirements.map((req) => (
                    <li key={req.id} className="checklist-item">
                      <div className="item-main">
                        <span className="item-title font-medium">{req.title}</span>
                        <span className="badge badge-neutral text-xs ml-2">{req.kind}</span>
                        {req.description && <p className="item-sub text-xs text-gray-500 mt-0.5">{req.description}</p>}
                        {req.instructions && <p className="item-sub text-xs text-gray-600 italic mt-0.5">{req.instructions}</p>}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: ELIGIBILITY */}
        {activeTab === 'eligibility' && (
          <div className="tab-pane">
            {!evalResult ? (
              <div className="state-container empty-state">
                <CheckCircle2 className="w-8 h-8 text-brand mx-auto mb-2" />
                <h4 className="font-semibold text-gray-700">No Evaluation Generated Yet</h4>
                <p className="text-sm text-gray-500 mb-4">
                  Run the deterministic eligibility evaluation to check all published criteria against your profile.
                </p>
                <button
                  type="button"
                  className="btn-primary"
                  disabled={evaluating}
                  onClick={handleRunEvaluation}
                >
                  {evaluating ? 'Evaluating...' : 'Evaluate Eligibility Now'}
                </button>
              </div>
            ) : (
              <div>
                <div className="eval-summary-banner">
                  <div>
                    <span className="text-xs uppercase tracking-wider text-gray-500 font-semibold block">
                      Overall Eligibility Status
                    </span>
                    <EligibilityBadge status={evalResult.status} />
                  </div>
                  <div className="eval-summary-explanation">
                    <p className="text-sm text-gray-700 font-medium">{evalResult.explanation}</p>
                    {evalResult.evaluation_contains_unverified_facts && (
                      <p className="text-xs text-amber-700 mt-1">
                        ⚠️ Note: This evaluation was executed with unverified facts enabled.
                      </p>
                    )}
                  </div>
                </div>

                {evalResult.is_gated && (
                  <div className="gated-warning-box">
                    <AlertTriangle className="w-5 h-5 text-amber-600 inline mr-2 align-middle" />
                    <strong>Gated Evaluation: </strong>
                    <span>
                      This opportunity has not reached official verification. By default, unverified data is gated to prevent false student guarantees.
                    </span>
                    <div className="mt-3">
                      <label className="checkbox-label text-sm text-amber-900">
                        <input
                          type="checkbox"
                          checked={allowPartiallyVerified}
                          onChange={(e) => {
                            setAllowPartiallyVerified(e.target.checked);
                          }}
                        />
                        <span className="ml-2 font-medium">
                          Allow evaluation with partially-verified / unverified facts (with explicit uncertainty flagging)
                        </span>
                      </label>
                      <button
                        type="button"
                        className="btn-secondary btn-sm mt-2 block"
                        onClick={handleRunEvaluation}
                      >
                        Re-evaluate with Overridden Gate
                      </button>
                    </div>
                  </div>
                )}

                <h4 className="font-semibold text-gray-800 mb-3 mt-6">Published Eligibility Rule Breakdown</h4>
                <div className="rules-table-container">
                  <table className="rules-table">
                    <thead>
                      <tr>
                        <th>Rule ID / Field</th>
                        <th>Kind</th>
                        <th>Status</th>
                        <th>Expected</th>
                        <th>Actual (Student)</th>
                        <th>Evidence / Explanation</th>
                      </tr>
                    </thead>
                    <tbody>
                      {evalResult.rule_results.map((r) => (
                        <tr key={r.rule_id}>
                          <td className="font-mono text-xs">{r.rule_id}</td>
                          <td>
                            <span className="badge badge-neutral text-xs">{r.rule_kind}</span>
                          </td>
                          <td>
                            {r.satisfied === true ? (
                              <span className="badge badge-eligible text-xs">
                                <CheckCircle2 className="w-3 h-3 inline mr-1" /> Satisfied
                              </span>
                            ) : r.satisfied === false ? (
                              <span className="badge badge-ineligible text-xs">
                                <XCircle className="w-3 h-3 inline mr-1" /> Not Satisfied
                              </span>
                            ) : (
                              <span className="badge badge-needs-info text-xs">
                                <HelpCircle className="w-3 h-3 inline mr-1" /> {r.status}
                              </span>
                            )}
                          </td>
                          <td className="font-mono text-xs">
                            {r.comparison_operator} {JSON.stringify(r.expected_value)}
                          </td>
                          <td className="font-mono text-xs">
                            {r.actual_value !== undefined && r.actual_value !== null
                              ? JSON.stringify(r.actual_value)
                              : '<unknown>'}
                          </td>
                          <td className="text-xs text-gray-600">
                            <div>{r.explanation}</div>
                            {r.evidence_snippet && (
                              <div className="quote-snippet mt-1 italic">"{r.evidence_snippet}"</div>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 3: FUNDING BREAKDOWN */}
        {activeTab === 'funding' && (
          <div className="tab-pane">
            <div className="funding-alert-banner">
              <AlertTriangle className="w-5 h-5 text-indigo-600 inline mr-2 align-middle" />
              <strong>Crucial Epistemic Principle: Full Tuition is NOT Full Funding.</strong>
              <p className="text-xs text-indigo-900 mt-1">
                Full tuition covers institutional fees/courses only. Living expenses, housing, health insurance, and books require distinct funding components.
              </p>
            </div>

            <div className="pane-section mt-4">
              <h3 className="section-title">Award Overview</h3>
              <div className="award-summary-box">
                <div className="flex items-center gap-3">
                  <FundingBadge classification={opp.funding_classification} />
                  <span className="font-medium text-gray-800">{opp.funding_summary}</span>
                </div>
                {opp.award_details && (
                  <div className="mt-3 text-sm text-gray-600 space-y-1">
                    <div>Award Title: <strong>{opp.award_details.title}</strong></div>
                    <div>Renewable: <strong>{opp.award_details.is_renewable}</strong></div>
                    {opp.award_details.renewal_criteria && (
                      <div>Renewal Criteria: <em>{opp.award_details.renewal_criteria}</em></div>
                    )}
                    {opp.award_details.estimated_annual_value_usd && (
                      <div>Estimated Annual Value: <strong>${opp.award_details.estimated_annual_value_usd.toLocaleString()} USD</strong></div>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="pane-section">
              <h3 className="section-title">Decomposed Funding Components</h3>
              {(!opp.award_details || opp.award_details.components.length === 0) ? (
                <p className="text-sm text-gray-500">
                  Specific breakdown of funding components is not published in verified sources.
                </p>
              ) : (
                <div className="components-list">
                  {opp.award_details.components.map((c) => (
                    <div key={c.id} className="funding-component-card">
                      <div className="component-header">
                        <span className="component-type font-semibold text-gray-800">
                          {c.component_type.replace('_', ' ')}
                        </span>
                        <span className="component-amount font-mono text-sm text-brand font-bold">
                          {c.percentage_tuition ? `${c.percentage_tuition}% of Tuition` : null}
                          {c.amount_min !== null || c.amount_max !== null ? (
                            <>
                              {c.amount_min !== null ? `$${c.amount_min.toLocaleString()}` : ''}
                              {c.amount_max !== null && c.amount_max !== c.amount_min
                                ? ` - $${c.amount_max.toLocaleString()}`
                                : ''}{' '}
                              {c.currency} ({c.amount_period})
                            </>
                          ) : null}
                          {!c.percentage_tuition && c.amount_min === null && c.amount_max === null && 'Specified in policy'}
                        </span>
                      </div>
                      {c.description && <p className="text-xs text-gray-600 mt-1">{c.description}</p>}
                      {c.source_evidence_snippet && (
                        <blockquote className="quote-snippet mt-2 text-xs">
                          "{c.source_evidence_snippet}"
                        </blockquote>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 4: DEADLINES */}
        {activeTab === 'deadlines' && (
          <div className="tab-pane">
            <div className="pane-section">
              <h3 className="section-title">Application Timeline</h3>
              {opp.deadlines.length === 0 ? (
                <div className="state-container empty-state">
                  <p className="text-sm text-gray-500">
                    No verified deadlines have been published for academic cycle {opp.academic_cycle}.
                  </p>
                </div>
              ) : (
                <div className="timeline-container">
                  {opp.deadlines.map((dl) => (
                    <div key={dl.id} className="timeline-item">
                      <div className="timeline-icon">
                        <Calendar className="w-4 h-4 text-brand" />
                      </div>
                      <div className="timeline-details">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-gray-800">
                            {dl.deadline_type.replace('_', ' ')}
                          </span>
                          <span className="badge badge-neutral text-xs">
                            {dl.is_exact_date ? 'Exact Date' : 'Inferred / Window'}
                          </span>
                          {dl.varies_by_program && (
                            <span className="badge badge-warning text-xs">Varies by Program</span>
                          )}
                        </div>
                        <div className="text-sm font-medium text-brand mt-0.5">
                          {dl.deadline_date ? (
                            new Date(dl.deadline_date).toLocaleDateString(undefined, {
                              weekday: 'short',
                              year: 'numeric',
                              month: 'long',
                              day: 'numeric',
                            })
                          ) : (
                            'Date not specified'
                          )}
                          {dl.timezone && ` (${dl.timezone})`}
                        </div>
                        {dl.context_description && (
                          <p className="text-xs text-gray-600 mt-1">{dl.context_description}</p>
                        )}
                        {dl.source_evidence_snippet && (
                          <blockquote className="quote-snippet mt-2 text-xs">
                            "{dl.source_evidence_snippet}"
                          </blockquote>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 5: COUNSELOR QUALITATIVE ASSESSMENT */}
        {activeTab === 'counselor' && (
          <div className="tab-pane">
            {!counselResult ? (
              <div className="state-container empty-state">
                <Sparkles className="w-8 h-8 text-brand mx-auto mb-2" />
                <h4 className="font-semibold text-gray-700">No Counselor Assessment Generated</h4>
                <p className="text-sm text-gray-500 mb-4">
                  The qualitative counselor assessment synthesizes academic alignment, geographic alignment, funding expectations, and application readiness without arbitrary LLM guessing.
                </p>
                <button
                  type="button"
                  className="btn-primary"
                  disabled={counseling}
                  onClick={handleRunCounselor}
                >
                  {counseling ? 'Generating Assessment...' : 'Run Counselor Assessment'}
                </button>
              </div>
            ) : (
              <div className="counselor-report">
                <div className="counselor-top-grid">
                  <div className="counselor-pill-card">
                    <span className="text-xs text-gray-500 font-semibold block uppercase">Academic Alignment</span>
                    <span className="text-base font-bold text-brand">{counselResult.academic_alignment}</span>
                  </div>
                  <div className="counselor-pill-card">
                    <span className="text-xs text-gray-500 font-semibold block uppercase">Geographic Alignment</span>
                    <span className="text-base font-bold text-brand">{counselResult.geographic_alignment}</span>
                  </div>
                  <div className="counselor-pill-card">
                    <span className="text-xs text-gray-500 font-semibold block uppercase">Funding Understanding</span>
                    <span className="text-base font-bold text-brand">{counselResult.funding_understanding}</span>
                  </div>
                  <div className="counselor-pill-card">
                    <span className="text-xs text-gray-500 font-semibold block uppercase">Deadline Status</span>
                    <span className="text-base font-bold text-brand">{counselResult.deadline_assessment.status}</span>
                  </div>
                  <div className="counselor-pill-card">
                    <span className="text-xs text-gray-500 font-semibold block uppercase">Application Readiness</span>
                    <span className="text-base font-bold text-brand">{counselResult.application_readiness}</span>
                  </div>
                </div>

                <div className="counselor-quadrant-grid mt-6">
                  <div className="counselor-section-card strengths-card">
                    <h4 className="section-subtitle text-emerald-800">
                      <CheckCircle2 className="w-4 h-4 mr-1.5 inline" /> Strengths
                    </h4>
                    {counselResult.strengths.length === 0 ? (
                      <p className="text-xs text-gray-500">No verified strengths identified.</p>
                    ) : (
                      <ul className="counselor-bullets">
                        {counselResult.strengths.map((s, idx) => (
                          <li key={idx} className="text-xs text-emerald-900">{s}</li>
                        ))}
                      </ul>
                    )}
                  </div>

                  <div className="counselor-section-card gaps-card">
                    <h4 className="section-subtitle text-red-800">
                      <XCircle className="w-4 h-4 mr-1.5 inline" /> Gaps & Incompatibilities
                    </h4>
                    {counselResult.gaps.length === 0 ? (
                      <p className="text-xs text-gray-500">No explicit incompatibilities identified.</p>
                    ) : (
                      <ul className="counselor-bullets">
                        {counselResult.gaps.map((g, idx) => (
                          <li key={idx} className="text-xs text-red-900">{g}</li>
                        ))}
                      </ul>
                    )}
                  </div>

                  <div className="counselor-section-card uncertainties-card">
                    <h4 className="section-subtitle text-amber-800">
                      <HelpCircle className="w-4 h-4 mr-1.5 inline" /> Unknowns & Uncertainties
                    </h4>
                    {counselResult.uncertainties.length === 0 ? (
                      <p className="text-xs text-gray-500">All required factors have been verified.</p>
                    ) : (
                      <ul className="counselor-bullets">
                        {counselResult.uncertainties.map((u, idx) => (
                          <li key={idx} className="text-xs text-amber-900">{u}</li>
                        ))}
                      </ul>
                    )}
                  </div>

                  <div className="counselor-section-card recommendations-card">
                    <h4 className="section-subtitle text-brand">
                      <Sparkles className="w-4 h-4 mr-1.5 inline" /> Recommended Next Steps
                    </h4>
                    {counselResult.recommended_actions.length === 0 ? (
                      <p className="text-xs text-gray-500">No action items recommended at this stage.</p>
                    ) : (
                      <ul className="counselor-bullets">
                        {counselResult.recommended_actions.map((r, idx) => (
                          <li key={idx} className="text-xs text-brand font-medium">{r}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 6: EVIDENCE & PROVENANCE */}
        {activeTab === 'verification' && (
          <div className="tab-pane">
            {opp.conflict_records.length > 0 && (
              <div className="conflict-alert-card mb-6">
                <div className="flex items-center gap-2 text-red-700 font-semibold mb-2">
                  <AlertTriangle className="w-5 h-5" />
                  <span>Conflicting Evidence Logged ({opp.conflict_records.length})</span>
                </div>
                <p className="text-xs text-red-600 mb-3">
                  Conflicting facts were reported across discovery sources. As an epistemic principle, we do not pick a favorite source — you should verify with the primary provider.
                </p>
                <div className="space-y-3">
                  {opp.conflict_records.map((cr) => (
                    <div key={cr.id} className="conflict-box">
                      <div className="font-mono text-xs font-bold text-gray-700">
                        Field: {cr.field_name} (Status: {cr.resolution_status})
                      </div>
                      <div className="conflict-sources-grid mt-2">
                        <div className="conflict-side">
                          <span className="text-xs font-semibold text-gray-600">Source A ({cr.source_a_tier || 'Tier'}):</span>
                          <div className="text-xs font-mono text-gray-800">{cr.source_a_value}</div>
                          <a href={cr.source_a_url} target="_blank" rel="noopener noreferrer" className="text-xs text-brand underline truncate block mt-1">
                            {cr.source_a_url}
                          </a>
                        </div>
                        <div className="conflict-side">
                          <span className="text-xs font-semibold text-gray-600">Source B ({cr.source_b_tier || 'Tier'}):</span>
                          <div className="text-xs font-mono text-gray-800">{cr.source_b_value}</div>
                          <a href={cr.source_b_url} target="_blank" rel="noopener noreferrer" className="text-xs text-brand underline truncate block mt-1">
                            {cr.source_b_url}
                          </a>
                        </div>
                      </div>
                      {cr.resolution_notes && (
                        <p className="text-xs text-gray-600 mt-2 italic">Notes: {cr.resolution_notes}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="pane-section">
              <h3 className="section-title">Authoritative Institutional Sources</h3>
              <div className="sources-list">
                {opp.official_sources.map((s) => (
                  <div key={s.id} className="source-item">
                    <div className="source-main">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-gray-800">{s.source_domain}</span>
                        <span className="badge badge-verified text-xs">{s.authority_tier}</span>
                        {s.is_primary && <span className="badge badge-brand text-xs">Primary</span>}
                      </div>
                      {s.page_title && <p className="text-xs text-gray-600 mt-0.5">{s.page_title}</p>}
                      <a
                        href={s.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-brand hover:underline inline-block mt-1 truncate max-w-lg"
                      >
                        {s.url} <ExternalLink className="w-3 h-3 inline" />
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {opp.verification_records.length > 0 && (
              <div className="pane-section">
                <h3 className="section-title">Audit Verification Trail</h3>
                <div className="verif-trail">
                  {opp.verification_records.map((vr) => (
                    <div key={vr.id} className="verif-record-card">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-xs text-gray-800">
                          Verifier: {vr.verifier_identity} ({vr.verification_method})
                        </span>
                        <span className="text-xs text-gray-500 font-mono">
                          {vr.verified_at ? new Date(vr.verified_at).toLocaleDateString() : ''}
                        </span>
                      </div>
                      <blockquote className="quote-snippet mt-2 text-xs">
                        "{vr.evidence_quote}"
                      </blockquote>
                      {vr.notes && <p className="text-xs text-gray-600 mt-1 italic">{vr.notes}</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {opp.verification_histories && opp.verification_histories.length > 0 && (
              <div className="pane-section">
                <h3 className="section-title">Fact Change History & Re-verification Ledger</h3>
                <p className="text-xs text-gray-500 mb-3">
                  Immutable audit ledger recording every fact modification, source evidence quote, and promotion decision.
                </p>
                <div className="space-y-3">
                  {opp.verification_histories.map((vh) => (
                    <div key={vh.id} className="verif-record-card">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-gray-800">
                          Field: <span className="font-mono text-brand font-bold">{vh.field_name}</span> &mdash; <span className="badge badge-brand text-xs">{vh.decision}</span>
                        </span>
                        <span className="text-gray-500 font-mono">
                          {vh.changed_at ? new Date(vh.changed_at).toLocaleString() : ''}
                        </span>
                      </div>
                      <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-2 text-xs bg-gray-50 p-2 rounded border border-gray-100">
                        <div>
                          <span className="text-gray-500 font-semibold block">Previous Value:</span>
                          <span className="font-mono text-gray-700">{vh.old_value || '<none>'}</span>
                          {vh.old_evidence_quote && (
                            <blockquote className="quote-snippet mt-1 italic text-xs">"{vh.old_evidence_quote}"</blockquote>
                          )}
                        </div>
                        <div>
                          <span className="text-gray-500 font-semibold block">New Verified Value:</span>
                          <span className="font-mono text-emerald-700 font-bold">{vh.new_value || '<none>'}</span>
                          {vh.new_evidence_quote && (
                            <blockquote className="quote-snippet mt-1 italic text-xs text-emerald-900">"{vh.new_evidence_quote}"</blockquote>
                          )}
                        </div>
                      </div>
                      <p className="text-xs text-gray-600 mt-2">
                        <strong>Decision Reason:</strong> {vh.reason}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="pane-section">
              <h3 className="section-title">Integrity Fingerprint</h3>
              <p className="text-xs text-gray-500 font-mono bg-gray-50 p-2 rounded border border-gray-200 break-all">
                SHA-256: {opp.fingerprint_sha256}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
