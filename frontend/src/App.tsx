import React, { useState, useEffect } from 'react';
import type { StudentProfile } from './types';
import { Navbar } from './components/Navbar';
import { DiscoverPage } from './pages/DiscoverPage';
import { OpportunityDetailPage } from './pages/OpportunityDetailPage';
import { ProfilePage } from './pages/ProfilePage';
import { ComparePage } from './pages/ComparePage';
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
  const [currentTab, setCurrentTab] = useState<'discover' | 'profile' | 'compare'>('discover');
  const [selectedOpportunityId, setSelectedOpportunityId] = useState<string | null>(null);
  const [comparedIds, setComparedIds] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem('scholarship_compare_ids');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [studentProfile, setStudentProfile] = useState<StudentProfile>(() => {
    try {
      const saved = localStorage.getItem('scholarship_student_profile');
      return saved ? JSON.parse(saved) : DEFAULT_PROFILE;
    } catch {
      return DEFAULT_PROFILE;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem('scholarship_compare_ids', JSON.stringify(comparedIds));
    } catch (e) {
      console.error('Failed to save compare IDs to localStorage', e);
    }
  }, [comparedIds]);

  const handleSaveProfile = (profile: StudentProfile) => {
    setStudentProfile(profile);
    try {
      localStorage.setItem('scholarship_student_profile', JSON.stringify(profile));
    } catch (e) {
      console.error('Failed to save profile to localStorage', e);
    }
  };

  const handleToggleCompare = (id: string) => {
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
  };

  const handleRemoveFromCompare = (id: string) => {
    setComparedIds((prev) => prev.filter((item) => item !== id));
  };

  const handleClearCompare = () => {
    setComparedIds([]);
  };

  const handleSelectOpportunity = (id: string) => {
    setSelectedOpportunityId(id);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleBackToDiscover = () => {
    setSelectedOpportunityId(null);
    setCurrentTab('discover');
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
    </div>
  );
};

export default App;
