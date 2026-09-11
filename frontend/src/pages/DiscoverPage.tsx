import React, { useState, useEffect, useCallback } from 'react';
import type { PaginatedOpportunities } from '../types';
import { fetchOpportunities } from '../api/client';
import type { OpportunityFilterParams } from '../api/client';
import { OpportunityCard } from '../components/OpportunityCard';
import { Search, Filter, RotateCcw, AlertCircle, Loader2, ArrowRight } from 'lucide-react';

interface DiscoverPageProps {
  onSelectOpportunity: (id: string) => void;
  comparedIds: string[];
  onToggleCompare: (id: string) => void;
  onGoToCompare: () => void;
}

export const DiscoverPage: React.FC<DiscoverPageProps> = ({
  onSelectOpportunity,
  comparedIds,
  onToggleCompare,
  onGoToCompare,
}) => {
  const [data, setData] = useState<PaginatedOpportunities | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters state
  const [search, setSearch] = useState<string>('');
  const [degreeLevel, setDegreeLevel] = useState<string>('');
  const [internationalAllowed, setInternationalAllowed] = useState<string>('');
  const [fundingClass, setFundingClass] = useState<string>('');
  const [verificationStatus, setVerificationStatus] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const pageSize = 9;

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: OpportunityFilterParams = {
        page,
        page_size: pageSize,
      };
      if (search.trim()) params.search = search.trim();
      if (degreeLevel) params.degree_level = degreeLevel;
      if (internationalAllowed === 'true') params.international_allowed = true;
      if (internationalAllowed === 'false') params.international_allowed = false;
      if (fundingClass) params.funding_classification = fundingClass;
      if (verificationStatus) params.verification_status = verificationStatus;

      const res = await fetchOpportunities(params);
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve opportunities');
    } finally {
      setLoading(false);
    }
  }, [search, degreeLevel, internationalAllowed, fundingClass, verificationStatus, page]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleResetFilters = () => {
    setSearch('');
    setDegreeLevel('');
    setInternationalAllowed('');
    setFundingClass('');
    setVerificationStatus('');
    setPage(1);
  };

  return (
    <div className="page-container">
      {/* Search & Filter Bar */}
      <section className="search-filter-section" aria-label="Search and Filter">
        <div className="search-box">
          <Search className="search-icon w-5 h-5 text-gray-400" />
          <input
            type="search"
            className="search-input"
            placeholder="Search scholarships by title, provider, university, or keyword..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            aria-label="Search scholarships"
          />
        </div>

        <div className="filters-row">
          <div className="filter-group">
            <label htmlFor="filter-degree" className="filter-label">
              <Filter className="w-3.5 h-3.5 inline mr-1" />
              Degree Level
            </label>
            <select
              id="filter-degree"
              className="filter-select"
              value={degreeLevel}
              onChange={(e) => {
                setDegreeLevel(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All Degree Levels</option>
              <option value="UNDERGRADUATE">Undergraduate</option>
              <option value="GRADUATE">Graduate (Master's / PhD)</option>
              <option value="POSTGRADUATE">Postgraduate</option>
              <option value="HIGH_SCHOOL">High School</option>
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="filter-intl" className="filter-label">
              International Students
            </label>
            <select
              id="filter-intl"
              className="filter-select"
              value={internationalAllowed}
              onChange={(e) => {
                setInternationalAllowed(e.target.value);
                setPage(1);
              }}
            >
              <option value="">Any Status</option>
              <option value="true">Allowed (Non-US Eligible)</option>
              <option value="false">US Citizens / Residents Only</option>
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="filter-funding" className="filter-label">
              Funding Coverage
            </label>
            <select
              id="filter-funding"
              className="filter-select"
              value={fundingClass}
              onChange={(e) => {
                setFundingClass(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All Funding Types</option>
              <option value="FULL_FUNDING">Full Funding (Tuition + Living)</option>
              <option value="FULL_TUITION">Full Tuition Only</option>
              <option value="PARTIAL_FUNDING">Partial Funding</option>
              <option value="STIPEND_ONLY">Stipend Only</option>
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="filter-verif" className="filter-label">
              Verification State
            </label>
            <select
              id="filter-verif"
              className="filter-select"
              value={verificationStatus}
              onChange={(e) => {
                setVerificationStatus(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All Verification States</option>
              <option value="VERIFIED">Verified Official Only</option>
              <option value="PARTIALLY_VERIFIED">Partially Verified</option>
              <option value="CONFLICTING">Conflicting Sources</option>
              <option value="UNVERIFIED">Unverified</option>
            </select>
          </div>

          {(search || degreeLevel || internationalAllowed || fundingClass || verificationStatus) && (
            <button
              type="button"
              className="btn-reset-filters"
              onClick={handleResetFilters}
              title="Reset all filters"
            >
              <RotateCcw className="w-3.5 h-3.5 mr-1 inline" />
              Reset Filters
            </button>
          )}
        </div>
      </section>

      {/* Main Content Area */}
      <section className="results-section">
        {loading ? (
          <div className="state-container loading-state">
            <Loader2 className="w-8 h-8 animate-spin text-brand mx-auto mb-3" />
            <h4 className="font-semibold text-gray-700">Loading Opportunities...</h4>
            <p className="text-sm text-gray-500">Checking verified repositories and eligibility records.</p>
          </div>
        ) : error ? (
          <div className="state-container error-state">
            <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-3" />
            <h4 className="font-semibold text-red-700">Unable to Load Opportunities</h4>
            <p className="text-sm text-red-600 mb-4">{error}</p>
            <button type="button" className="btn-primary" onClick={loadData}>
              Retry Connection
            </button>
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="state-container empty-state">
            <h4 className="font-semibold text-gray-700">No Matching Opportunities</h4>
            <p className="text-sm text-gray-500 mb-4">
              No opportunities match your current filter criteria. Try broadening your search or resetting filters.
            </p>
            <button type="button" className="btn-secondary" onClick={handleResetFilters}>
              Clear All Filters
            </button>
          </div>
        ) : (
          <>
            <div className="results-header-bar">
              <span className="results-count">
                Showing <strong>{data.items.length}</strong> of <strong>{data.total}</strong> opportunities
              </span>
              <span className="epistemic-note">
                Epistemic rule: Unknown or conflicting items are never fabricated or hidden.
              </span>
            </div>

            <div className="opp-cards-grid">
              {data.items.map((opp) => (
                <OpportunityCard
                  key={opp.id}
                  opportunity={opp}
                  onSelect={onSelectOpportunity}
                  isCompared={comparedIds.includes(opp.id)}
                  onToggleCompare={onToggleCompare}
                />
              ))}
            </div>

            {/* Pagination */}
            {((data as any).total_pages ?? data.pages ?? 1) > 1 && (
              <div className="pagination-bar" aria-label="Pagination">
                <button
                  type="button"
                  className="btn-pagination"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </button>
                <span className="page-indicator">
                  Page <strong>{data.page}</strong> of <strong>{(data as any).total_pages ?? data.pages}</strong>
                </span>
                <button
                  type="button"
                  className="btn-pagination"
                  disabled={page >= ((data as any).total_pages ?? data.pages ?? 1)}
                  onClick={() => setPage((p) => Math.min((data as any).total_pages ?? data.pages ?? 1, p + 1))}
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </section>

      {/* Floating Comparison Tray */}
      {comparedIds.length > 0 && (
        <aside className="comparison-tray" aria-label="Comparison Tray">
          <div className="tray-content">
            <span className="tray-text">
              <strong>{comparedIds.length}</strong> opportunity{comparedIds.length > 1 ? 'ies' : ''} selected for side-by-side comparison
            </span>
            <div className="tray-actions">
              <button
                type="button"
                className="btn-primary btn-sm"
                onClick={onGoToCompare}
              >
                Compare Now <ArrowRight className="w-4 h-4 ml-1 inline" />
              </button>
            </div>
          </div>
        </aside>
      )}
    </div>
  );
};
