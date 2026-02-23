import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { toast } from 'sonner';
import { ChevronLeft, ChevronRight, CheckCircle2, Clock, AlertCircle } from 'lucide-react';

const ClientAssessmentTaker = ({ assessmentId, onComplete, onCancel }) => {
  const [assessment, setAssessment] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showStartScreen, setShowStartScreen] = useState(true);
  const [showConfirmation, setShowConfirmation] = useState(false);

  useEffect(() => {
    fetchAssessment();
  }, [assessmentId]);

  const fetchAssessment = async () => {
    try {
      const res = await axios.get(`${API}/assessments/${assessmentId}`);
      setAssessment(res.data);
      
      // Restore saved progress if any
      if (res.data.saved_answers && res.data.saved_answers.length > 0) {
        setAnswers(res.data.saved_answers);
        setCurrentIndex(res.data.current_question_index || 0);
        setShowStartScreen(false);
      } else {
        // Initialize empty answers array
        setAnswers(new Array(res.data.questions?.length || 0).fill(null));
      }
    } catch (error) {
      toast.error('Failed to load assessment');
      onCancel?.();
    } finally {
      setLoading(false);
    }
  };

  // Auto-save with debounce
  const saveProgress = useCallback(async (answersToSave, currentIdx) => {
    try {
      await axios.post(`${API}/assessments/${assessmentId}/save-progress`, {
        answers: answersToSave,
        current_index: currentIdx
      });
    } catch (error) {
      // Silent fail for auto-save
      console.log('Auto-save failed');
    }
  }, [assessmentId]);

  // Debounced save
  useEffect(() => {
    if (!showStartScreen && assessment) {
      const timer = setTimeout(() => {
        saveProgress(answers, currentIndex);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [answers, currentIndex, showStartScreen, assessment, saveProgress]);

  const handleSelectAnswer = (questionId, value, label) => {
    const newAnswers = [...answers];
    newAnswers[currentIndex] = {
      question_id: questionId,
      value: value,
      label: label
    };
    setAnswers(newAnswers);
  };

  const handleNext = () => {
    if (currentIndex < assessment.questions.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const handleSubmit = async () => {
    // Check if all questions are answered
    const unanswered = answers.filter(a => a === null).length;
    if (unanswered > 0) {
      toast.error(`Please answer all questions (${unanswered} remaining)`);
      // Navigate to first unanswered question
      const firstUnanswered = answers.findIndex(a => a === null);
      setCurrentIndex(firstUnanswered);
      return;
    }

    setSubmitting(true);
    try {
      // Convert answers to simple response values for backend
      const responses = answers.map(a => a?.value || 0);
      await axios.post(`${API}/assessments/${assessmentId}/submit`, {
        responses: responses,
        notes: ''
      });
      setShowConfirmation(true);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit assessment');
    } finally {
      setSubmitting(false);
    }
  };

  const handleFinish = () => {
    setShowConfirmation(false);
    onComplete?.();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading assessment...</p>
        </div>
      </div>
    );
  }

  if (!assessment) {
    return null;
  }

  const questions = assessment.questions || [];
  const currentQuestion = questions[currentIndex];
  const progress = ((currentIndex + 1) / questions.length) * 100;
  const answeredCount = answers.filter(a => a !== null).length;

  // Start Screen
  if (showStartScreen) {
    return (
      <div className="max-w-2xl mx-auto p-4 sm:p-6" data-testid="assessment-start-screen">
        <Card className="p-6 sm:p-10 bg-gradient-to-br from-white to-green-50/30 border-none shadow-xl">
          <div className="text-center space-y-6">
            {/* Header */}
            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-8 h-8 text-primary" />
            </div>
            
            <div>
              <h2 className="text-2xl sm:text-3xl font-serif text-primary mb-2">
                {assessment.friendly_name}
              </h2>
              <p className="text-muted-foreground text-sm sm:text-base">
                {assessment.purpose}
              </p>
            </div>

            {/* Info Cards */}
            <div className="flex justify-center gap-4 text-sm">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Clock className="w-4 h-4" />
                <span>{assessment.time_estimate}</span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <AlertCircle className="w-4 h-4" />
                <span>{questions.length} questions</span>
              </div>
            </div>

            {/* Reassurance Text */}
            <Card className="bg-amber-50/50 border-amber-200/50 p-4 text-left">
              <p className="text-amber-800 text-sm leading-relaxed">
                <strong>There are no right or wrong answers.</strong> Answer honestly based on how you've been feeling.
              </p>
            </Card>

            {/* Disclaimer */}
            <p className="text-xs text-muted-foreground italic">
              This helps your therapist understand your experience. It is not a diagnosis.
            </p>

            {/* Instruction */}
            <p className="text-sm text-muted-foreground">
              {assessment.instruction}
            </p>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 pt-4">
              <Button
                onClick={() => setShowStartScreen(false)}
                className="flex-1 h-12 text-base rounded-full"
                data-testid="begin-assessment-btn"
              >
                Begin Assessment
              </Button>
              <Button
                variant="outline"
                onClick={onCancel}
                className="flex-1 h-12 text-base rounded-full"
                data-testid="cancel-assessment-btn"
              >
                Maybe Later
              </Button>
            </div>

            {/* Saved Progress Notice */}
            {assessment.saved_answers?.length > 0 && (
              <p className="text-sm text-primary">
                You have saved progress. Click Begin to continue where you left off.
              </p>
            )}
          </div>
        </Card>
      </div>
    );
  }

  // Confirmation Screen
  if (showConfirmation) {
    return (
      <div className="max-w-2xl mx-auto p-4 sm:p-6" data-testid="assessment-confirmation">
        <Card className="p-6 sm:p-10 bg-gradient-to-br from-white to-green-50/30 border-none shadow-xl">
          <div className="text-center space-y-6">
            <div className="w-20 h-20 bg-success/10 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-10 h-10 text-success" />
            </div>
            
            <div>
              <h2 className="text-2xl sm:text-3xl font-serif text-primary mb-2">
                Thank You
              </h2>
              <p className="text-muted-foreground text-base sm:text-lg">
                Your responses have been submitted successfully.
              </p>
            </div>

            <Card className="bg-blue-50/50 border-blue-200/50 p-4">
              <p className="text-blue-800 text-sm">
                Your therapist will review your responses and discuss them with you in your next session.
              </p>
            </Card>

            <Button
              onClick={handleFinish}
              className="h-12 px-8 text-base rounded-full"
              data-testid="finish-assessment-btn"
            >
              Done
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  // Question Screen
  return (
    <div className="max-w-2xl mx-auto p-4 sm:p-6" data-testid="assessment-question-screen">
      {/* Progress Header */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-muted-foreground">
            Question {currentIndex + 1} of {questions.length}
          </span>
          <span className="text-sm text-muted-foreground">
            {answeredCount} answered
          </span>
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      {/* Question Card */}
      <Card className="p-6 sm:p-8 bg-white shadow-lg border-none mb-6">
        <div className="space-y-6">
          {/* Question Text */}
          <h3 className="text-lg sm:text-xl font-medium text-foreground leading-relaxed" data-testid="question-text">
            {currentQuestion?.text}
          </h3>

          {/* Answer Options */}
          <div className="space-y-3">
            {currentQuestion?.options?.map((option, idx) => {
              const isSelected = answers[currentIndex]?.value === option.value;
              return (
                <button
                  key={idx}
                  onClick={() => handleSelectAnswer(currentQuestion.id, option.value, option.label)}
                  className={`w-full p-4 text-left rounded-xl border-2 transition-all duration-200 ${
                    isSelected
                      ? 'border-primary bg-primary/5 ring-2 ring-primary/20'
                      : 'border-border/50 hover:border-primary/30 hover:bg-surface/50'
                  }`}
                  data-testid={`option-${idx}`}
                >
                  <span className={`text-base ${isSelected ? 'text-primary font-medium' : 'text-foreground'}`}>
                    {option.label}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between items-center gap-4">
        <Button
          variant="outline"
          onClick={handlePrevious}
          disabled={currentIndex === 0}
          className="h-12 px-6 rounded-full"
          data-testid="prev-question-btn"
        >
          <ChevronLeft className="w-4 h-4 mr-1" />
          Back
        </Button>

        {currentIndex === questions.length - 1 ? (
          <Button
            onClick={handleSubmit}
            disabled={submitting || answers[currentIndex] === null}
            className="h-12 px-8 rounded-full"
            data-testid="submit-assessment-btn"
          >
            {submitting ? 'Submitting...' : 'Submit'}
          </Button>
        ) : (
          <Button
            onClick={handleNext}
            disabled={answers[currentIndex] === null}
            className="h-12 px-6 rounded-full"
            data-testid="next-question-btn"
          >
            Next
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        )}
      </div>

      {/* Auto-save indicator */}
      <p className="text-center text-xs text-muted-foreground mt-4">
        Your progress is being saved automatically
      </p>
    </div>
  );
};

export default ClientAssessmentTaker;
