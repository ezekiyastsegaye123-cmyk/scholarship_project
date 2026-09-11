import React from 'react';
import type { OpportunitySummary } from '../types';
import { VerificationBadge, FundingBadge, TriStateBadge, FreshnessBadge } from './StatusBadges';
import { Calendar, Globe, Building2, GraduationCap, ArrowRight, CheckSquare, Square } from 'lucide-react';

interface OpportunityCardProps {
  opportunity: OpportunitySummary;
  onSelect: (id: string) => void;
  isCompared: boolean;
  onToggleCompare: (id: string) => void;
}

export const OpportunityCard: React.FC<OpportunityCardProps> = ({
  opportunity,
  onSelect,
  isCompared,
  onToggleCompare,
}) => {
  const formatDeadline = (dateStr: string | null, status: string) => {
    if (!dateStr) {
      if (status === 'ROLLING') return 'Rolling Admissions';
      return 'Information unavailable';
    }
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  return (
    <article className="opp-card" data-testid={`opp-card-${opportunity.id}`}>
      <div className="opp-card-header">
        <div className="opp-meta-row">
          <div className="flex items-center gap-1.5 flex-wrap">
            <VerificationBadge state={opportunity.verification_status} />
            <FreshnessBadge level={opportunity.freshness_level} message={opportunity.freshness_message} />
          </div>
          <button
            type="button"
            className={`compare-toggle-btn ${isCompared ? 'compared-active' : ''}`}
            onClick={(e) => {
              e.stopPropagation();
              onToggleCompare(opportunity.id);
            }}
            aria-label={isCompared ? 'Remove from comparison' : 'Add to comparison'}
          >
            {isCompared ? (
              <>
                <CheckSquare className="w-4 h-4 text-brand inline mr-1" />
                <span className="text-xs font-semibold">Comparing</span>
              </>
            ) : (
              <>
                <Square className="w-4 h-4 text-gray-400 inline mr-1" />
                <span className="text-xs text-gray-600">Compare</span>
              </>
            )}
          </button>
        </div>

        <h3 className="opp-title" onClick={() => onSelect(opportunity.id)}>
          {opportunity.title}
        </h3>

        <div className="opp-entities">
          {opportunity.provider_name && (
            <span className="opp-entity">
              <Building2 className="w-3.5 h-3.5 inline mr-1 text-gray-500" />
              {opportunity.provider_name}
            </span>
          )}
          {opportunity.university_name && (
            <span className="opp-entity">
              <GraduationCap className="w-3.5 h-3.5 inline mr-1 text-gray-500" />
              {opportunity.university_name}
            </span>
          )}
        </div>
      </div>

      <div className="opp-card-body">
        <div className="opp-section">
          <div className="section-label">Funding</div>
          <div className="funding-row">
            <FundingBadge classification={opportunity.funding_classification} />
            <span className="funding-summary-text">{opportunity.funding_summary}</span>
          </div>
        </div>

        <div className="opp-details-grid">
          <div className="detail-item">
            <span className="detail-label">
              <Calendar className="w-3.5 h-3.5 inline mr-1 text-gray-500" />
              Earliest Deadline
            </span>
            <span className="detail-value font-medium">
              {formatDeadline(opportunity.earliest_deadline, opportunity.deadline_status)}
            </span>
          </div>

          <div className="detail-item">
            <span className="detail-label">
              <Globe className="w-3.5 h-3.5 inline mr-1 text-gray-500" />
              Degree Level
            </span>
            <span className="detail-value">
              {(opportunity.target_degree_level || opportunity.degree_level || 'UNDERGRADUATE').replace('_', ' ')}
            </span>
          </div>
        </div>

        <div className="opp-flags-row">
          <TriStateBadge
            value={opportunity.international_students_allowed}
            label="International Students"
          />
          <TriStateBadge
            value={opportunity.financial_need_required}
            label="Need-Based"
          />
        </div>
      </div>

      <div className="opp-card-footer">
        <button
          type="button"
          className="btn-view-details"
          onClick={() => onSelect(opportunity.id)}
        >
          View Details & Counselor Evaluation
          <ArrowRight className="w-4 h-4 ml-1 inline" />
        </button>
      </div>
    </article>
  );
};
