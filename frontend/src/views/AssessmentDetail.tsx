import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { assessmentAPI, scoringAPI, cmmsAPI, observationAPI } from '../api/client';
import { Button, Card, Modal } from '../components';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts';

export const AssessmentDetail: React.FC = () => {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const [assessment, setAssessment] = useState<any>(null);
  const [scores, setScores] = useState<any>(null);
  const [observations, setObservations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showReportModal, setShowReportModal] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadAssessmentData();
  }, [assessmentId]);

  const loadAssessmentData = async () => {
    try {
      const [assessmentData, scoresData, observationsData] = await Promise.all([
        assessmentAPI.getById(Number(assessmentId)),
        scoringAPI.getScores(Number(assessmentId)).catch(() => null),
        observationAPI.list(Number(assessmentId)).catch(() => []),
      ]);
      
      setAssessment(assessmentData);
      setScores(scoresData);
      setObservations(observationsData);
    } catch (error) {
      console.error('Failed to load assessment:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCalculateScores = async () => {
    try {
      const calculatedScores = await scoringAPI.calculate(Number(assessmentId));
      setScores(calculatedScores);
    } catch (error) {
      console.error('Failed to calculate scores:', error);
    }
  };

  const handleGenerateReport = async () => {
    setGeneratingReport(true);
    try {
      await assessmentAPI.generateReport(Number(assessmentId));
      setShowReportModal(true);
    } catch (error) {
      console.error('Failed to generate report:', error);
    } finally {
      setGeneratingReport(false);
    }
  };

  const handleDownloadReport = async () => {
    try {
      const blob = await assessmentAPI.downloadReport(Number(assessmentId));
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `RMI_Report_${assessment.client_name}_${new Date().toISOString().split('T')[0]}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download report:', error);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      await cmmsAPI.upload(Number(assessmentId), file);
      alert('CMMS data uploaded successfully!');
    } catch (error) {
      console.error('Failed to upload CMMS data:', error);
      alert('Failed to upload CMMS data');
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div className="spinner" />
      </div>
    );
  }

  const radarData = scores?.pillar_scores ? [
    { pillar: 'People', score: scores.pillar_scores.people || 0 },
    { pillar: 'Process', score: scores.pillar_scores.process || 0 },
    { pillar: 'Technology', score: scores.pillar_scores.technology || 0 },
  ] : [];

  const criticalObservations = observations.filter((obs: any) => 
    obs.severity === 'high' || obs.compliance_status === 'non_compliant'
  );

  return (
    <div style={{ padding: '40px 24px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '40px' }}>
        <Button
          variant="text"
          onClick={() => navigate('/dashboard')}
          style={{ marginBottom: '16px', padding: '0' }}
        >
          ← Back to Dashboard
        </Button>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h1 style={{ fontSize: '2.5rem', marginBottom: '8px' }}>
              {assessment.client_name}
            </h1>
            <p style={{ color: '#5C5C5C', fontSize: '1rem' }}>
              📍 {assessment.site_location}
            </p>
          </div>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <Button onClick={handleCalculateScores}>
              Calculate RMI Score
            </Button>
            <Button
              variant="secondary"
              onClick={handleGenerateReport}
              loading={generatingReport}
            >
              📄 Generate Report
            </Button>
          </div>
        </div>
      </div>

      {/* RMI Score Card */}
      {scores && (
        <Card style={{ marginBottom: '40px', background: '#0D4F4F', color: '#fff', padding: '48px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '48px', alignItems: 'center' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{
                fontSize: '5rem',
                fontWeight: 700,
                fontFamily: "'IBM Plex Mono', monospace",
                lineHeight: 1,
                marginBottom: '8px',
              }}>
                {scores.overall_rmi.toFixed(1)}
              </div>
              <div style={{
                fontSize: '0.875rem',
                textTransform: 'uppercase',
                letterSpacing: '0.15em',
                color: 'rgba(255,255,255,0.7)',
              }}>
                RMI Score
              </div>
              <div style={{
                marginTop: '16px',
                padding: '8px 16px',
                background: 'rgba(255,255,255,0.15)',
                borderRadius: '4px',
                fontSize: '0.875rem',
                fontWeight: 500,
              }}>
                {scores.maturity_level}
              </div>
            </div>

            {radarData.length > 0 && (
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="rgba(255,255,255,0.2)" />
                  <PolarAngleAxis dataKey="pillar" tick={{ fill: '#fff', fontSize: 14 }} />
                  <PolarRadiusAxis angle={90} domain={[0, 5]} tick={{ fill: 'rgba(255,255,255,0.6)' }} />
                  <Radar
                    dataKey="score"
                    stroke="#C65D3B"
                    fill="#C65D3B"
                    fillOpacity={0.6}
                    strokeWidth={3}
                  />
                </RadarChart>
              </ResponsiveContainer>
            )}
          </div>

          {scores.pillar_scores && (
            <div style={{
              marginTop: '32px',
              paddingTop: '32px',
              borderTop: '1px solid rgba(255,255,255,0.2)',
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '24px',
            }}>
              {Object.entries(scores.pillar_scores).map(([pillar, score]: any) => (
                <div key={pillar}>
                  <div style={{
                    fontSize: '0.75rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.1em',
                    color: 'rgba(255,255,255,0.7)',
                    marginBottom: '4px',
                  }}>
                    {pillar}
                  </div>
                  <div style={{
                    fontSize: '2rem',
                    fontWeight: 600,
                    fontFamily: "'IBM Plex Mono', monospace",
                  }}>
                    {score.toFixed(1)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Action Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '24px',
        marginBottom: '40px',
      }}>
        <Card
          hover
          onClick={() => navigate(`/assessment/${assessmentId}/interview`)}
          style={{ cursor: 'pointer' }}
        >
          <div style={{
            fontSize: '0.75rem',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
            color: '#C65D3B',
            marginBottom: '12px',
            fontWeight: 600,
          }}>
            01 · People & Process
          </div>
          <h3 style={{ fontSize: '1.25rem', marginBottom: '8px' }}>
            Interview Module
          </h3>
          <p style={{ color: '#5C5C5C', fontSize: '0.875rem', marginBottom: '16px' }}>
            Conduct structured interviews across all three RMI pillars
          </p>
          <Button variant="text" style={{ padding: '0' }}>
            Start Interview →
          </Button>
        </Card>

        <Card
          hover
          onClick={() => navigate(`/assessment/${assessmentId}/observations`)}
          style={{ cursor: 'pointer' }}
        >
          <div style={{
            fontSize: '0.75rem',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
            color: '#0D4F4F',
            marginBottom: '12px',
            fontWeight: 600,
          }}>
            02 · Field Observations
          </div>
          <h3 style={{ fontSize: '1.25rem', marginBottom: '8px' }}>
            Observation Checklist
          </h3>
          <p style={{ color: '#5C5C5C', fontSize: '0.875rem', marginBottom: '16px' }}>
            Real-time compliance assessment during job shadowing
          </p>
          <Button variant="text" style={{ padding: '0' }}>
            Open Checklist →
          </Button>
        </Card>

        <Card hover style={{ cursor: 'pointer', position: 'relative' }}>
          <div style={{
            fontSize: '0.75rem',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
            color: '#B5830B',
            marginBottom: '12px',
            fontWeight: 600,
          }}>
            03 · Technology Data
          </div>
          <h3 style={{ fontSize: '1.25rem', marginBottom: '8px' }}>
            CMMS Data Upload
          </h3>
          <p style={{ color: '#5C5C5C', fontSize: '0.875rem', marginBottom: '16px' }}>
            Import work order history for automated analysis
          </p>
          <input
            type="file"
            accept=".csv,.xlsx,.xls"
            onChange={handleFileUpload}
            style={{ display: 'none' }}
            id="cmms-upload"
          />
          <label htmlFor="cmms-upload">
            <Button variant="text" as="span" style={{ padding: '0', cursor: 'pointer' }}>
              Upload CMMS Export →
            </Button>
          </label>
        </Card>
      </div>

      {/* Critical Observations */}
      {criticalObservations.length > 0 && (
        <Card style={{ marginBottom: '40px', borderColor: '#9B2C2C', borderWidth: '2px' }}>
          <h2 style={{ fontSize: '1.5rem', marginBottom: '16px', color: '#9B2C2C' }}>
            ⚠️ Critical Observations ({criticalObservations.length})
          </h2>
          <div style={{ display: 'grid', gap: '12px' }}>
            {criticalObservations.slice(0, 5).map((obs: any) => (
              <div
                key={obs.id}
                style={{
                  padding: '16px',
                  background: '#F2F1EE',
                  borderRadius: '8px',
                  borderLeft: '4px solid #9B2C2C',
                }}
              >
                <div style={{ fontWeight: 500, marginBottom: '4px' }}>
                  {obs.category}
                </div>
                <p style={{ fontSize: '0.875rem', color: '#5C5C5C' }}>
                  {obs.description}
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Report Modal */}
      <Modal
        isOpen={showReportModal}
        onClose={() => setShowReportModal(false)}
        title="Report Generated Successfully"
        maxWidth="500px"
      >
        <p style={{ marginBottom: '24px', color: '#5C5C5C' }}>
          Your RMI audit report has been generated and is ready to download.
        </p>
        <div style={{ display: 'flex', gap: '12px' }}>
          <Button onClick={handleDownloadReport} fullWidth>
            📥 Download PDF Report
          </Button>
        </div>
      </Modal>
    </div>
  );
};
