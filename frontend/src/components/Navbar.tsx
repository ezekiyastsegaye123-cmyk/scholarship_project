import React from 'react';
import { Compass, UserCheck, Scale, ShieldCheck, Bookmark, CheckCircle, LogIn, LogOut, User } from 'lucide-react';
import type { StudentAccount } from '../types';

export type NavTab = 'discover' | 'profile' | 'compare' | 'saved' | 'applications';

interface NavbarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  selectedCompareCount: number;
  currentUser?: StudentAccount | null;
  savedCount?: number;
  applicationsCount?: number;
  onOpenAuth?: (mode: 'login' | 'register') => void;
  onLogout?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  onSelectTab,
  selectedCompareCount,
  currentUser,
  savedCount,
  applicationsCount,
  onOpenAuth,
  onLogout,
}) => {
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

          {/* Authenticated / Student Persistence Tabs */}
          <button
            type="button"
            className={`nav-item ${currentTab === 'saved' ? 'nav-item-active' : ''}`}
            onClick={() => {
              if (!currentUser && onOpenAuth) {
                onOpenAuth('login');
              } else {
                onSelectTab('saved');
              }
            }}
          >
            <Bookmark className="w-4 h-4 mr-1.5 inline" />
            Saved
            {savedCount !== undefined && savedCount > 0 && (
              <span className="compare-badge bg-brand/80">{savedCount}</span>
            )}
          </button>

          <button
            type="button"
            className={`nav-item ${currentTab === 'applications' ? 'nav-item-active' : ''}`}
            onClick={() => {
              if (!currentUser && onOpenAuth) {
                onOpenAuth('login');
              } else {
                onSelectTab('applications');
              }
            }}
          >
            <CheckCircle className="w-4 h-4 mr-1.5 inline" />
            Tracker
            {applicationsCount !== undefined && applicationsCount > 0 && (
              <span className="compare-badge bg-emerald-600">{applicationsCount}</span>
            )}
          </button>
        </nav>

        {/* Authentication State Controls */}
        <div className="flex items-center gap-3">
          {currentUser ? (
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-600 hidden md:inline-flex items-center gap-1 font-medium bg-gray-50 px-2.5 py-1 rounded-full border border-gray-200">
                <User className="w-3.5 h-3.5 text-brand" />
                {currentUser.email}
              </span>
              <button
                type="button"
                className="btn-secondary text-xs px-2.5 py-1"
                onClick={onLogout}
                title="Sign out of student account"
              >
                <LogOut className="w-3.5 h-3.5 md:mr-1 inline" />
                <span className="hidden md:inline">Sign Out</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <button
                type="button"
                className="btn-secondary text-xs px-2.5 py-1"
                onClick={() => onOpenAuth && onOpenAuth('login')}
              >
                <LogIn className="w-3.5 h-3.5 mr-1 inline" /> Sign In
              </button>
              <button
                type="button"
                className="btn-primary text-xs px-2.5 py-1"
                onClick={() => onOpenAuth && onOpenAuth('register')}
              >
                Register
              </button>
            </div>
          )}
        </div>
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
