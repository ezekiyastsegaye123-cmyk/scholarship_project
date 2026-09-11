import React, { useState, useEffect, useCallback } from 'react';
import type { ApplicationRecord, ApplicationStatus } from '../types';
import {
  fetchApplications,
  updateApplication,
  deleteApplication,
  createApplication,
  fetchOpportunities,
  ApiError,
} from '../api/client';
import { VerificationBadge, FreshnessBadge } from '../components/StatusBadges';
import {
  CheckCircle,
  FileText,
  Trash2,
  Edit2,
  Save,
  X,
  Plus,
  Loader2,
  AlertCircle,
  Building2,
  Calendar,
  Compass,
} from 'lucide-react';

const STATUS_LABELS: Record<ApplicationStatus, string> = {
  NOT_STARTED: 'Not Started',
  PLANNING: 'Planning',
  IN_PROGRESS: 'In Progress',
  SUBMITTED: 'Submitted',
  WITHDRAWN: 'Withdrawn',
  DECISION_RECEIVED: 'Decision Received',
};

const STATUS_COLORS: Record<ApplicationStatus, string> = {
  NOT_STARTED: 'bg-gray-100 text-gray-700 border-gray-300',
  PLANNING: 'bg-blue-50 text-blue-700 border-blue-200',
  IN_PROGRESS: 'bg-amber-50 text-amber-700 border-amber-200',
  SUBMITTED: 'bg-purple-50 text-purple-700 border-purple-200',
  WITHDRAWN: 'bg-gray-200 text-gray-600 border-gray-300',
  DECISION_RECEIVED: 'bg-emerald-50 text-emerald-700 border-emerald-200',
};

interface ApplicationTrackerPageProps {
  onSelectOpportunity: (id: string) => void;
  onGoToDiscover: () => void;
  initialAddOpportunityId?: string | null;
}

export const ApplicationTrackerPage: React.FC<ApplicationTrackerPageProps> = ({
  onSelectOpportunity,
  onGoToDiscover,
  initialAddOpportunityId,
}) => {
  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<ApplicationStatus | 'ALL'>('ALL');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<{
    status: ApplicationStatus;
    student_notes: string;
    target_academic_cycle: string;
    planned_submission_date: string;
    actual_submission_date: string;
  }>({
    status: 'NOT_STARTED',
    student_notes: '',
    target_academic_cycle: '2026-2027',
    planned_submission_date: '',
    actual_submission_date: '',
  });
  const [savingEdit, setSavingEdit] = useState<boolean>(false);
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [searchOppTerm, setSearchOppTerm] = useState<string>('');
  const [availableOpps, setAvailableOpps] = useState<Array<{ id: string; title: string; university_name: string | null }>>([]);
  const [searchingOpps, setSearchingOpps] = useState<boolean>(false);
  const [newOppId, setNewOppId] = useState<string>(initialAddOpportunityId || '');

  const loadApplications = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchApplications(1, 100, statusFilter === 'ALL' ? undefined : statusFilter);
      setApplications(res.items);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to load scholarship applications. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    loadApplications();
  }, [loadApplications]);

  useEffect(() => {
    if (initialAddOpportunityId) {
      setShowAddModal(true);
      setNewOppId(initialAddOpportunityId);
    }
  }, [initialAddOpportunityId]);

  const handleStartEdit = (app: ApplicationRecord) => {
    setEditingId(app.id);
    setEditForm({
      status: app.status,
      student_notes: app.student_notes || '',
      target_academic_cycle: app.target_academic_cycle || '2026-2027',
      planned_submission_date: app.planned_submission_date || '',
      actual_submission_date: app.actual_submission_date || '',
    });
  };

  const handleSaveEdit = async (appId: string) => {
    setSavingEdit(true);
    try {
      const updated = await updateApplication(appId, {
        status: editForm.status,
        student_notes: editForm.student_notes || null,
        target_academic_cycle: editForm.target_academic_cycle || null,
        planned_submission_date: editForm.planned_submission_date || null,
        actual_submission_date: editForm.actual_submission_date || null,
      });
      setApplications((prev) => prev.map((item) => (item.id === appId ? updated : item)));
      setEditingId(null);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update application');
    } finally {
      setSavingEdit(false);
    }
  };

  const handleDelete = async (appId: string, oppTitle: string) => {
    if (!window.confirm(`Are you sure you want to delete the application record for "${oppTitle}"?`)) {
      return;
    }
    try {
      await deleteApplication(appId);
      setApplications((prev) => prev.filter((item) => item.id !== appId));
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete application');
    }
  };

  const handleSearchOpps = async (term: string) => {
    setSearchOppTerm(term);
    if (!term.trim()) {
      setAvailableOpps([]);
      return;
    }
    setSearchingOpps(true);
    try {
      const res = await fetchOpportunities({ search: term, page_size: 10 });
      setAvailableOpps(
        res.items.map((o) => ({
          id: o.id,
          title: o.title,
          university_name: o.university_name,
        }))
      );
    } catch {
      // Ignore search error
    } finally {
      setSearchingOpps(false);
    }
  };

  const handleCreateApplication = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newOppId) return;
    try {
      const created = await createApplication({
        opportunity_id: newOppId,
        status: 'PLANNING',
        target_academic_cycle: '2026-2027',
      });
      setApplications((prev) => [created, ...prev]);
      setShowAddModal(false);
      setNewOppId('');
      setSearchOppTerm('');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to create application');
    }
  };

  if (loading) {
    return (
      <div className="page-container flex justify-center items-center py-20">
        <Loader2 className="w-8 h-8 text-brand animate-spin" />
        <span className="ml-3 text-gray-600 font-medium">Loading your applications...</span>
      </div>
    );
  }

  return (
    <div className="page-container tracker-page-container">
      {/* Header */}
      <div className="page-header flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2">
            <CheckCircle className="w-6 h-6 text-brand" />
            <h1 className="text-2xl font-bold text-gray-900">Application Tracker</h1>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Track deadlines, submission status, and personal preparation notes without arbitrary match scores.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="btn-primary text-xs"
            onClick={() => setShowAddModal(true)}
          >
            <Plus className="w-3.5 h-3.5 mr-1 inline" /> Track New Scholarship
          </button>
        </div>
      </div>

      {/* Status Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-3 mb-6 border-b border-gray-200">
        {(['ALL', 'NOT_STARTED', 'PLANNING', 'IN_PROGRESS', 'SUBMITTED', 'WITHDRAWN', 'DECISION_RECEIVED'] as const).map(
          (status) => (
            <button
              key={status}
              type="button"
              className={`px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-colors ${
                statusFilter === status
                  ? 'bg-brand text-white shadow-sm'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
              onClick={() => setStatusFilter(status)}
            >
              {status === 'ALL' ? 'All Applications' : STATUS_LABELS[status]}
              {status === 'ALL' && ` (${applications.length})`}
            </button>
          )
        )}
      </div>

      {error && (
        <div className="banner-alert banner-alert-error mb-6" role="alert">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="font-semibold text-sm">Failed to retrieve applications</h3>
            <p className="text-xs text-gray-600 mt-1">{error}</p>
          </div>
          <button type="button" className="btn-secondary text-xs" onClick={loadApplications}>
            Retry
          </button>
        </div>
      )}

      {applications.length === 0 ? (
        <div className="empty-state-card text-center py-16 px-4 bg-white border border-gray-200 rounded-xl">
          <div className="w-12 h-12 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-3 text-gray-400">
            <FileText className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-gray-800">
            {statusFilter === 'ALL' ? 'No applications tracked yet' : `No applications in "${STATUS_LABELS[statusFilter]}"`}
          </h3>
          <p className="text-sm text-gray-500 max-w-md mx-auto mt-1 mb-6">
            Track key submission milestones, planned submission dates, and private notes across your scholarship portfolio.
          </p>
          <div className="flex justify-center gap-3">
            <button type="button" className="btn-primary text-xs" onClick={() => setShowAddModal(true)}>
              <Plus className="w-3.5 h-3.5 mr-1 inline" /> Track an Application
            </button>
            <button type="button" className="btn-secondary text-xs" onClick={onGoToDiscover}>
              <Compass className="w-3.5 h-3.5 mr-1 inline" /> Browse Scholarships
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5">
          {applications.map((app) => {
            const opp = app.opportunity;
            const isEditing = editingId === app.id;

            return (
              <div
                key={app.id}
                className="application-card bg-white border border-gray-200 rounded-xl p-5 hover:border-gray-300 transition-colors shadow-sm"
                data-testid={`app-card-${app.id}`}
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-100 pb-4 mb-4">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap mb-1.5">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
                          STATUS_COLORS[app.status]
                        }`}
                      >
                        {STATUS_LABELS[app.status]}
                      </span>
                      <VerificationBadge state={opp.verification_status} />
                      <FreshnessBadge level={opp.freshness_level} message={opp.freshness_message} />
                    </div>

                    <h2
                      className="text-lg font-bold text-gray-900 hover:text-brand cursor-pointer truncate"
                      onClick={() => onSelectOpportunity(opp.id)}
                    >
                      {opp.title}
                    </h2>

                    <div className="flex items-center gap-3 text-xs text-gray-500 mt-1 flex-wrap">
                      <span className="flex items-center gap-1">
                        <Building2 className="w-3.5 h-3.5 text-gray-400" />
                        {opp.university_name || opp.provider_name || 'Institutional Opportunity'}
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5 text-gray-400" />
                        Deadline: {opp.earliest_deadline || 'Not published'} ({opp.deadline_status})
                      </span>
                      <span className="text-gray-400">Cycle: {app.target_academic_cycle || opp.academic_cycle}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0">
                    {!isEditing ? (
                      <>
                        <button
                          type="button"
                          className="btn-secondary text-xs"
                          onClick={() => handleStartEdit(app)}
                        >
                          <Edit2 className="w-3.5 h-3.5 mr-1 inline" /> Edit Tracking
                        </button>
                        <button
                          type="button"
                          className="btn-primary text-xs"
                          onClick={() => onSelectOpportunity(opp.id)}
                        >
                          View Details
                        </button>
                        <button
                          type="button"
                          className="btn-outline-danger text-xs px-2.5"
                          onClick={() => handleDelete(app.id, opp.title)}
                          aria-label={`Delete application for ${opp.title}`}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          type="button"
                          className="btn-primary text-xs"
                          onClick={() => handleSaveEdit(app.id)}
                          disabled={savingEdit}
                        >
                          {savingEdit ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin mr-1 inline" />
                          ) : (
                            <Save className="w-3.5 h-3.5 mr-1 inline" />
                          )}
                          Save Changes
                        </button>
                        <button
                          type="button"
                          className="btn-secondary text-xs"
                          onClick={() => setEditingId(null)}
                          disabled={savingEdit}
                        >
                          <X className="w-3.5 h-3.5 mr-1 inline" /> Cancel
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {isEditing ? (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-gray-700 mb-1">Status</label>
                        <select
                          className="form-input text-xs w-full"
                          value={editForm.status}
                          onChange={(e) => setEditForm((prev) => ({ ...prev, status: e.target.value as ApplicationStatus }))}
                        >
                          <option value="NOT_STARTED">Not Started</option>
                          <option value="PLANNING">Planning</option>
                          <option value="IN_PROGRESS">In Progress</option>
                          <option value="SUBMITTED">Submitted</option>
                          <option value="WITHDRAWN">Withdrawn</option>
                          <option value="DECISION_RECEIVED">Decision Received</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-gray-700 mb-1">Planned Submission Date</label>
                        <input
                          type="date"
                          className="form-input text-xs w-full"
                          value={editForm.planned_submission_date}
                          onChange={(e) => setEditForm((prev) => ({ ...prev, planned_submission_date: e.target.value }))}
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-gray-700 mb-1">Actual Submission Date</label>
                        <input
                          type="date"
                          className="form-input text-xs w-full"
                          value={editForm.actual_submission_date}
                          onChange={(e) => setEditForm((prev) => ({ ...prev, actual_submission_date: e.target.value }))}
                        />
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <label className="text-xs font-semibold text-gray-700">
                          Student-Provided Notes (Max 5,000 chars)
                        </label>
                        <span className="text-[10px] text-amber-700 font-medium bg-amber-50 px-2 py-0.5 rounded">
                          Student-provided note — Not official scholarship evidence
                        </span>
                      </div>
                      <textarea
                        rows={3}
                        maxLength={5000}
                        className="form-input text-xs w-full font-mono text-gray-700"
                        placeholder="Write personal preparation reminders, checklist progress, contacts, or draft links..."
                        value={editForm.student_notes}
                        onChange={(e) => setEditForm((prev) => ({ ...prev, student_notes: e.target.value }))}
                      />
                    </div>
                  </div>
                ) : (
                  <div className="text-xs space-y-2">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-gray-600">
                      <div>
                        <span className="font-semibold text-gray-700">Planned Submission:</span>{' '}
                        {app.planned_submission_date ? app.planned_submission_date : 'Not scheduled'}
                      </div>
                      <div>
                        <span className="font-semibold text-gray-700">Actual Submission:</span>{' '}
                        {app.actual_submission_date ? app.actual_submission_date : 'Pending'}
                      </div>
                    </div>

                    {app.student_notes ? (
                      <div className="mt-3 bg-amber-50/60 border border-amber-200/80 rounded-lg p-3">
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <span className="font-semibold text-amber-900 text-[11px] uppercase tracking-wider">
                            Student-provided note
                          </span>
                          <span className="text-[10px] text-amber-700">
                            Private note • Never treated as official evidence
                          </span>
                        </div>
                        <p className="text-gray-800 whitespace-pre-wrap font-sans text-xs">{app.student_notes}</p>
                      </div>
                    ) : (
                      <p className="text-gray-400 italic text-[11px] mt-2">
                        No private notes added. Click &ldquo;Edit Tracking&rdquo; to add personal notes or submission dates.
                      </p>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Modal to add an application */}
      {showAddModal && (
        <div
          className="modal-overlay"
          role="dialog"
          aria-modal="true"
          aria-labelledby="add-app-title"
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowAddModal(false);
          }}
        >
          <div className="modal-dialog">
            <div className="modal-header">
              <h2 id="add-app-title" className="modal-title">Track a Scholarship Application</h2>
              <button
                type="button"
                className="btn-close-modal"
                onClick={() => setShowAddModal(false)}
                aria-label="Close dialog"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateApplication} className="p-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Search Scholarship Opportunity
                </label>
                <input
                  type="text"
                  className="form-input text-xs w-full"
                  placeholder="Type scholarship or university name..."
                  value={searchOppTerm}
                  onChange={(e) => handleSearchOpps(e.target.value)}
                />
                {searchingOpps && <p className="text-xs text-gray-400 mt-1">Searching...</p>}
                {availableOpps.length > 0 && (
                  <div className="border border-gray-200 rounded-md mt-2 max-h-48 overflow-y-auto divide-y divide-gray-100 bg-white shadow-sm">
                    {availableOpps.map((opp) => (
                      <div
                        key={opp.id}
                        className={`p-2 text-xs cursor-pointer hover:bg-brand/10 transition-colors ${
                          newOppId === opp.id ? 'bg-brand/20 font-semibold' : ''
                        }`}
                        onClick={() => setNewOppId(opp.id)}
                      >
                        <div className="text-gray-900">{opp.title}</div>
                        <div className="text-gray-500 text-[11px]">{opp.university_name || 'General Opportunity'}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Selected Opportunity ID
                </label>
                <input
                  type="text"
                  required
                  readOnly
                  className="form-input text-xs w-full bg-gray-100 text-gray-600"
                  value={newOppId}
                  placeholder="Select a scholarship from the list above"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-gray-100">
                <button
                  type="button"
                  className="btn-secondary text-xs"
                  onClick={() => setShowAddModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary text-xs"
                  disabled={!newOppId}
                >
                  Start Tracking
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
