/**
 * StandupBot — DigestDetail Page
 *
 * Fetches a single digest by ID and renders the DigestView component.
 * Route: /dashboard/digests/:id
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { DigestView } from '../components/digest/DigestView';
import { Spinner } from '../components/ui/Spinner';
import './DigestDetail.css';

interface DigestData {
  id: string;
  team_id: string;
  digest_date: string;
  ai_summary: string | null;
  total_members: number;
  responded_count: number;
  response_rate: number;
  non_responders: string[];
  blockers: any[];
  status: string;
  created_at: string;
}

export function DigestDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [digest, setDigest] = useState<DigestData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    async function fetchDigest() {
      try {
        // First get the team_id from teams list
        const teamsRes = await apiClient.get('/v1/teams');
        if (teamsRes.data.length === 0) {
          setError('No teams found');
          setLoading(false);
          return;
        }
        const teamId = teamsRes.data[0].id;

        const res = await apiClient.get<DigestData>(
          `/v1/digests/${teamId}/${id}`
        );
        setDigest(res.data);
      } catch (err: any) {
        setError(err?.detail || 'Failed to load digest');
      } finally {
        setLoading(false);
      }
    }

    fetchDigest();
  }, [id]);

  if (loading) {
    return (
      <div className="digest-detail__loading">
        <Spinner size="lg" label="Loading digest..." />
      </div>
    );
  }

  if (error || !digest) {
    return (
      <div className="digest-detail__error">
        <span className="digest-detail__error-icon">❌</span>
        <h2>Digest Not Found</h2>
        <p>{error || 'This digest could not be loaded.'}</p>
        <button
          className="digest-detail__error-btn"
          onClick={() => navigate('/dashboard/digests')}
        >
          ← Back to Digests
        </button>
      </div>
    );
  }

  return (
    <div className="digest-detail">
      <DigestView
        digest={digest}
        onBack={() => navigate('/dashboard/digests')}
      />
    </div>
  );
}
