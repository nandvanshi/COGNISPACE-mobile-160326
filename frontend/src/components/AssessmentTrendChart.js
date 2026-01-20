import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { toast } from 'sonner';
import { TrendingDown, TrendingUp, Minus, BarChart3 } from 'lucide-react';

// Simple line chart for assessment trends
const AssessmentTrendChart = ({ clientId }) => {
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState(null);

  useEffect(() => {
    if (clientId) {
      fetchAssessments();
    }
  }, [clientId]);

  const fetchAssessments = async () => {
    try {
      const res = await axios.get(`${API}/clients/${clientId}/assessments`);
      // Filter to only completed assessments with scores
      const completed = res.data.filter(a => a.status === 'completed' && a.score !== null);
      setAssessments(completed);
      
      // Auto-select the most common assessment type
      if (completed.length > 0) {
        const typeCounts = completed.reduce((acc, a) => {
          acc[a.assessment_type] = (acc[a.assessment_type] || 0) + 1;
          return acc;
        }, {});
        const mostCommon = Object.entries(typeCounts).sort((a, b) => b[1] - a[1])[0]?.[0];
        setSelectedType(mostCommon);
      }
    } catch (error) {
      console.error('Failed to fetch assessment trends:', error);
    } finally {
      setLoading(false);
    }
  };

  // Get unique assessment types
  const assessmentTypes = [...new Set(assessments.map(a => a.assessment_type))];

  // Filter assessments by selected type
  const filteredAssessments = assessments
    .filter(a => a.assessment_type === selectedType)
    .sort((a, b) => new Date(a.completed_at) - new Date(b.completed_at));

  // Calculate trend (comparing first and last)
  const calculateTrend = () => {
    if (filteredAssessments.length < 2) return null;
    const first = filteredAssessments[0].score;
    const last = filteredAssessments[filteredAssessments.length - 1].score;
    const change = last - first;
    const percentChange = ((change / first) * 100).toFixed(1);
    return { change, percentChange, direction: change < 0 ? 'down' : change > 0 ? 'up' : 'stable' };
  };

  const trend = calculateTrend();

  // Get max score for scaling
  const maxScore = Math.max(...filteredAssessments.map(a => a.score), 1);

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-muted rounded w-1/3 mb-4"></div>
          <div className="h-32 bg-muted rounded"></div>
        </div>
      </Card>
    );
  }

  if (assessments.length === 0) {
    return (
      <Card className="p-6 text-center">
        <BarChart3 className="w-12 h-12 mx-auto text-muted-foreground mb-3" />
        <p className="text-muted-foreground">No completed assessments yet</p>
        <p className="text-sm text-muted-foreground mt-1">Trends will appear after multiple assessments</p>
      </Card>
    );
  }

  return (
    <Card className="p-6" data-testid="assessment-trend-chart">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <BarChart3 className="text-primary" size={20} />
          <h3 className="font-semibold text-lg">Assessment Trends</h3>
        </div>
        
        {/* Assessment Type Selector */}
        {assessmentTypes.length > 1 && (
          <select
            value={selectedType || ''}
            onChange={(e) => setSelectedType(e.target.value)}
            className="text-sm border rounded-lg px-3 py-1.5 bg-white"
          >
            {assessmentTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        )}
      </div>

      {/* Trend Summary */}
      {trend && (
        <div className="flex items-center gap-3 mb-4 p-3 bg-muted/30 rounded-lg">
          {trend.direction === 'down' ? (
            <>
              <div className="p-2 bg-success/10 rounded-full">
                <TrendingDown className="text-success" size={20} />
              </div>
              <div>
                <p className="font-medium text-success">Improving</p>
                <p className="text-sm text-muted-foreground">
                  Score decreased by {Math.abs(trend.change)} points ({Math.abs(trend.percentChange)}%)
                </p>
              </div>
            </>
          ) : trend.direction === 'up' ? (
            <>
              <div className="p-2 bg-warning/10 rounded-full">
                <TrendingUp className="text-warning" size={20} />
              </div>
              <div>
                <p className="font-medium text-warning">Needs attention</p>
                <p className="text-sm text-muted-foreground">
                  Score increased by {trend.change} points ({trend.percentChange}%)
                </p>
              </div>
            </>
          ) : (
            <>
              <div className="p-2 bg-info/10 rounded-full">
                <Minus className="text-info" size={20} />
              </div>
              <div>
                <p className="font-medium text-info">Stable</p>
                <p className="text-sm text-muted-foreground">No significant change</p>
              </div>
            </>
          )}
        </div>
      )}

      {/* Simple Chart */}
      <div className="relative h-40 mt-4">
        {filteredAssessments.length < 2 ? (
          <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
            Need at least 2 assessments to show trend
          </div>
        ) : (
          <div className="flex items-end justify-between h-full gap-2">
            {filteredAssessments.map((assess, idx) => {
              const height = (assess.score / maxScore) * 100;
              const isFirst = idx === 0;
              const isLast = idx === filteredAssessments.length - 1;
              
              return (
                <div key={assess.id} className="flex-1 flex flex-col items-center gap-1">
                  {/* Score label on top */}
                  <span className={`text-xs font-medium ${isLast ? 'text-primary' : 'text-muted-foreground'}`}>
                    {assess.score}
                  </span>
                  
                  {/* Bar */}
                  <div 
                    className={`w-full rounded-t transition-all ${
                      isLast ? 'bg-primary' : 
                      isFirst ? 'bg-primary/30' : 
                      'bg-primary/50'
                    }`}
                    style={{ height: `${height}%`, minHeight: '4px' }}
                    title={`${assess.assessment_type}: ${assess.score}`}
                  />
                  
                  {/* Date label */}
                  <span className="text-[10px] text-muted-foreground mt-1">
                    {new Date(assess.completed_at).toLocaleDateString('en-IN', { 
                      day: '2-digit', 
                      month: 'short' 
                    })}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 mt-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1">
          <div className="w-3 h-3 bg-primary/30 rounded"></div>
          First
        </span>
        <span className="flex items-center gap-1">
          <div className="w-3 h-3 bg-primary rounded"></div>
          Latest
        </span>
      </div>
      
      <p className="text-xs text-muted-foreground text-center mt-3">
        {selectedType} - {filteredAssessments.length} assessment{filteredAssessments.length !== 1 ? 's' : ''}
      </p>
    </Card>
  );
};

export default AssessmentTrendChart;
