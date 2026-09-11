import React, { useState, useEffect, useCallback } from 'react';
import type { SavedOpportunity } from '../types';
import { fetchSavedOpportunities, unsaveOpportunity, ApiError } from '../api/client';
import { VerificationBadge, FundingBadge, FreshnessBadge } from '../components/StatusBadges';
import { Bookmark, Trash2, Calendar, Building2, ArrowRight, Loader2, AlertCircle, Compass } from 'lucide-react';

interface SavedOpportunitiesPageProps {
  onSelectOpportunity: (id: string) => void;
  onGoToDiscover: () => void;
  onTrackApplication?: (opportunityId: string) => void;
}

export const SavedOpportunitiesPage: React.FC<SavedOpportunitiesPageProps> = ({
  onSelectOpportunity,
  onGoToDiscover,
  onTrackApplication,
}) => {
  const [savedItems, setSavedItems] = useState<SavedOpportunity[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [page, setPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [totalCount, setTotalCount] = useState<number>(0);

  const loadSaved = useCallback(async (pageToLoad: number) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchSavedOpportunities(pageToLoad, 20);
      setSavedItems(res.items);
      setPage(res.page);
      setTotalPages(res.pages);
      setTotalCount(res.total);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to load saved scholarships. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSaved(1);
  }, [loadSaved]);

  const handleUnsave = async (opportunityId: string) => {
    setActionLoadingId(opportunityId);
    try {
      await unsaveOpportunity(opportunityId);
      setSavedItems((prev) => prev.filter((item) => item.opportunity_id !== opportunityId));
      setTotalCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to unsave scholarship');
    } finally {
      setActionLoadingId(null);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Not published';
    try {
      return new Date(dateStr).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  if (loading) {
    return (
      <div className="page-container flex justify-center items-center py-20">
        <Loader2 className="w-8 h-8 text-brand animate-spin" />
        <span className="ml-3 text-gray-600 font-medium">Loading your saved scholarships...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container py-12">
        <div className="banner-alert banner-alert-error" role="alert">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="font-semibold text-sm">Failed to retrieve saved scholarships</h3>
            <p className="text-xs text-gray-600 mt-1">{error}</p>
          </div>
          <button type="button" className="btn-secondary text-xs" onClick={() => loadSaved(page)}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container saved-page-container">
      <div className="page-header flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2">
            <Bookmark className="w-6 h-6 text-brand" />
            <h1 className="text-2xl font-bold text-gray-900">Saved Scholarships</h1>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Your personal shortlist. Canonical facts, deadlines, and verification updates are reflected in real time.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 font-medium">
            {totalCount} {totalCount === 1 ? 'Scholarship' : 'Scholarships'} Saved
          </span>
          <button type="button" className="btn-secondary text-xs" onClick={onGoToDiscover}>
            <Compass className="w-3.5 h-3.5 mr-1 inline" /> Discover More
          </button>
        </div>
      </div>

      {savedItems.length === 0 ? (
        <div className="empty-state-card text-center py-16 px-4 bg-white border border-gray-200 rounded-xl">
          <div className="w-12 h-12 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-3 text-gray-400">
            <Bookmark className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-gray-800">No saved scholarships yet</h3>
          <p className="text-sm text-gray-500 max-w-md mx-auto mt-1 mb-6">
            Browse through verified opportunities and click the bookmark icon to keep track of deadlines and funding facts.
          </p>
          <button type="button" className="btn-primary" onClick={onGoToDiscover}>
            Explore Verified Scholarships <ArrowRight className="w-4 h-4 ml-1 inline" />
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {savedItems.map((item) => {
            const opp = item.opportunity;
            const isUnsaving = actionLoadingId === item.opportunity_id;
            return (
              <div
                key={item.id}
                className="saved-opp-card bg-white border border-gray-200 rounded-xl p-5 hover:border-gray-300 transition-colors shadow-sm"
                data-testid={`saved-card-${opp.id}`}
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-2">
                      <VerificationBadge state={opp.verification_status} />
                      <FreshnessBadge level={opp.freshness_level} message={opp.freshness_message} />
                      <FundingBadge classification={opp.funding_classification} />
                      <span className="badge badge-neutral text-xs">Cycle: {opp.academic_cycle}</span>
                    </div>

                    <h2
                      className="text-lg font-semibold text-gray-900 hover:text-brand cursor-pointer truncate"
                      onClick={() => onSelectOpportunity(opp.id)}
                    >
                      {opp.title}
                    </h2>

                    <div className="flex items-center gap-4 text-xs text-gray-500 mt-2 flex-wrap">
                      <span className="flex items-center gap-1">
                        <Building2 className="w-3.5 h-3.5 text-gray-400" />
                        {opp.university_name || opp.provider_name || 'Institutional Opportunity'}
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5 text-gray-400" />
                        Deadline: {formatDate(opp.earliest_deadline)} ({opp.deadline_status})
                      </span>
                      <span className="text-gray-400">
                        Saved {formatDate(item.created_at)}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0">
                    {onTrackApplication && (
                      <button
                        type="button"
                        className="btn-secondary text-xs"
                        onClick={() => onTrackApplication(opp.id)}
                      >
                        Track Application
                      </button>
                    )}
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
                      onClick={() => handleUnsave(opp.id)}
                      disabled={isUnsaving}
                      aria-label={`Unsave ${opp.title}`}
                    >
                      {isUnsaving ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Trash2 className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {totalPages > 1 && (
        <div className="pagination-bar flex justify-center items-center gap-2 mt-8">
          <button
            type="button"
            className="btn-secondary text-xs"
            disabled={page <= 1}
            onClick={() => loadSaved(page - 1)}
          >
            Previous
          </button>
          <span className="text-xs text-gray-500">
            Page {page} of {totalPages}
          </span>
          <button
            type="button"
            className="btn-secondary text-xs"
            disabled={page >= totalPages}
            onClick={() => loadSaved(page + 1)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};
