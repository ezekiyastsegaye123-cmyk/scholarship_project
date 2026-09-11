import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import {
  VerificationBadge,
  FundingBadge,
  EligibilityBadge,
  TriStateBadge,
} from '../components/StatusBadges';

describe('StatusBadges Component', () => {
  it('renders verification badges correctly for distinct states', () => {
    const { rerender } = render(<VerificationBadge state="VERIFIED" />);
    expect(screen.getByText(/Verified Official/i)).toBeInTheDocument();

    rerender(<VerificationBadge state="PARTIALLY_VERIFIED" />);
    expect(screen.getByText(/Partially Verified/i)).toBeInTheDocument();

    rerender(<VerificationBadge state="CONFLICTING" />);
    expect(screen.getByText(/Conflicting Sources/i)).toBeInTheDocument();

    rerender(<VerificationBadge state="UNVERIFIED" />);
    expect(screen.getByText(/Unverified/i)).toBeInTheDocument();
  });

  it('distinguishes Full Funding from Full Tuition', () => {
    const { rerender } = render(<FundingBadge classification="FULL_FUNDING" />);
    expect(screen.getByText(/Full Funding \(Tuition \+ Living\)/i)).toBeInTheDocument();

    rerender(<FundingBadge classification="FULL_TUITION" />);
    expect(screen.getByText(/Full Tuition Only/i)).toBeInTheDocument();
    expect(screen.queryByText(/Tuition \+ Living/i)).not.toBeInTheDocument();

    rerender(<FundingBadge classification="UNKNOWN" />);
    expect(screen.getByText(/Funding Unavailable/i)).toBeInTheDocument();
  });

  it('renders eligibility badges with distinct states', () => {
    const { rerender } = render(<EligibilityBadge status="ELIGIBLE" />);
    expect(screen.getByText(/Eligible/i)).toBeInTheDocument();

    rerender(<EligibilityBadge status="INELIGIBLE" />);
    expect(screen.getByText(/Ineligible/i)).toBeInTheDocument();

    rerender(<EligibilityBadge status="NEEDS_INFORMATION" />);
    expect(screen.getByText(/Needs Information/i)).toBeInTheDocument();

    rerender(<EligibilityBadge status="GATED_UNVERIFIED" />);
    expect(screen.getByText(/Gated \(Unverified Data\)/i)).toBeInTheDocument();
  });

  it('preserves tri-state semantics without collapsing UNKNOWN to NO', () => {
    const { rerender } = render(<TriStateBadge value="YES" label="Test Requirement" />);
    expect(screen.getByText(/Test Requirement/i)).toBeInTheDocument();
    expect(screen.getByText('Yes')).toBeInTheDocument();

    rerender(<TriStateBadge value="NO" label="Test Requirement" />);
    expect(screen.getByText('No')).toBeInTheDocument();

    rerender(<TriStateBadge value="UNKNOWN" label="Test Requirement" />);
    expect(screen.getByText('Unknown')).toBeInTheDocument();
    expect(screen.queryByText('No')).not.toBeInTheDocument();

    rerender(<TriStateBadge value="CONFLICTING" label="Test Requirement" />);
    expect(screen.getByText('Conflicting')).toBeInTheDocument();
  });
});
