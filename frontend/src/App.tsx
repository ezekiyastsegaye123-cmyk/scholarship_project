import React, { useState, useEffect, useCallback } from 'react';
import type { StudentProfile, StudentAccount } from './types';
import { Navbar, type NavTab } from './components/Navbar';
import { DiscoverPage } from './pages/DiscoverPage';
import { OpportunityDetailPage } from './pages/OpportunityDetailPage';
import { ProfilePage } from './pages/ProfilePage';
import { ComparePage } from './pages/ComparePage';
import { SavedOpportunitiesPage } from './pages/SavedOpportunitiesPage';
import { ApplicationTrackerPage } from './pages/ApplicationTrackerPage';
import { AuthModal } from './components/AuthModal';
import {
  authMe,
  authLogout,
  fetchComparisonSelections,
  addComparisonSelection,
  removeComparisonSelection,
  clearComparisonSelections,
  saveOpportunity,
  unsaveOpportunity,
  fetchSavedOpportunities,
  fetchApplications,
  getAuthToken,
} from './api/client';
import './App.css';

const DEFAULT_PROFILE: StudentProfile = {
  degree_level: 'UNDERGRADUATE',
  gpa: 3.8,
  gpa_scale: 4.0,
  citizenship_country: 'ET',
  country_of_residence: 'ET',
  us_state: null,
  intended_major: 'Computer Science',
  sat_total: 1450,
  act_composite: null,
  toefl_total: 105,
  ielts_overall: null,
  financial_need_tier: 'HIGH',
  has_leadership_experience: true,
  has_community_service: true,
  first_generation_college_student: false,
  prepared_components: ['TRANSCRIPT', 'RECOMMENDATION', 'ESSAY'],
  target_academic_cycle: '2026-2027',
};

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavTab>('discover');
  const [selectedOpportunityId, setSelectedOpportunityId] = useState<string | null>(null);

  // Authentication State
  const [currentUser, setCurrentUser] = useState<StudentAccount | null>(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);
  const [authModalMode, setAuthModalMode] = useState<'login' | 'register'>('login');

  // Comparison State
  const [comparedIds, setComparedIds] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem('scholarship_compare_ids');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  // Saved Opportunities & Applications counts
  const [savedIds, setSavedIds] = useState<string[]>([]);
  const [applicationsCount, setApplicationsCount] = useState<number>(0);
  const [trackOppId, setTrackOppId] = useState<string | null>(null);

  const [studentProfile, setStudentProfile] = useState<StudentProfile>(() => {
    try {
      const saved = localStorage.getItem('scholarship_student_profile');
      return saved ? JSON.parse(saved) : DEFAULT_PROFILE;
    } catch {
      return DEFAULT_PROFILE;
    }
  });

  // Session restoration on mount
  useEffect(() => {
    const token = getAuthToken();
    if (token) {
      authMe()
        .then((account) => {
          setCurrentUser(account);
        })
        .catch(() => {
          setCurrentUser(null);
        });
    }
  }, []);

  // Sync authenticated user data (comparisons, saved IDs, applications count)
  const syncUserData = useCallback(async () => {
    if (!currentUser) return;
    try {
      const [compRes, savedRes, appsRes] = await Promise.all([
        fetchComparisonSelections().catch(() => null),
        fetchSavedOpportunities(1, 100).catch(() => null),
        fetchApplications(1, 1).catch(() => null),
      ]);

      if (compRes) {
        const ids = compRes.items.map((it) => it.opportunity_id);
        setComparedIds(ids);
      }
      if (savedRes) {
        setSavedIds(savedRes.items.map((it) => it.opportunity_id));
      }
      if (appsRes) {
        setApplicationsCount(appsRes.total);
      }
    } catch (e) {
      console.error('Failed to sync authenticated user data', e);
    }
  }, [currentUser]);

  useEffect(() => {
    if (currentUser) {
      syncUserData();
    }
  }, [currentUser, syncUserData]);

  // Persist local comparisons when unauthenticated
  useEffect(() => {
    if (!currentUser) {
      try {
        localStorage.setItem('scholarship_compare_ids', JSON.stringify(comparedIds));
      } catch (e) {
        console.error('Failed to save compare IDs to localStorage', e);
      }
    }
  }, [comparedIds, currentUser]);

  const handleSaveProfile = (profile: StudentProfile) => {
    setStudentProfile(profile);
    try {
      localStorage.setItem('scholarship_student_profile', JSON.stringify(profile));
    } catch (e) {
      console.error('Failed to save profile to localStorage', e);
    }
  };

  const handleToggleCompare = async (id: string) => {
    if (currentUser) {
      if (comparedIds.includes(id)) {
        try {
          const res = await removeComparisonSelection(id);
          setComparedIds(res.items.map((it) => it.opportunity_id));
        } catch (err) {
          alert(err instanceof Error ? err.message : 'Failed to update comparison');
        }
      } else {
        if (comparedIds.length >= 4) {
          alert('You can compare a maximum of 4 scholarships simultaneously.');
          return;
        }
        try {
          const res = await addComparisonSelection(id);
          setComparedIds(res.items.map((it) => it.opportunity_id));
        } catch (err) {
          alert(err instanceof Error ? err.message : 'Failed to update comparison');
        }
      }
    } else {
      setComparedIds((prev) => {
        if (prev.includes(id)) {
          return prev.filter((item) => item !== id);
        } else {
          if (prev.length >= 4) {
            alert('You can compare a maximum of 4 scholarships simultaneously.');
            return prev;
          }
          return [...prev, id];
        }
      });
    }
  };

  const handleRemoveFromCompare = async (id: string) => {
    if (currentUser) {
      try {
        const res = await removeComparisonSelection(id);
        setComparedIds(res.items.map((it) => it.opportunity_id));
      } catch (err) {
        alert(err instanceof Error ? err.message : 'Failed to remove from comparison');
      }
    } else {
      setComparedIds((prev) => prev.filter((item) => item !== id));
    }
  };

  const handleClearCompare = async () => {
    if (currentUser) {
      try {
        await clearComparisonSelections();
        setComparedIds([]);
      } catch (err) {
        alert(err instanceof Error ? err.message : 'Failed to clear comparisons');
      }
    } else {
      setComparedIds([]);
    }
  };

  const handleToggleSave = async (id: string) => {
    if (!currentUser) {
      setAuthModalMode('login');
      setIsAuthModalOpen(true);
      return;
    }

    if (savedIds.includes(id)) {
      try {
        await unsaveOpportunity(id);
        setSavedIds((prev) => prev.filter((item) => item !== id));
      } catch (err) {
        alert(err instanceof Error ? err.message : 'Failed to unsave scholarship');
      }
    } else {
      try {
        await saveOpportunity(id);
        setSavedIds((prev) => [...prev, id]);
      } catch (err) {
        alert(err instanceof Error ? err.message : 'Failed to save scholarship');
      }
    }
  };

  const handleTrackApplication = (id: string) => {
    if (!currentUser) {
      setAuthModalMode('login');
      setIsAuthModalOpen(true);
      return;
    }
    setTrackOppId(id);
    setSelectedOpportunityId(null);
    setCurrentTab('applications');
  };

  const handleSelectOpportunity = (id: string) => {
    setSelectedOpportunityId(id);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleBackToDiscover = () => {
    setSelectedOpportunityId(null);
    setCurrentTab('discover');
  };

  const handleLogout = async () => {
    await authLogout();
    setCurrentUser(null);
    setSavedIds([]);
    setApplicationsCount(0);
    if (currentTab === 'saved' || currentTab === 'applications') {
      setCurrentTab('discover');
    }
  };

  return (
    <div className="app-layout">
      <Navbar
        currentTab={currentTab}
        onSelectTab={(tab) => {
          setSelectedOpportunityId(null);
          setCurrentTab(tab);
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }}
        selectedCompareCount={comparedIds.length}
        currentUser={currentUser}
        savedCount={savedIds.length}
        applicationsCount={applicationsCount}
        onOpenAuth={(mode) => {
          setAuthModalMode(mode);
          setIsAuthModalOpen(true);
        }}
        onLogout={handleLogout}
      />

      <main className="main-content" id="main-content">
        {selectedOpportunityId ? (
          <OpportunityDetailPage
            opportunityId={selectedOpportunityId}
            onBack={handleBackToDiscover}
            studentProfile={studentProfile}
            isCompared={comparedIds.includes(selectedOpportunityId)}
            onToggleCompare={handleToggleCompare}
            onGoToProfile={() => {
              setSelectedOpportunityId(null);
              setCurrentTab('profile');
            }}
            isSaved={savedIds.includes(selectedOpportunityId)}
            onToggleSave={handleToggleSave}
            onTrackApplication={handleTrackApplication}
            isAuthenticated={!!currentUser}
            onOpenAuthModal={() => setIsAuthModalOpen(true)}
          />
        ) : currentTab === 'discover' ? (
          <DiscoverPage
            onSelectOpportunity={handleSelectOpportunity}
            comparedIds={comparedIds}
            onToggleCompare={handleToggleCompare}
            onGoToCompare={() => setCurrentTab('compare')}
          />
        ) : currentTab === 'profile' ? (
          <ProfilePage
            profile={studentProfile}
            onSaveProfile={handleSaveProfile}
            onGoToDiscover={() => setCurrentTab('discover')}
          />
        ) : currentTab === 'compare' ? (
          <ComparePage
            opportunityIds={comparedIds}
            studentProfile={studentProfile}
            onRemoveFromCompare={handleRemoveFromCompare}
            onClearAll={handleClearCompare}
            onGoToDiscover={() => setCurrentTab('discover')}
            onSelectOpportunity={handleSelectOpportunity}
          />
        ) : currentTab === 'saved' ? (
          <SavedOpportunitiesPage
            onSelectOpportunity={handleSelectOpportunity}
            onGoToDiscover={() => setCurrentTab('discover')}
            onTrackApplication={handleTrackApplication}
          />
        ) : currentTab === 'applications' ? (
          <ApplicationTrackerPage
            onSelectOpportunity={handleSelectOpportunity}
            onGoToDiscover={() => setCurrentTab('discover')}
            initialAddOpportunityId={trackOppId}
          />
        ) : null}
      </main>

      <footer className="site-footer">
        <div className="footer-container">
          <div className="footer-col">
            <h5 className="font-semibold text-gray-800 text-sm">Scholarship Intelligence & Counselor</h5>
            <p className="text-xs text-gray-500 mt-1">
              Deterministic, evidence-backed counseling platform built for ethical, transparent student guidance.
            </p>
          </div>
          <div className="footer-col">
            <h5 className="font-semibold text-gray-800 text-sm">Epistemic Guarantees</h5>
            <p className="text-xs text-gray-500 mt-1">
              Verified institutional authority • Gated unverified facts • Zero admission chances or fake rankings.
            </p>
          </div>
        </div>
      </footer>

      {/* Authentication Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        initialMode={authModalMode}
        onClose={() => setIsAuthModalOpen(false)}
        onAuthSuccess={(account) => {
          setCurrentUser(account);
        }}
      />
    </div>
  );
};

export default App;
