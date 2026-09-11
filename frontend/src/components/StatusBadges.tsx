import React from 'react';
import type { VerificationState, FundingClassification, EligibilityStatus, TriState } from '../types';
import { CheckCircle2, AlertTriangle, HelpCircle, Clock, ShieldAlert, XCircle, Info } from 'lucide-react';

export const VerificationBadge: React.FC<{ state: VerificationState; showIcon?: boolean }> = ({
  state,
  showIcon = true,
}) => {
  switch (state) {
    case 'VERIFIED':
      return (
        <span className="badge badge-verified" title="Verified against primary authoritative institutional source">
          {showIcon && <CheckCircle2 className="w-3.5 h-3.5 mr-1 inline" />}
          Verified Official
        </span>
      );
    case 'PARTIALLY_VERIFIED':
      return (
        <span className="badge badge-partially-verified" title="Some facts verified, others pending verification">
          {showIcon && <AlertTriangle className="w-3.5 h-3.5 mr-1 inline" />}
          Partially Verified
        </span>
      );
    case 'CONFLICTING':
      return (
        <span className="badge badge-conflicting" title="Conflicting facts reported across independent sources">
          {showIcon && <ShieldAlert className="w-3.5 h-3.5 mr-1 inline" />}
          Conflicting Sources
        </span>
      );
    case 'OUTDATED':
      return (
        <span className="badge badge-outdated" title="Information is from a prior academic cycle">
          {showIcon && <Clock className="w-3.5 h-3.5 mr-1 inline" />}
          Outdated Cycle
        </span>
      );
    case 'SOURCE_UNAVAILABLE':
      return (
        <span className="badge badge-unavailable" title="Primary official source is currently unreachable">
          {showIcon && <AlertTriangle className="w-3.5 h-3.5 mr-1 inline" />}
          Source Unavailable
        </span>
      );
    case 'QUARANTINED_FOR_REVIEW':
      return (
        <span className="badge badge-quarantined" title="Flagged and quarantined due to anomalies">
          {showIcon && <ShieldAlert className="w-3.5 h-3.5 mr-1 inline" />}
          Quarantined for Review
        </span>
      );
    case 'UNVERIFIED':
    default:
      return (
        <span className="badge badge-unverified" title="Discovered from aggregator; official verification pending">
          {showIcon && <HelpCircle className="w-3.5 h-3.5 mr-1 inline" />}
          Unverified
        </span>
      );
  }
};

export const FundingBadge: React.FC<{ classification: FundingClassification }> = ({ classification }) => {
  switch (classification) {
    case 'FULL_FUNDING':
      return (
        <span className="badge badge-full-funding" title="Covers 100% Tuition + Living / Stipend">
          Full Funding (Tuition + Living)
        </span>
      );
    case 'FULL_TUITION':
      return (
        <span className="badge badge-full-tuition" title="Covers 100% Tuition (living expenses not included)">
          Full Tuition Only
        </span>
      );
    case 'PARTIAL_FUNDING':
      return <span className="badge badge-partial-funding">Partial Funding</span>;
    case 'STIPEND_ONLY':
      return <span className="badge badge-stipend">Stipend Only</span>;
    case 'FEES_ONLY':
      return <span className="badge badge-fees">Mandatory Fees Only</span>;
    case 'UNKNOWN':
    default:
      return <span className="badge badge-unknown">Funding Unavailable</span>;
  }
};

export const EligibilityBadge: React.FC<{ status: EligibilityStatus | string }> = ({ status }) => {
  switch (status) {
    case 'ELIGIBLE':
      return (
        <span className="badge badge-eligible">
          <CheckCircle2 className="w-3.5 h-3.5 mr-1 inline" /> Eligible
        </span>
      );
    case 'INELIGIBLE':
      return (
        <span className="badge badge-ineligible">
          <XCircle className="w-3.5 h-3.5 mr-1 inline" /> Ineligible
        </span>
      );
    case 'NEEDS_INFORMATION':
      return (
        <span className="badge badge-needs-info">
          <HelpCircle className="w-3.5 h-3.5 mr-1 inline" /> Needs Information
        </span>
      );
    case 'GATED_UNVERIFIED':
      return (
        <span className="badge badge-gated">
          <AlertTriangle className="w-3.5 h-3.5 mr-1 inline" /> Gated (Unverified Data)
        </span>
      );
    case 'NEEDS_REVIEW':
      return (
        <span className="badge badge-review">
          <Info className="w-3.5 h-3.5 mr-1 inline" /> Needs Review
        </span>
      );
    case 'OUTDATED_CYCLE':
      return (
        <span className="badge badge-outdated">
          <Clock className="w-3.5 h-3.5 mr-1 inline" /> Outdated Cycle
        </span>
      );
    default:
      return <span className="badge badge-unknown">{status || 'Not Evaluated'}</span>;
  }
};

export const TriStateBadge: React.FC<{ value: TriState; label: string }> = ({ value, label }) => {
  let badgeClass = 'badge-unknown';
  let displayVal = 'Unknown';

  if (value === 'YES') {
    badgeClass = 'badge-eligible';
    displayVal = 'Yes';
  } else if (value === 'NO') {
    badgeClass = 'badge-ineligible';
    displayVal = 'No';
  } else if (value === 'CONFLICTING') {
    badgeClass = 'badge-conflicting';
    displayVal = 'Conflicting';
  } else if (value === 'NOT_APPLICABLE') {
    badgeClass = 'badge-unverified';
    displayVal = 'N/A';
  }

  return (
    <span className={`badge ${badgeClass}`} title={`${label}: ${displayVal}`}>
      {label}: <strong>{displayVal}</strong>
    </span>
  );
};
