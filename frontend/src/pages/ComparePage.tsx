import React, { useState, useEffect } from 'react';
import type { ComparisonResponse, StudentProfile } from '../types';
import { compareOpportunities } from '../api/client';
import { VerificationBadge, FundingBadge, EligibilityBadge } from '../components/StatusBadges';
import { Scale, ArrowLeft, ExternalLink, Trash2, AlertTriangle, Loader2 } from 'lucide-react';

interface ComparePageProps {
  opportunityIds: string[];
  studentProfile: StudentProfile;
  onRemoveFromCompare: (id: string) => void;
  onClearAll: () => void;
  onGoToDiscover: () => void;
  onSelectOpportunity: (id: string) => void;
}

export const ComparePage: React.FC<ComparePageProps> = ({
  opportunityIds,
  studentProfile,
  onRemoveFromCompare,
  onClearAll,
  onGoToDiscover,
  onSelectOpportunity,
}) => {
  const [data, setData] = useState<ComparisonResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const comparisons: any[] = data ? ((data as any).comparisons || (data as any).items || []) : [];

  useEffect(() => {
    if (opportunityIds.length === 0) {
      setData(null);
      return;
    }

    let isMounted = true;
    async function loadComparison() {
      setLoading(true);
      setError(null);
      try {
        const res = await compareOpportunities(opportunityIds, studentProfile);
        if (isMounted) setData(res);
      } catch (err) {
        if (isMounted) setError(err instanceof Error ? err.message : 'Comparison failed');
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadComparison();
    return () => {
      isMounted = false;
    };
  }, [opportunityIds, studentProfile]);

  if (opportunityIds.length === 0) {
    return (
      <div className="page-container state-container empty-state">
        <Scale className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <h3 className="text-xl font-bold text-gray-800">No Scholarships Selected for Comparison</h3>
        <p className="text-sm text-gray-500 max-w-md mx-auto mb-6 mt-1">
          Browse scholarships and click the "Compare" checkbox on any opportunity card to view them side-by-side.
        </p>
        <button type="button" className="btn-primary" onClick={onGoToDiscover}>
          <ArrowLeft className="w-4 h-4 mr-1.5 inline" /> Browse Scholarships
        </button>
      </div>
    );
  }

  return (
    <div className="page-container compare-page-container">
      <div className="compare-header-row">
        <div>
          <button type="button" className="btn-back mb-2" onClick={onGoToDiscover}>
            <ArrowLeft className="w-4 h-4 mr-1 inline" /> Back to Discover
          </button>
          <h2 className="text-2xl font-bold text-gray-900">Side-by-Side Scholarship Comparison</h2>
          <p className="text-sm text-gray-600">
            Comparing <strong>{opportunityIds.length}</strong> opportunities against student profile ({studentProfile.citizenship_country}, GPA {studentProfile.gpa ?? 'Unset'}).
          </p>
        </div>

        <div className="compare-top-actions">
          <button type="button" className="btn-secondary btn-sm" onClick={onClearAll}>
            <Trash2 className="w-4 h-4 mr-1 inline" /> Clear All
          </button>
          <button type="button" className="btn-primary btn-sm" onClick={onGoToDiscover}>
            + Add More
          </button>
        </div>
      </div>

      <div className="epistemic-alert mt-4">
        <AlertTriangle className="w-4 h-4 text-brand inline mr-1.5 align-middle" />
        <span>
          <strong>Ethical Comparison Principle:</strong> We do not compute synthetic composite scores or fake "probability of winning." You receive objective, verified criteria comparisons.
        </span>
      </div>

      {loading ? (
        <div className="state-container loading-state mt-6">
          <Loader2 className="w-8 h-8 animate-spin text-brand mx-auto mb-3" />
          <h4 className="font-semibold text-gray-700">Generating Comparison Matrix...</h4>
          <p className="text-sm text-gray-500">Evaluating eligibility rules and counselor alignment for selected opportunities.</p>
        </div>
      ) : error ? (
        <div className="state-container error-state mt-6">
          <AlertTriangle className="w-8 h-8 text-red-500 mx-auto mb-3" />
          <h4 className="font-semibold text-red-700">Unable to Compare Opportunities</h4>
          <p className="text-sm text-red-600 mb-4">{error}</p>
          <button type="button" className="btn-primary" onClick={onGoToDiscover}>
            Return to Discover
          </button>
        </div>
      ) : !data || comparisons.length === 0 ? (
        <div className="state-container empty-state mt-6">
          <p className="text-sm text-gray-500">No comparison data available.</p>
        </div>
      ) : (
        <div className="matrix-wrapper mt-6">
          <table className="comparison-table">
            <thead>
              <tr>
                <th className="feature-col">Dimension</th>
                {comparisons.map((c) => (
                  <th key={c.opportunity_id} className="opp-header-col">
                    <div className="flex items-start justify-between gap-2">
                      <button
                        type="button"
                        className="opp-col-title"
                        onClick={() => onSelectOpportunity(c.opportunity_id)}
                      >
                        {c.title || c.opportunity_title}
                      </button>
                      <button
                        type="button"
                        className="remove-col-btn"
                        onClick={() => onRemoveFromCompare(c.opportunity_id)}
                        title="Remove from comparison"
                        aria-label={`Remove ${c.title || c.opportunity_title}`}
                      >
                        ×
                      </button>
                    </div>
                    <div className="text-xs text-gray-500 font-normal mt-1">
                      {c.provider || c.provider_name || ''} {(c.university || c.university_name) ? `• ${c.university || c.university_name}` : ''}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {/* Row: Verification */}
              <tr>
                <td className="feature-name">Verification Status</td>
                {comparisons.map((c) => (
                  <td key={c.opportunity_id}>
                    <VerificationBadge state={c.verification_status as any} />
                  </td>
                ))}
              </tr>

              {/* Row: Funding Classification */}
              <tr>
                <td className="feature-name">Funding Coverage</td>
                {comparisons.map((c) => (
                  <td key={c.opportunity_id}>
                    <FundingBadge classification={c.funding_classification as any} />
                  </td>
                ))}
              </tr>

              {/* Row: Earliest Deadline */}
              <tr>
                <td className="feature-name">Earliest Deadline</td>
                {comparisons.map((c) => (
                  <td key={c.opportunity_id}>
                    <span className="font-medium text-gray-800">
                      {c.earliest_deadline ? new Date(c.earliest_deadline).toLocaleDateString() : 'Unavailable'}
                    </span>
                    <span className="badge badge-neutral text-xs ml-1.5">{c.deadline_status}</span>
                  </td>
                ))}
              </tr>

              {/* Row: Deterministic Eligibility */}
              <tr>
                <td className="feature-name">Profile Eligibility</td>
                {comparisons.map((c) => (
                  <td key={c.opportunity_id}>
                    <EligibilityBadge status={c.eligibility_status || 'Not Evaluated'} />
                  </td>
                ))}
              </tr>

              {/* Row: Academic Alignment */}
              <tr>
                <td className="feature-name">Academic Alignment</td>
                {comparisons.map((c) => (
                  <td key={c.opportunity_id}>
                    <span className="font-semibold text-xs text-brand">
                      {c.academic_alignment || 'NOT_ASSESSABLE'}
                    </span>
                  </td>
                ))}
              </tr>

              {/* Row: Geographic Alignment */}
              <tr>
                <td className="feature-name">Geographic Alignment</td>
                {comparisons.map((c) => (
                  <td key={c.opportunity_id}>
                    <span className="font-semibold text-xs text-brand">
                      {c.geographic_alignment || 'UNKNOWN'}
                    </span>
                  </td>
                ))}
              </tr>

              {/* Row: Application Readiness */}
              <tr>
                <td className="feature-name">Application Readiness</td>
                {comparisons.map((c) => (
                  <td key={c.opportunity_id}>
                    <span className="font-semibold text-xs text-gray-800">
                      {c.application_readiness || 'LIMITED'}
                    </span>
                  </td>
                ))}
              </tr>

              {/* Row: Primary Source */}
              <tr>
                <td className="feature-name">Official Source</td>
                {comparisons.map((c) => (
                  <td key={c.opportunity_id}>
                    {c.primary_source_url ? (
                      <a
                        href={c.primary_source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-brand hover:underline inline-flex items-center gap-1"
                      >
                        Visit Source <ExternalLink className="w-3 h-3 inline" />
                      </a>
                    ) : (
                      <span className="text-xs text-gray-400">Unavailable</span>
                    )}
                  </td>
                ))}
              </tr>

              {/* Row: Actions */}
              <tr>
                <td className="feature-name">Action</td>
                {comparisons.map((c) => (
                  <td key={c.opportunity_id}>
                    <button
                      type="button"
                      className="btn-primary btn-sm w-full"
                      onClick={() => onSelectOpportunity(c.opportunity_id)}
                    >
                      View Detail & Counsel
                    </button>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
