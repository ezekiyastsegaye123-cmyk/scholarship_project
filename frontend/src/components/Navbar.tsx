import React from 'react';
import { Compass, UserCheck, Scale, ShieldCheck } from 'lucide-react';

interface NavbarProps {
  currentTab: 'discover' | 'profile' | 'compare';
  onSelectTab: (tab: 'discover' | 'profile' | 'compare') => void;
  selectedCompareCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, onSelectTab, selectedCompareCount }) => {
  return (
    <header className="site-header">
      <div className="header-container">
        <div className="brand-section" onClick={() => onSelectTab('discover')} role="button" tabIndex={0}>
          <div className="brand-logo-container">
            <ShieldCheck className="w-6 h-6 text-brand" />
          </div>
          <div>
            <h1 className="brand-title">Scholarship Intelligence</h1>
            <p className="brand-subtitle">Deterministic Counseling & Epistemic Verification</p>
          </div>
        </div>

        <nav className="nav-menu" aria-label="Main Navigation">
          <button
            type="button"
            className={`nav-item ${currentTab === 'discover' ? 'nav-item-active' : ''}`}
            onClick={() => onSelectTab('discover')}
          >
            <Compass className="w-4 h-4 mr-1.5 inline" />
            Discover
          </button>

          <button
            type="button"
            className={`nav-item ${currentTab === 'profile' ? 'nav-item-active' : ''}`}
            onClick={() => onSelectTab('profile')}
          >
            <UserCheck className="w-4 h-4 mr-1.5 inline" />
            Student Profile
          </button>

          <button
            type="button"
            className={`nav-item ${currentTab === 'compare' ? 'nav-item-active' : ''}`}
            onClick={() => onSelectTab('compare')}
          >
            <Scale className="w-4 h-4 mr-1.5 inline" />
            Compare
            {selectedCompareCount > 0 && (
              <span className="compare-badge">{selectedCompareCount}</span>
            )}
          </button>
        </nav>
      </div>

      <div className="epistemic-banner">
        <span>Cycle 2026-2027</span>
        <span className="banner-divider">•</span>
        <span>Evidence-Backed Verification</span>
        <span className="banner-divider">•</span>
        <span>Zero Synthetic Scores or Fake Rankings</span>
      </div>
    </header>
  );
};
