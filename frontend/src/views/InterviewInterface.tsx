import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { questionAPI, assessmentAPI } from '../api/client';
import { Button, Card, TextArea } from '../components';

interface Question {
  id: number;
  question_text: string;
  pillar: string;
  subcategory: string;
  target_role: string;
  question_type: string;
  evidence_required: boolean;
  is_critical: boolean;
}

interface Response {
  answer_text: string;
  score: number | null;
  has_evidence: boolean;
  notes: string;
}

export const InterviewInterface: React.FC = () => {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [responses, setResponses] = useState<Record<number, Response>>({});
  const [loading, setLoading] = useState(true);
  const [assessment, setAssessment] = useState<any>(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadData();
  }, [assessmentId]);

  const loadData = async () => {
    try {
      const [questionsData, assessmentData] = await Promise.all([
        questionAPI.listAll(),
        assessmentAPI.getById(Number(assessmentId)),
      ]);
      setQuestions(questionsData);
      setAssessment(assessmentData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const currentQuestion = questions[currentIndex];
  const currentResponse = responses[currentQuestion?.id] || {
    answer_text: '',
    score: null,
    has_evidence: false,
    notes: '',
  };

  const handleResponseChange = (field: keyof Response, value: any) => {
    setResponses({
      ...responses,
      [currentQuestion.id]: {
        ...currentResponse,
        [field]: value,
      },
    });
  };

  const handleSubmitResponse = async () => {
    try {
      await questionAPI.submitResponse(
        Number(assessmentId),
        currentQuestion.id,
        {
          ...currentResponse,
          score: currentResponse.score ?? undefined
        }
      );
      
      if (currentIndex < questions.length - 1) {
        setCurrentIndex(currentIndex + 1);
      } else {
        navigate(`/assessment/${assessmentId}`);
      }
    } catch (error) {
      console.error('Failed to submit response:', error);
    }
  };

  const getPillarColor = (pillar: string) => {
    switch (pillar.toLowerCase()) {
      case 'people': return '#C65D3B';
      case 'process': return '#0D4F4F';
      case 'technology': return '#B5830B';
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

  if (!currentQuestion) {
    return (
      <div style={{ padding: '40px 24px', maxWidth: '800px', margin: '0 auto', textAlign: 'center' }}>
        <Card>
          <h2>No Questions Available</h2>
          <Button onClick={() => navigate(`/assessment/${assessmentId}`)}>
            Back to Assessment
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div style={{ padding: '40px 24px', maxWidth: '900px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '40px' }}>
        <Button
          variant="text"
          onClick={() => navigate(`/assessment/${assessmentId}`)}
          style={{ marginBottom: '16px', padding: '0' }}
        >
          ← Back to Assessment
        </Button>
        <h1 style={{ fontSize: '2rem', marginBottom: '8px' }}>
          {assessment?.client_name} - Interview
        </h1>
        <p style={{ color: '#5C5C5C', fontSize: '0.875rem' }}>
          Question {currentIndex + 1} of {questions.length}
        </p>
      </div>

      {/* Progress Bar */}
      <div style={{
        height: '4px',
        background: '#E5E4E0',
        borderRadius: '4px',
        marginBottom: '40px',
        overflow: 'hidden',
      }}>
        <div style={{
          height: '100%',
          background: '#0D4F4F',
          width: `${((currentIndex + 1) / questions.length) * 100}%`,
          transition: 'width 0.3s ease',
        }} />
      </div>

      <Card>
        {/* Question Metadata */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', flexWrap: 'wrap' }}>
          <span style={{
            padding: '4px 12px',
            borderRadius: '12px',
            fontSize: '0.75rem',
            fontWeight: 500,
            background: `${getPillarColor(currentQuestion.pillar)}20`,
            color: getPillarColor(currentQuestion.pillar),
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}>
            {currentQuestion.pillar}
          </span>
          <span style={{
            padding: '4px 12px',
            borderRadius: '12px',
            fontSize: '0.75rem',
            fontWeight: 500,
            background: '#F2F1EE',
            color: '#5C5C5C',
            fontFamily: "'IBM Plex Mono', monospace",
          }}>
            {currentQuestion.target_role}
          </span>
          {currentQuestion.is_critical && (
            <span style={{
              padding: '4px 12px',
              borderRadius: '12px',
              fontSize: '0.75rem',
              fontWeight: 500,
              background: '#9B2C2C20',
              color: '#9B2C2C',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}>
              ⚠️ Critical
            </span>
          )}
        </div>

        {/* Question Text */}
        <h2 style={{ fontSize: '1.5rem', marginBottom: '8px', lineHeight: 1.4 }}>
          {currentQuestion.question_text}
        </h2>
        <p style={{ color: '#8A8A8A', fontSize: '0.875rem', marginBottom: '32px' }}>
          {currentQuestion.subcategory}
        </p>

        {/* Response Fields */}
        <div style={{ marginBottom: '24px' }}>
          <TextArea
            label="Answer / Observations"
            value={currentResponse.answer_text}
            onChange={(e) => handleResponseChange('answer_text', e.target.value)}
            rows={6}
            placeholder="Record the interviewee's response, key observations, and any relevant details..."
          />

          {currentQuestion.question_type === 'scored' && (
            <div style={{ marginBottom: '24px' }}>
              <label style={{
                display: 'block',
                marginBottom: '12px',
                fontWeight: 500,
                fontSize: '0.875rem',
                color: '#1A1A1A',
              }}>
                Score (1-5)
              </label>
              <div style={{ display: 'flex', gap: '12px' }}>
                {[1, 2, 3, 4, 5].map((score) => (
                  <button
                    key={score}
                    type="button"
                    onClick={() => handleResponseChange('score', score)}
                    style={{
                      flex: 1,
                      padding: '16px',
                      border: `2px solid ${currentResponse.score === score ? '#0D4F4F' : '#E5E4E0'}`,
                      borderRadius: '8px',
                      background: currentResponse.score === score ? '#0D4F4F' : '#fff',
                      color: currentResponse.score === score ? '#fff' : '#1A1A1A',
                      fontSize: '1.25rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      fontFamily: "'IBM Plex Mono', monospace",
                    }}
                  >
                    {score}
                  </button>
                ))}
              </div>
              <p style={{ marginTop: '8px', fontSize: '0.75rem', color: '#8A8A8A' }}>
                1 = Reactive | 2 = Developing | 3 = Preventive | 4 = Predictive | 5 = Prescriptive
              </p>
            </div>
          )}

          {currentQuestion.evidence_required && (
            <div style={{
              padding: '16px',
              background: '#F2F1EE',
              borderRadius: '8px',
              marginBottom: '24px',
            }}>
              <label style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                cursor: 'pointer',
                fontWeight: 500,
                fontSize: '0.875rem',
              }}>
                <input
                  type="checkbox"
                  checked={currentResponse.has_evidence}
                  onChange={(e) => handleResponseChange('has_evidence', e.target.checked)}
                  style={{ width: '20px', height: '20px', cursor: 'pointer' }}
                />
                Evidence Provided
                {currentQuestion.evidence_required && (
                  <span style={{ color: '#9B2C2C', fontSize: '0.75rem' }}>
                    (Required for scores ≥4)
                  </span>
                )}
              </label>
            </div>
          )}

          <TextArea
            label="Additional Notes (Optional)"
            value={currentResponse.notes}
            onChange={(e) => handleResponseChange('notes', e.target.value)}
            rows={3}
            placeholder="Any clarifications, follow-up items, or context..."
          />
        </div>

        {/* Navigation Buttons */}
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'space-between' }}>
          <Button
            variant="outline"
            onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))}
            disabled={currentIndex === 0}
          >
            ← Previous
          </Button>

          <div style={{ display: 'flex', gap: '12px' }}>
            <Button variant="secondary" onClick={() => navigate(`/assessment/${assessmentId}`)}>
              Save & Exit
            </Button>
            <Button onClick={handleSubmitResponse}>
              {currentIndex < questions.length - 1 ? 'Next →' : 'Complete Interview'}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};
