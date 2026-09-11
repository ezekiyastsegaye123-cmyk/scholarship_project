import React, { useState } from 'react';
import type { StudentProfile } from '../types';
import { submitStudentProfile } from '../api/client';
import { ShieldCheck, UserCheck, Save, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

interface ProfilePageProps {
  profile: StudentProfile;
  onSaveProfile: (profile: StudentProfile) => void;
  onGoToDiscover: () => void;
}

const PREPARATION_OPTIONS = [
  { id: 'TRANSCRIPT', label: 'Official / Unofficial Transcripts Prepared' },
  { id: 'RECOMMENDATION', label: 'Letters of Recommendation Secured' },
  { id: 'ESSAY', label: 'Personal Statement / Scholarship Essays Drafted' },
  { id: 'STANDARDIZED_TEST', label: 'Official Standardized Test Scores Available' },
  { id: 'ENGLISH_PROFICIENCY', label: 'English Proficiency Exam Passed & Score Report Ready' },
  { id: 'CSS_PROFILE', label: 'CSS Profile Completed / Verified' },
  { id: 'FINANCIAL_DOCUMENTS', label: 'Financial Need Documentation Ready' },
  { id: 'PORTFOLIO', label: 'Creative / Academic Portfolio Prepared' },
];

export const ProfilePage: React.FC<ProfilePageProps> = ({
  profile: initialProfile,
  onSaveProfile,
  onGoToDiscover,
}) => {
  const [form, setForm] = useState<StudentProfile>(initialProfile);
  const [saving, setSaving] = useState<boolean>(false);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const handleTogglePrepared = (componentId: string) => {
    setForm((prev) => {
      const exists = prev.prepared_components.includes(componentId);
      const updated = exists
        ? prev.prepared_components.filter((c) => c !== componentId)
        : [...prev.prepared_components, componentId];
      return { ...prev, prepared_components: updated };
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaveSuccess(false);
    setSaveError(null);

    try {
      // Validate via backend endpoint to confirm privacy & schema constraints
      const validated = await submitStudentProfile(form);
      onSaveProfile(validated);
      setSaveSuccess(true);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Failed to validate profile');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page-container profile-container">
      {/* Privacy Guarantee Banner */}
      <section className="privacy-banner" aria-label="Privacy Assurances">
        <div className="flex items-start gap-3">
          <ShieldCheck className="w-6 h-6 text-brand shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-brand-dark">Student Privacy Guarantee</h4>
            <p className="text-xs text-brand-muted mt-0.5">
              This platform uses strict privacy controls. We <strong>never</strong> ask for, store, or infer sensitive data such as Social Security Numbers, bank details, passwords, tax filings, or identity document uploads. Your profile is preserved locally and evaluated deterministically.
            </p>
          </div>
        </div>
      </section>

      <div className="profile-header-bar mt-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Student Counseling Profile</h2>
          <p className="text-sm text-gray-600">
            Define your academic background and readiness checklist to generate accurate eligibility evaluations.
          </p>
        </div>
      </div>

      {saveSuccess && (
        <div className="alert-box success-alert mt-4">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 inline mr-2" />
          <span>Profile validated and saved successfully! You can now browse opportunities tailored to your criteria.</span>
        </div>
      )}

      {saveError && (
        <div className="alert-box error-alert mt-4">
          <AlertCircle className="w-4 h-4 text-red-600 inline mr-2" />
          <span>{saveError}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="profile-form mt-6">
        {/* Section 1: Academic Background */}
        <fieldset className="form-fieldset">
          <legend className="form-legend">
            <UserCheck className="w-4 h-4 mr-2 inline text-brand" />
            1. Academic Background
          </legend>

          <div className="form-grid-2">
            <div className="form-field">
              <label htmlFor="degree_level" className="field-label">Current / Target Degree Level *</label>
              <select
                id="degree_level"
                className="form-input"
                value={form.degree_level}
                onChange={(e) => setForm({ ...form, degree_level: e.target.value })}
                required
              >
                <option value="UNDERGRADUATE">Undergraduate (Bachelor's)</option>
                <option value="GRADUATE">Graduate (Master's / Doctoral)</option>
                <option value="POSTGRADUATE">Postgraduate / Postdoctoral</option>
                <option value="HIGH_SCHOOL">High School Senior</option>
              </select>
            </div>

            <div className="form-field">
              <label htmlFor="intended_major" className="field-label">Intended Major / Field of Study</label>
              <input
                id="intended_major"
                type="text"
                className="form-input"
                placeholder="e.g. Computer Science, Public Policy, Biology"
                value={form.intended_major || ''}
                onChange={(e) => setForm({ ...form, intended_major: e.target.value || null })}
              />
            </div>

            <div className="form-field">
              <label htmlFor="gpa" className="field-label">Cumulative GPA (if known)</label>
              <input
                id="gpa"
                type="number"
                step="0.01"
                min="0"
                max={form.gpa_scale}
                className="form-input"
                placeholder="e.g. 3.85"
                value={form.gpa !== null && form.gpa !== undefined ? form.gpa : ''}
                onChange={(e) => {
                  const val = e.target.value ? parseFloat(e.target.value) : null;
                  setForm({ ...form, gpa: val });
                }}
              />
            </div>

            <div className="form-field">
              <label htmlFor="gpa_scale" className="field-label">GPA Scale</label>
              <select
                id="gpa_scale"
                className="form-input"
                value={form.gpa_scale}
                onChange={(e) => setForm({ ...form, gpa_scale: parseFloat(e.target.value) })}
              >
                <option value="4.0">4.0 Scale</option>
                <option value="5.0">5.0 Scale</option>
                <option value="10.0">10.0 Scale</option>
                <option value="100.0">100.0 (Percentage)</option>
              </select>
            </div>
          </div>
        </fieldset>

        {/* Section 2: Citizenship & Geography */}
        <fieldset className="form-fieldset">
          <legend className="form-legend">2. Citizenship & Residence</legend>

          <div className="form-grid-3">
            <div className="form-field">
              <label htmlFor="citizenship_country" className="field-label">Citizenship Country (ISO 2-letter) *</label>
              <input
                id="citizenship_country"
                type="text"
                maxLength={2}
                className="form-input font-mono uppercase"
                placeholder="e.g. US, IN, ET, CA, GB"
                value={form.citizenship_country}
                onChange={(e) => setForm({ ...form, citizenship_country: e.target.value.toUpperCase() })}
                required
              />
            </div>

            <div className="form-field">
              <label htmlFor="country_of_residence" className="field-label">Country of Residence *</label>
              <input
                id="country_of_residence"
                type="text"
                maxLength={2}
                className="form-input font-mono uppercase"
                placeholder="e.g. US, IN, ET"
                value={form.country_of_residence}
                onChange={(e) => setForm({ ...form, country_of_residence: e.target.value.toUpperCase() })}
                required
              />
            </div>

            <div className="form-field">
              <label htmlFor="us_state" className="field-label">US State (if applicable)</label>
              <input
                id="us_state"
                type="text"
                maxLength={2}
                className="form-input font-mono uppercase"
                placeholder="e.g. CA, NY, TX"
                value={form.us_state || ''}
                onChange={(e) => setForm({ ...form, us_state: e.target.value.toUpperCase() || null })}
              />
            </div>
          </div>
        </fieldset>

        {/* Section 3: Standardized Testing & Language */}
        <fieldset className="form-fieldset">
          <legend className="form-legend">3. Standardized Tests & English Proficiency</legend>

          <div className="form-grid-4">
            <div className="form-field">
              <label htmlFor="sat_total" className="field-label">SAT Total (400-1600)</label>
              <input
                id="sat_total"
                type="number"
                min="400"
                max="1600"
                className="form-input"
                placeholder="e.g. 1450"
                value={form.sat_total || ''}
                onChange={(e) => setForm({ ...form, sat_total: e.target.value ? parseInt(e.target.value, 10) : null })}
              />
            </div>

            <div className="form-field">
              <label htmlFor="act_composite" className="field-label">ACT Composite (1-36)</label>
              <input
                id="act_composite"
                type="number"
                min="1"
                max="36"
                className="form-input"
                placeholder="e.g. 33"
                value={form.act_composite || ''}
                onChange={(e) => setForm({ ...form, act_composite: e.target.value ? parseInt(e.target.value, 10) : null })}
              />
            </div>

            <div className="form-field">
              <label htmlFor="toefl_total" className="field-label">TOEFL iBT (0-120)</label>
              <input
                id="toefl_total"
                type="number"
                min="0"
                max="120"
                className="form-input"
                placeholder="e.g. 105"
                value={form.toefl_total || ''}
                onChange={(e) => setForm({ ...form, toefl_total: e.target.value ? parseInt(e.target.value, 10) : null })}
              />
            </div>

            <div className="form-field">
              <label htmlFor="ielts_overall" className="field-label">IELTS (0-9.0)</label>
              <input
                id="ielts_overall"
                type="number"
                step="0.5"
                min="0"
                max="9.0"
                className="form-input"
                placeholder="e.g. 7.5"
                value={form.ielts_overall || ''}
                onChange={(e) => setForm({ ...form, ielts_overall: e.target.value ? parseFloat(e.target.value) : null })}
              />
            </div>
          </div>
        </fieldset>

        {/* Section 4: Application Readiness Checklist */}
        <fieldset className="form-fieldset">
          <legend className="form-legend">4. Application Preparation Checklist</legend>
          <p className="text-xs text-gray-500 mb-3">
            Explicitly mark items you have currently completed or prepared. We do not infer readiness.
          </p>

          <div className="form-grid-2">
            {PREPARATION_OPTIONS.map((opt) => {
              const isChecked = form.prepared_components.includes(opt.id);
              return (
                <label key={opt.id} className="checklist-box-label">
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => handleTogglePrepared(opt.id)}
                  />
                  <span className="text-sm text-gray-700">{opt.label}</span>
                </label>
              );
            })}
          </div>
        </fieldset>

        {/* Section 5: Need & Demographic Background */}
        <fieldset className="form-fieldset">
          <legend className="form-legend">5. Financial Need & Background Indicators</legend>

          <div className="form-grid-2">
            <div className="form-field">
              <label htmlFor="need_tier" className="field-label">Demonstrated Financial Need Level</label>
              <select
                id="need_tier"
                className="form-input"
                value={form.financial_need_tier || ''}
                onChange={(e) => setForm({ ...form, financial_need_tier: e.target.value || null })}
              >
                <option value="">Not Disclosed / Unknown</option>
                <option value="HIGH">High Demonstrated Need</option>
                <option value="MODERATE">Moderate Need</option>
                <option value="LOW">Low Need</option>
                <option value="NONE">No Financial Need</option>
              </select>
            </div>

            <div className="form-field">
              <span className="field-label">Self-Reported Factors</span>
              <div className="space-y-2 mt-2">
                <label className="checkbox-label text-sm text-gray-700 block">
                  <input
                    type="checkbox"
                    checked={form.first_generation_college_student}
                    onChange={(e) => setForm({ ...form, first_generation_college_student: e.target.checked })}
                  />
                  <span className="ml-2">First-Generation College Student</span>
                </label>
                <label className="checkbox-label text-sm text-gray-700 block">
                  <input
                    type="checkbox"
                    checked={form.has_leadership_experience}
                    onChange={(e) => setForm({ ...form, has_leadership_experience: e.target.checked })}
                  />
                  <span className="ml-2">Demonstrated Leadership Experience</span>
                </label>
                <label className="checkbox-label text-sm text-gray-700 block">
                  <input
                    type="checkbox"
                    checked={form.has_community_service}
                    onChange={(e) => setForm({ ...form, has_community_service: e.target.checked })}
                  />
                  <span className="ml-2">Community Service / Volunteer Experience</span>
                </label>
              </div>
            </div>
          </div>
        </fieldset>

        <div className="form-action-bar">
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? (
              <>
                <Loader2 className="w-4 h-4 mr-1 animate-spin inline" /> Saving Profile...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-1 inline" /> Save & Apply Profile
              </>
            )}
          </button>
          <button type="button" className="btn-secondary" onClick={onGoToDiscover}>
            Browse Scholarships
          </button>
        </div>
      </form>
    </div>
  );
};
