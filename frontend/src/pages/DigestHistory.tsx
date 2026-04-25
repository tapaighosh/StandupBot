/**
 * StandupBot — DigestHistory Page
 *
 * Paginated list of past digests with date, rate, and status.
 * Click any item to see its detail view.
 */

import { useState, useEffect, useCallback } from 'react';
import apiClient from '../api/client';
import { DigestCard } from '../components/digest/DigestCard';
import { Spinner } from '../components/ui/Spinner';
import './DigestHistory.css';

interface DigestListItem {
  id: string;
  digest_date: string;
  total_members: number;
  responded_count: number;
  response_rate: number;
  status: string;
  sent_at: string | null;
}

export function DigestHistory() {
  const [digests, setDigests] = useState<DigestListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  // TODO: In a real app, team_id comes from a team selector or context
  // For now, we'll fetch from the first available team
  const [teamId, setTeamId] = useState<string | null>(null);

  // Fetch teams to get team_id
  useEffect(() => {
    async function fetchTeamId() {
      try {
        const res = await apiClient.get('/v1/teams');
        if (res.data.length > 0) {
          setTeamId(res.data[0].id);
        } else {
          setLoading(false);
        }
      } catch {
        setError('Failed to load teams');
        setLoading(false);
      }
    }
    fetchTeamId();
  }, []);

  const fetchDigests = useCallback(async (pageNum: number) => {
    if (!teamId) return;
    setLoading(true);
    try {
      const res = await apiClient.get<DigestListItem[]>(
        `/v1/digests/${teamId}/history?page=${pageNum}&page_size=20`
      );
      if (pageNum === 1) {
        setDigests(res.data);
      } else {
        setDigests((prev) => [...prev, ...res.data]);
      }
      setHasMore(res.data.length === 20);
    } catch {
      setError('Failed to load digest history');
    } finally {
      setLoading(false);
    }
  }, [teamId]);

  useEffect(() => {
    if (teamId) fetchDigests(page);
  }, [teamId, page, fetchDigests]);

  const loadMore = () => {
    if (!loading && hasMore) setPage((p) => p + 1);
  };

  // No team yet
  if (!loading && !teamId) {
    return (
      <div className="digest-history">
        <div className="digest-history__header">
          <h1 className="digest-history__title">📋 Digest History</h1>
        </div>
        <div className="digest-history__empty">
          <span className="digest-history__empty-icon">📊</span>
          <h3 className="digest-history__empty-title">No digests yet</h3>
          <p className="digest-history__empty-text">
            Create a team first, then digests will appear here after your
            first standup day.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="digest-history">
      <div className="digest-history__header">
        <h1 className="digest-history__title">📋 Digest History</h1>
        <p className="digest-history__subtitle">
          View your team&apos;s daily standup summaries
        </p>
      </div>

      {error && (
        <div className="digest-history__error">
          <span>⚠️</span> {error}
        </div>
      )}

      {/* Digest List */}
      {digests.length > 0 ? (
        <div className="digest-history__list stagger-children">
          {digests.map((d) => (
            <DigestCard
              key={d.id}
              id={d.id}
              digestDate={d.digest_date}
              totalMembers={d.total_members}
              respondedCount={d.responded_count}
              responseRate={d.response_rate}
              status={d.status}
              sentAt={d.sent_at}
            />
          ))}
        </div>
      ) : !loading ? (
        <div className="digest-history__empty">
          <span className="digest-history__empty-icon">📊</span>
          <h3 className="digest-history__empty-title">No digests yet</h3>
          <p className="digest-history__empty-text">
            They&apos;ll appear here after your first standup day.
            Once your team starts submitting, you&apos;ll see daily summaries.
          </p>
        </div>
      ) : null}

      {/* Loading / Load More */}
      {loading && (
        <div className="digest-history__loading">
          <Spinner size="md" label="Loading digests..." />
        </div>
      )}

      {!loading && hasMore && digests.length > 0 && (
        <button className="digest-history__load-more" onClick={loadMore}>
          Load more
        </button>
      )}
    </div>
  );
}
