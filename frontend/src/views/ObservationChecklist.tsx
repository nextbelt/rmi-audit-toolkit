import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { observationAPI } from '../api/client';
import { Button, Card } from '../components';

interface ChecklistItem {
  id: string;
  category: string;
  description: string;
  status: 'pass' | 'fail' | null;
  severity?: 'low' | 'medium' | 'high';
  notes?: string;
}

const CHECKLIST_TEMPLATES = {
  'Work Execution': [
    { id: 'we-1', description: 'Technician reviewed work order before starting' },
    { id: 'we-2', description: 'All required parts and tools were ready' },
    { id: 'we-3', description: 'Standard operating procedure (SOP) was followed' },
    { id: 'we-4', description: 'Work area was clean and organized' },
    { id: 'we-5', description: 'Technician documented work performed accurately' },
  ],
  'Safety (LOTO/PPE)': [
    { id: 'sf-1', description: 'Proper PPE worn for the task' },
    { id: 'sf-2', description: 'Lockout/Tagout properly applied if required' },
    { id: 'sf-3', description: 'Energy sources verified de-energized' },
    { id: 'sf-4', description: 'Work permit obtained when required' },
    { id: 'sf-5', description: 'Housekeeping maintained during work' },
  ],
  'CMMS Usage': [
    { id: 'cm-1', description: 'Work order accessed on mobile device' },
    { id: 'cm-2', description: 'Time stamps recorded accurately' },
    { id: 'cm-3', description: 'Parts consumption entered in CMMS' },
    { id: 'cm-4', description: 'Failure codes selected appropriately' },
    { id: 'cm-5', description: 'Closure notes provide meaningful details' },
  ],
};

const getStorageKey = (assessmentId: string) => `checklist-${assessmentId}`;

export const ObservationChecklist: React.FC = () => {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const navigate = useNavigate();
  
  // Store ALL categories' data in a single object
  const [allCategoriesData, setAllCategoriesData] = useState<Record<string, ChecklistItem[]>>(() => {
    if (!assessmentId) return {};
    const saved = localStorage.getItem(getStorageKey(assessmentId));
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return parsed.allCategories || {};
      } catch {
        return {};
      }
    }
    return {};
  });
  
  // Load saved state from localStorage on mount
  const [selectedCategory, setSelectedCategory] = useState<string>(() => {
    if (!assessmentId) return 'Work Execution';
    const saved = localStorage.getItem(getStorageKey(assessmentId));
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return parsed.selectedCategory || 'Work Execution';
      } catch {
        return 'Work Execution';
      }
    }
    return 'Work Execution';
  });
  
  const [checklist, setChecklist] = useState<ChecklistItem[]>(() => {
    if (!assessmentId) {
      return CHECKLIST_TEMPLATES['Work Execution'].map(item => ({
        ...item,
        category: 'Work Execution',
        status: null,
      }));
    }
    
    const saved = localStorage.getItem(getStorageKey(assessmentId));
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        const categoryData = parsed.allCategories?.['Work Execution'];
        if (categoryData) {
          return categoryData;
        }
      } catch {
        // Fall through to default
      }
    }
    
    return CHECKLIST_TEMPLATES['Work Execution'].map(item => ({
      ...item,
      category: 'Work Execution',
      status: null,
    }));
  });
  
  const [submitting, setSubmitting] = useState(false);
  
  // Save to localStorage whenever checklist or category changes
  useEffect(() => {
    if (assessmentId) {
      // Update the all categories data with current checklist
      const updatedCategories = {
        ...allCategoriesData,
        [selectedCategory]: checklist,
      };
      setAllCategoriesData(updatedCategories);
      
      // Save everything to localStorage
      localStorage.setItem(getStorageKey(assessmentId), JSON.stringify({
        selectedCategory,
        allCategories: updatedCategories,
      }));
    }
  }, [checklist, selectedCategory, assessmentId]);

  const handleCategoryChange = (category: string) => {
    // Save current checklist to allCategoriesData before switching
    const updatedCategories = {
      ...allCategoriesData,
      [selectedCategory]: checklist,
    };
    
    setSelectedCategory(category);
    
    // Load saved data for the new category if it exists
    if (updatedCategories[category]) {
      setChecklist(updatedCategories[category]);
    } else {
      // Create fresh checklist for this category
      setChecklist(
        CHECKLIST_TEMPLATES[category as keyof typeof CHECKLIST_TEMPLATES].map(item => ({
          ...item,
          category,
          status: null,
        }))
      );
    }
    
    setAllCategoriesData(updatedCategories);
  };

  const handleStatusChange = (id: string, status: 'pass' | 'fail') => {
    setChecklist(checklist.map(item => {
      if (item.id === id) {
        return {
          ...item,
          status: item.status === status ? null : status,
          severity: status === 'fail' ? 'medium' : undefined,
        };
      }
      return item;
    }));
  };

  const handleNotesChange = (id: string, notes: string) => {
    setChecklist(checklist.map(item =>
      item.id === id ? { ...item, notes } : item
    ));
  };

  const handleSeverityChange = (id: string, severity: 'low' | 'medium' | 'high') => {
    setChecklist(checklist.map(item =>
      item.id === id ? { ...item, severity } : item
    ));
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      // Collect observations from ALL categories (not just current one)
      const allObservations: any[] = [];
      
      // Add current category's data
      const currentCategoryData = {
        ...allCategoriesData,
        [selectedCategory]: checklist,
      };
      
      // Check if ALL categories are complete
      const incompleteCategoriesDetails: string[] = [];
      Object.keys(CHECKLIST_TEMPLATES).forEach((categoryName) => {
        const categoryItems = currentCategoryData[categoryName] || [];
        const templateItems = CHECKLIST_TEMPLATES[categoryName as keyof typeof CHECKLIST_TEMPLATES];
        const completedCount = categoryItems.filter((item: ChecklistItem) => item.status !== null).length;
        
        if (completedCount === 0) {
          incompleteCategoriesDetails.push(`• ${categoryName}: 0/${templateItems.length} completed`);
        } else if (completedCount < templateItems.length) {
          incompleteCategoriesDetails.push(`• ${categoryName}: ${completedCount}/${templateItems.length} completed`);
        }
      });
      
      if (incompleteCategoriesDetails.length > 0) {
        alert(
          `⚠️ Please complete ALL categories before submitting:\n\n${incompleteCategoriesDetails.join('\n')}\n\nAll observations will auto-save as you work.`
        );
        setSubmitting(false);
        return;
      }
      
      // Iterate through all categories and collect completed items
      Object.entries(currentCategoryData).forEach(([categoryName, items]) => {
        const categoryObservations = items
          .filter((item: ChecklistItem) => item.status !== null)
          .map((item: ChecklistItem) => ({
            title: item.description,
            type: categoryName,
            pillar: 'PROCESS', // Uppercase for database enum
            notes: item.notes || '',
            pass_fail: item.status === 'pass',
            severity: item.severity || 'low',
          }));
        allObservations.push(...categoryObservations);
      });

      if (allObservations.length > 0) {
        console.log('Submitting observations:', allObservations);
        const result = await observationAPI.createBatch(Number(assessmentId), allObservations);
        console.log('Submit result:', result);
        
        // DO NOT clear localStorage - keep it so users can see what they submitted
        // The data will be cleared when they start a new assessment or manually reset
        
        alert(`✅ Successfully submitted ${result.created_count || allObservations.length} observations!\n\nYour observations have been saved to the assessment.`);
        navigate(`/assessment/${assessmentId}`);
      } else {
        alert('No observations to submit. Please mark at least one item as Pass or Fail.');
      }
    } catch (error: any) {
      console.error('Failed to submit observations:', error);
      console.error('Error details:', error.response?.data);
      alert(`❌ Failed to submit observations: ${error.response?.data?.detail || error.message || 'Unknown error'}`);
    } finally {
      setSubmitting(false);
    }
  };

  const completedCount = checklist.filter(item => item.status !== null).length;
  const failCount = checklist.filter(item => item.status === 'fail').length;
  
  // Calculate total across all categories
  const totalCompletedAllCategories = Object.values({
    ...allCategoriesData,
    [selectedCategory]: checklist,
  }).reduce((sum, items) => sum + items.filter(item => item.status !== null).length, 0);
  
  const totalItemsAllCategories = Object.keys(CHECKLIST_TEMPLATES).reduce(
    (sum, cat) => sum + CHECKLIST_TEMPLATES[cat as keyof typeof CHECKLIST_TEMPLATES].length,
    0
  );

  return (
    <div style={{ padding: '40px 24px', maxWidth: '1000px', margin: '0 auto' }}>
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
          Field Observation Checklist
        </h1>
        <p style={{ color: '#5C5C5C', fontSize: '0.875rem' }}>
          Real-time compliance assessment during job shadowing
        </p>
      </div>

      {/* Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: '16px',
        marginBottom: '40px',
      }}>
        <Card style={{ padding: '24px', textAlign: 'center', background: '#F2F1EE' }}>
          <div style={{
            fontSize: '1.75rem',
            fontWeight: 600,
            color: '#0D4F4F',
            fontFamily: "'IBM Plex Mono', monospace",
          }}>
            {totalCompletedAllCategories}/{totalItemsAllCategories}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#5C5C5C', marginTop: '4px' }}>
            Completed (All Categories)
          </div>
        </Card>
        <Card style={{ padding: '24px', textAlign: 'center', background: failCount > 0 ? '#9B2C2C15' : '#F2F1EE' }}>
          <div style={{
            fontSize: '1.75rem',
            fontWeight: 600,
            color: failCount > 0 ? '#9B2C2C' : '#8A8A8A',
            fontFamily: "'IBM Plex Mono', monospace",
          }}>
            {failCount}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#5C5C5C', marginTop: '4px' }}>
            Issues Found
          </div>
        </Card>
      </div>

      {/* Category Selector */}
      <div style={{ marginBottom: '32px' }}>
        <label style={{
          display: 'block',
          marginBottom: '12px',
          fontWeight: 500,
          fontSize: '0.875rem',
          color: '#1A1A1A',
        }}>
          Checklist Category
        </label>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          {Object.keys(CHECKLIST_TEMPLATES).map((category) => (
            <button
              key={category}
              onClick={() => handleCategoryChange(category)}
              style={{
                padding: '12px 24px',
                border: `2px solid ${selectedCategory === category ? '#0D4F4F' : '#E5E4E0'}`,
                borderRadius: '8px',
                background: selectedCategory === category ? '#0D4F4F' : '#fff',
                color: selectedCategory === category ? '#fff' : '#1A1A1A',
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                fontFamily: "'Space Grotesk', sans-serif",
              }}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {/* Checklist Items */}
      <div style={{ display: 'grid', gap: '16px', marginBottom: '40px' }}>
        {checklist.map((item) => (
          <Card key={item.id} style={{ padding: '24px' }}>
            <div style={{ marginBottom: '16px' }}>
              <p style={{ fontSize: '1rem', fontWeight: 500, marginBottom: '12px' }}>
                {item.description}
              </p>

              {/* Pass/Fail Buttons */}
              <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
                <button
                  onClick={() => handleStatusChange(item.id, 'pass')}
                  style={{
                    flex: 1,
                    padding: '12px',
                    border: `2px solid ${item.status === 'pass' ? '#2D6A4F' : '#E5E4E0'}`,
                    borderRadius: '6px',
                    background: item.status === 'pass' ? '#2D6A4F' : '#fff',
                    color: item.status === 'pass' ? '#fff' : '#1A1A1A',
                    fontWeight: 500,
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                  }}
                >
                  ✓ Pass
                </button>
                <button
                  onClick={() => handleStatusChange(item.id, 'fail')}
                  style={{
                    flex: 1,
                    padding: '12px',
                    border: `2px solid ${item.status === 'fail' ? '#9B2C2C' : '#E5E4E0'}`,
                    borderRadius: '6px',
                    background: item.status === 'fail' ? '#9B2C2C' : '#fff',
                    color: item.status === 'fail' ? '#fff' : '#1A1A1A',
                    fontWeight: 500,
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                  }}
                >
                  ✕ Fail
                </button>
              </div>

              {/* Severity Selection (if failed) */}
              {item.status === 'fail' && (
                <div style={{ marginBottom: '12px' }}>
                  <label style={{
                    display: 'block',
                    marginBottom: '8px',
                    fontSize: '0.75rem',
                    fontWeight: 500,
                    color: '#5C5C5C',
                  }}>
                    Severity Level
                  </label>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    {(['low', 'medium', 'high'] as const).map((sev) => (
                      <button
                        key={sev}
                        onClick={() => handleSeverityChange(item.id, sev)}
                        style={{
                          flex: 1,
                          padding: '8px',
                          border: `2px solid ${item.severity === sev ? '#C65D3B' : '#E5E4E0'}`,
                          borderRadius: '4px',
                          background: item.severity === sev ? '#C65D3B' : '#fff',
                          color: item.severity === sev ? '#fff' : '#1A1A1A',
                          fontSize: '0.75rem',
                          fontWeight: 500,
                          cursor: 'pointer',
                          textTransform: 'capitalize',
                          transition: 'all 0.2s ease',
                        }}
                      >
                        {sev}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Notes Textarea (if status selected) */}
              {item.status !== null && (
                <textarea
                  value={item.notes || ''}
                  onChange={(e) => handleNotesChange(item.id, e.target.value)}
                  placeholder={item.status === 'fail' ? 'Describe the issue and corrective action needed...' : 'Optional notes...'}
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: '1px solid #E5E4E0',
                    borderRadius: '4px',
                    fontSize: '0.875rem',
                    fontFamily: "'Space Grotesk', sans-serif",
                    resize: 'vertical',
                    minHeight: '80px',
                  }}
                />
              )}
            </div>
          </Card>
        ))}
      </div>

      {/* Submit Button */}
      <div style={{ display: 'flex', gap: '12px', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: '0.875rem', color: '#5C5C5C' }}>
          {totalCompletedAllCategories === totalItemsAllCategories ? (
            <span style={{ color: '#2D6A4F', fontWeight: 500 }}>✓ All categories complete</span>
          ) : (
            <span>Complete all {totalItemsAllCategories} items across all categories to submit</span>
          )}
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <Button
            variant="outline"
            onClick={() => navigate(`/assessment/${assessmentId}`)}
          >
            Save & Exit
          </Button>
          <Button
            onClick={handleSubmit}
            loading={submitting}
            disabled={submitting || totalCompletedAllCategories !== totalItemsAllCategories}
          >
            Submit All {totalCompletedAllCategories} Observations
          </Button>
        </div>
      </div>
    </div>
  );
};
