import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { assessmentAPI } from '../api/client';
import { Button, Card, Modal, Input } from '../components';
import { format } from 'date-fns';

interface Assessment {
  id: number;
  client_name: string;
  site_name: string;
  assessment_date: string;
  status: string;
  created_at: string;
}

export const Dashboard: React.FC = () => {
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newAssessment, setNewAssessment] = useState({
    client_name: '',
    site_name: '',
    assessment_date: '',
  });
  const navigate = useNavigate();

  useEffect(() => {
    loadAssessments();
  }, []);

  const loadAssessments = async () => {
    try {
      const data = await assessmentAPI.list();
      setAssessments(data);
    } catch (error) {
      console.error('Failed to load assessments:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAssessment = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // Convert date string to ISO datetime format
      const assessmentData = {
        ...newAssessment,
        assessment_date: new Date(newAssessment.assessment_date).toISOString(),
      };
      const created = await assessmentAPI.create(assessmentData);
      setAssessments([...assessments, created]);
      setShowCreateModal(false);
      setNewAssessment({ client_name: '', site_name: '', assessment_date: '' });
    } catch (error) {
      console.error('Failed to create assessment:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'in_progress': return '#C65D3B';
      case 'completed': return '#2D6A4F';
      case 'draft': return '#8A8A8A';
      default: return '#5C5C5C';
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div style={{ padding: '40px 24px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '40px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '2rem', marginBottom: '8px' }}>RMI Assessments</h1>
          <p style={{ color: '#5C5C5C', fontSize: '0.875rem' }}>
            Manage your Reliability Maturity Index audits
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          + New Assessment
        </Button>
      </div>

      {/* Stats Bar */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '24px',
        marginBottom: '40px',
      }}>
        {[
          { label: 'Total Assessments', value: assessments.length, color: '#0D4F4F' },
          { label: 'In Progress', value: assessments.filter(a => a.status === 'in_progress').length, color: '#C65D3B' },
          { label: 'Completed', value: assessments.filter(a => a.status === 'completed').length, color: '#2D6A4F' },
        ].map((stat, i) => (
          <Card key={i} hover style={{ textAlign: 'center', padding: '24px' }}>
            <div style={{
              fontSize: '2rem',
              fontWeight: 600,
              color: stat.color,
              fontFamily: "'IBM Plex Mono', monospace",
              marginBottom: '8px',
            }}>
              {stat.value}
            </div>
            <div style={{
              fontSize: '0.75rem',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              color: '#5C5C5C',
              fontWeight: 500,
            }}>
              {stat.label}
            </div>
          </Card>
        ))}
      </div>

      {/* Assessments Grid */}
      <div style={{ display: 'grid', gap: '24px' }}>
        {assessments.length === 0 ? (
          <Card style={{ textAlign: 'center', padding: '60px 24px' }}>
            <p style={{ color: '#8A8A8A', marginBottom: '24px' }}>
              No assessments yet. Create your first RMI audit to get started.
            </p>
            <Button onClick={() => setShowCreateModal(true)}>
              + Create Assessment
            </Button>
          </Card>
        ) : (
          assessments.map((assessment) => (
            <Card
              key={assessment.id}
              hover
              onClick={() => navigate(`/assessment/${assessment.id}`)}
              style={{ cursor: 'pointer' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', gap: '24px', flexWrap: 'wrap' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                    <h3 style={{ fontSize: '1.25rem', margin: 0 }}>
                      {assessment.client_name}
                    </h3>
                    <span style={{
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontSize: '0.75rem',
                      fontWeight: 500,
                      background: `${getStatusColor(assessment.status)}20`,
                      color: getStatusColor(assessment.status),
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                    }}>
                      {assessment.status.replace('_', ' ')}
                    </span>
                  </div>
                  <p style={{ color: '#5C5C5C', marginBottom: '16px' }}>
                    📍 {assessment.site_name}
                  </p>
                  <div style={{ display: 'flex', gap: '24px', fontSize: '0.875rem', color: '#8A8A8A', fontFamily: "'IBM Plex Mono', monospace" }}>
                    <span>Date: {format(new Date(assessment.assessment_date), 'MMM dd, yyyy')}</span>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/assessment/${assessment.id}`);
                  }}
                >
                  View Details →
                </Button>
              </div>
            </Card>
          ))
        )}
      </div>

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New Assessment"
        maxWidth="600px"
      >
        <form onSubmit={handleCreateAssessment}>
          <Input
            label="Client Name"
            value={newAssessment.client_name}
            onChange={(e) => setNewAssessment({ ...newAssessment, client_name: e.target.value })}
            placeholder="e.g., ACME Manufacturing"
            required
          />
          
          <Input
            label="Site Name"
            value={newAssessment.site_name}
            onChange={(e) => setNewAssessment({ ...newAssessment, site_name: e.target.value })}
            placeholder="e.g., Houston Plant #3"
            required
          />
          
          <Input
            label="Assessment Date"
            type="date"
            value={newAssessment.assessment_date}
            onChange={(e) => setNewAssessment({ ...newAssessment, assessment_date: e.target.value })}
            required
          />
          
          <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
            <Button type="submit" fullWidth={true}>
              Create Assessment
            </Button>
            <Button
              type="button"
              variant="outline"
              fullWidth={true}
              onClick={() => setShowCreateModal(false)}
            >
              Cancel
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
