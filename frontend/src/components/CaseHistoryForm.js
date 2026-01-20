import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Checkbox } from './ui/checkbox';
import { toast } from 'sonner';
import { 
  ChevronLeft, ChevronRight, Save, Check, Download, FileText,
  Loader2, User, MessageSquare, History, Brain, Stethoscope,
  Users, BookOpen, ClipboardCheck, Target, FileCheck
} from 'lucide-react';

const SECTIONS = [
  { id: 'basic_identification', label: 'Basic Identification', icon: User },
  { id: 'presenting_complaints', label: 'Presenting Complaints', icon: MessageSquare },
  { id: 'history_of_present_illness', label: 'History of Present Illness', icon: History },
  { id: 'past_psychiatric_history', label: 'Past Psychiatric History', icon: Brain },
  { id: 'medical_history', label: 'Medical History', icon: Stethoscope },
  { id: 'family_history', label: 'Family History', icon: Users },
  { id: 'personal_developmental_history', label: 'Personal & Developmental History', icon: BookOpen },
  { id: 'mental_status_examination', label: 'Mental Status Examination', icon: ClipboardCheck },
  { id: 'provisional_formulation', label: 'Provisional Formulation', icon: Target },
  { id: 'initial_therapy_plan', label: 'Initial Therapy Plan', icon: Target },
  { id: 'consent_disclaimer', label: 'Consent & Disclaimer', icon: FileCheck },
];

const CaseHistoryForm = ({ clientId, clientName, onComplete, onClose, isReadOnly = false }) => {
  const [currentSection, setCurrentSection] = useState(0);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [showFullView, setShowFullView] = useState(false);
  const printRef = useRef(null);

  // Fetch existing case history
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get(`${API}/case-history/${clientId}`);
        if (response.data) {
          setFormData({
            basic_identification: response.data.basic_identification || { name: clientName || '' },
            presenting_complaints: response.data.presenting_complaints || {},
            history_of_present_illness: response.data.history_of_present_illness || {},
            past_psychiatric_history: response.data.past_psychiatric_history || {},
            medical_history: response.data.medical_history || {},
            family_history: response.data.family_history || {},
            personal_developmental_history: response.data.personal_developmental_history || {},
            mental_status_examination: response.data.mental_status_examination || {},
            provisional_formulation: response.data.provisional_formulation || {},
            initial_therapy_plan: response.data.initial_therapy_plan || {},
            consent_disclaimer: response.data.consent_disclaimer || { informed_consent_taken: false, confidentiality_explained: false }
          });
          setIsComplete(response.data.is_complete || false);
        }
      } catch (error) {
        // Initialize with defaults
        setFormData({
          basic_identification: { name: clientName || '' },
          presenting_complaints: {},
          history_of_present_illness: {},
          past_psychiatric_history: {},
          medical_history: {},
          family_history: {},
          personal_developmental_history: {},
          mental_status_examination: {},
          provisional_formulation: {},
          initial_therapy_plan: {},
          consent_disclaimer: { informed_consent_taken: false, confidentiality_explained: false }
        });
      } finally {
        setLoading(false);
      }
    };

    if (clientId) {
      fetchData();
    }
  }, [clientId, clientName]);

  const updateField = (section, field, value) => {
    setFormData(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  };

  const saveCurrentSection = async () => {
    if (isReadOnly) return true;
    
    setSaving(true);
    const sectionId = SECTIONS[currentSection].id;
    
    try {
      await axios.patch(
        `${API}/case-history/${clientId}/section?section=${sectionId}`, 
        formData[sectionId] || {}
      );
      return true;
    } catch (error) {
      toast.error('Failed to save section');
      return false;
    } finally {
      setSaving(false);
    }
  };

  const handleNext = async () => {
    const saved = await saveCurrentSection();
    if (saved && currentSection < SECTIONS.length - 1) {
      setCurrentSection(prev => prev + 1);
      window.scrollTo(0, 0);
    }
  };

  const handlePrev = () => {
    if (currentSection > 0) {
      setCurrentSection(prev => prev - 1);
      window.scrollTo(0, 0);
    }
  };

  const handleComplete = async () => {
    if (isReadOnly) return;
    
    // Validate required fields
    if (!formData.basic_identification?.name) {
      toast.error('Please enter client name');
      setCurrentSection(0);
      return;
    }
    
    if (!formData.presenting_complaints?.main_problems) {
      toast.error('Please enter main problems/complaints');
      setCurrentSection(1);
      return;
    }
    
    if (!formData.consent_disclaimer?.informed_consent_taken) {
      toast.error('Please confirm informed consent');
      setCurrentSection(10);
      return;
    }

    setSaving(true);
    try {
      // Save current section first
      await saveCurrentSection();
      
      // Mark as complete
      await axios.patch(`${API}/case-history/${clientId}/complete`);
      
      toast.success('Case History completed successfully');
      setIsComplete(true);
      setShowFullView(true);
      
      if (onComplete) {
        onComplete();
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to complete case history');
    } finally {
      setSaving(false);
    }
  };

  const handlePrint = () => {
    const printContent = printRef.current;
    if (!printContent) return;

    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
      <html>
        <head>
          <title>Case History - ${clientName}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 20px; line-height: 1.6; }
            h1 { color: #16a34a; border-bottom: 2px solid #16a34a; padding-bottom: 10px; }
            h2 { color: #333; margin-top: 30px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
            .field { margin: 10px 0; }
            .label { font-weight: bold; color: #555; }
            .value { margin-left: 10px; }
            @media print { body { padding: 0; } }
          </style>
        </head>
        <body>
          ${printContent.innerHTML}
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.print();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  // Full View Mode
  if (showFullView) {
    return (
      <div className="min-h-screen bg-background p-4 sm:p-6 lg:p-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <div>
              <h1 className="text-2xl sm:text-3xl font-serif text-primary">Case History</h1>
              <p className="text-muted-foreground">{clientName}</p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={handlePrint} className="gap-2">
                <Download size={18} />
                Download PDF
              </Button>
              <Button variant="outline" onClick={() => setShowFullView(false)}>
                Edit
              </Button>
              {onClose && (
                <Button variant="ghost" onClick={onClose}>
                  Close
                </Button>
              )}
            </div>
          </div>

          {/* Print Content */}
          <div ref={printRef} className="bg-white rounded-lg border p-6 space-y-8">
            <h1>Case History - {clientName}</h1>
            
            {SECTIONS.map(section => {
              const data = formData[section.id] || {};
              const hasData = Object.keys(data).some(k => data[k]);
              
              if (!hasData) return null;
              
              return (
                <div key={section.id}>
                  <h2>{section.label}</h2>
                  {Object.entries(data).map(([key, value]) => {
                    if (!value || value === '' || value === false) return null;
                    const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    return (
                      <div key={key} className="field">
                        <span className="label">{label}:</span>
                        <span className="value">{typeof value === 'boolean' ? 'Yes' : value}</span>
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  const currentSectionData = formData[SECTIONS[currentSection].id] || {};
  const SectionIcon = SECTIONS[currentSection].icon;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="sticky top-0 bg-background border-b z-10">
        <div className="max-w-3xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {onClose && (
                <Button variant="ghost" size="sm" onClick={onClose}>
                  <ChevronLeft size={20} />
                </Button>
              )}
              <div>
                <h1 className="text-lg sm:text-xl font-semibold text-foreground">Case History</h1>
                <p className="text-sm text-muted-foreground">{clientName}</p>
              </div>
            </div>
            <div className="text-sm text-muted-foreground">
              {currentSection + 1} / {SECTIONS.length}
            </div>
          </div>
          
          {/* Progress Bar */}
          <div className="mt-3 h-1 bg-muted rounded-full overflow-hidden">
            <div 
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${((currentSection + 1) / SECTIONS.length) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Section Title */}
      <div className="max-w-3xl mx-auto px-4 py-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
            <SectionIcon size={20} className="text-primary" />
          </div>
          <h2 className="text-xl sm:text-2xl font-semibold">{SECTIONS[currentSection].label}</h2>
        </div>

        {/* Form Fields */}
        <div className="space-y-6">
          {renderSectionFields(SECTIONS[currentSection].id, currentSectionData, updateField, isReadOnly)}
        </div>
      </div>

      {/* Footer Navigation */}
      <div className="sticky bottom-0 bg-background border-t">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between gap-4">
            <Button
              variant="outline"
              onClick={handlePrev}
              disabled={currentSection === 0}
              className="gap-2"
            >
              <ChevronLeft size={18} />
              <span className="hidden sm:inline">Previous</span>
            </Button>

            <div className="flex gap-2">
              {isComplete && (
                <Button variant="outline" onClick={() => setShowFullView(true)} className="gap-2">
                  <FileText size={18} />
                  <span className="hidden sm:inline">View Full</span>
                </Button>
              )}
            </div>

            {currentSection < SECTIONS.length - 1 ? (
              <Button onClick={handleNext} disabled={saving} className="gap-2">
                {saving ? <Loader2 size={18} className="animate-spin" /> : null}
                <span className="hidden sm:inline">Next</span>
                <ChevronRight size={18} />
              </Button>
            ) : (
              <Button 
                onClick={handleComplete} 
                disabled={saving || isReadOnly}
                className="gap-2 bg-green-600 hover:bg-green-700"
              >
                {saving ? <Loader2 size={18} className="animate-spin" /> : <Check size={18} />}
                Complete
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Render fields for each section
const renderSectionFields = (sectionId, data, updateField, isReadOnly) => {
  const fieldClass = "w-full";
  const labelClass = "text-sm font-medium text-foreground mb-1.5 block";
  
  switch (sectionId) {
    case 'basic_identification':
      return (
        <>
          <div>
            <Label className={labelClass}>Full Name *</Label>
            <Input
              className={fieldClass}
              value={data.name || ''}
              onChange={(e) => updateField(sectionId, 'name', e.target.value)}
              disabled={isReadOnly}
              placeholder="Enter client's full name"
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label className={labelClass}>Age / Date of Birth</Label>
              <Input
                className={fieldClass}
                value={data.age_dob || ''}
                onChange={(e) => updateField(sectionId, 'age_dob', e.target.value)}
                disabled={isReadOnly}
                placeholder="e.g., 28 years or 15/03/1995"
              />
            </div>
            <div>
              <Label className={labelClass}>Gender</Label>
              <Select
                value={data.gender || ''}
                onValueChange={(value) => updateField(sectionId, 'gender', value)}
                disabled={isReadOnly}
              >
                <SelectTrigger className={fieldClass}>
                  <SelectValue placeholder="Select gender" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="male">Male</SelectItem>
                  <SelectItem value="female">Female</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                  <SelectItem value="prefer_not_to_say">Prefer not to say</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label className={labelClass}>Marital Status</Label>
              <Select
                value={data.marital_status || ''}
                onValueChange={(value) => updateField(sectionId, 'marital_status', value)}
                disabled={isReadOnly}
              >
                <SelectTrigger className={fieldClass}>
                  <SelectValue placeholder="Select status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="single">Single</SelectItem>
                  <SelectItem value="married">Married</SelectItem>
                  <SelectItem value="divorced">Divorced</SelectItem>
                  <SelectItem value="widowed">Widowed</SelectItem>
                  <SelectItem value="separated">Separated</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className={labelClass}>Education</Label>
              <Input
                className={fieldClass}
                value={data.education || ''}
                onChange={(e) => updateField(sectionId, 'education', e.target.value)}
                disabled={isReadOnly}
                placeholder="Highest qualification"
              />
            </div>
          </div>
          <div>
            <Label className={labelClass}>Occupation</Label>
            <Input
              className={fieldClass}
              value={data.occupation || ''}
              onChange={(e) => updateField(sectionId, 'occupation', e.target.value)}
              disabled={isReadOnly}
              placeholder="Current occupation"
            />
          </div>
          <div>
            <Label className={labelClass}>Address</Label>
            <Textarea
              className={fieldClass}
              value={data.address || ''}
              onChange={(e) => updateField(sectionId, 'address', e.target.value)}
              disabled={isReadOnly}
              placeholder="Full address"
              rows={2}
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label className={labelClass}>Contact Number</Label>
              <Input
                className={fieldClass}
                value={data.contact || ''}
                onChange={(e) => updateField(sectionId, 'contact', e.target.value)}
                disabled={isReadOnly}
                placeholder="Phone number"
              />
            </div>
            <div>
              <Label className={labelClass}>Emergency Contact</Label>
              <Input
                className={fieldClass}
                value={data.emergency_contact || ''}
                onChange={(e) => updateField(sectionId, 'emergency_contact', e.target.value)}
                disabled={isReadOnly}
                placeholder="Emergency contact number"
              />
            </div>
          </div>
          <div>
            <Label className={labelClass}>Referred By</Label>
            <Input
              className={fieldClass}
              value={data.referred_by || ''}
              onChange={(e) => updateField(sectionId, 'referred_by', e.target.value)}
              disabled={isReadOnly}
              placeholder="Doctor/Self/Family/Friend"
            />
          </div>
        </>
      );

    case 'presenting_complaints':
      return (
        <>
          <div>
            <Label className={labelClass}>Main Problems / Complaints *</Label>
            <Textarea
              className={fieldClass}
              value={data.main_problems || ''}
              onChange={(e) => updateField(sectionId, 'main_problems', e.target.value)}
              disabled={isReadOnly}
              placeholder="Describe the main problems in client's own words"
              rows={4}
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label className={labelClass}>Duration</Label>
              <Input
                className={fieldClass}
                value={data.duration || ''}
                onChange={(e) => updateField(sectionId, 'duration', e.target.value)}
                disabled={isReadOnly}
                placeholder="e.g., 6 months, 2 years"
              />
            </div>
            <div>
              <Label className={labelClass}>Severity</Label>
              <Select
                value={data.severity || ''}
                onValueChange={(value) => updateField(sectionId, 'severity', value)}
                disabled={isReadOnly}
              >
                <SelectTrigger className={fieldClass}>
                  <SelectValue placeholder="Select severity" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="mild">Mild</SelectItem>
                  <SelectItem value="moderate">Moderate</SelectItem>
                  <SelectItem value="severe">Severe</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div>
            <Label className={labelClass}>Frequency</Label>
            <Input
              className={fieldClass}
              value={data.frequency || ''}
              onChange={(e) => updateField(sectionId, 'frequency', e.target.value)}
              disabled={isReadOnly}
              placeholder="e.g., Daily, Weekly, Occasional"
            />
          </div>
          <div>
            <Label className={labelClass}>Triggers</Label>
            <Textarea
              className={fieldClass}
              value={data.triggers || ''}
              onChange={(e) => updateField(sectionId, 'triggers', e.target.value)}
              disabled={isReadOnly}
              placeholder="What triggers or worsens the symptoms?"
              rows={3}
            />
          </div>
        </>
      );

    case 'history_of_present_illness':
      return (
        <>
          <div>
            <Label className={labelClass}>Onset</Label>
            <Textarea
              className={fieldClass}
              value={data.onset || ''}
              onChange={(e) => updateField(sectionId, 'onset', e.target.value)}
              disabled={isReadOnly}
              placeholder="When and how did the problems start?"
              rows={3}
            />
          </div>
          <div>
            <Label className={labelClass}>Course</Label>
            <Textarea
              className={fieldClass}
              value={data.course || ''}
              onChange={(e) => updateField(sectionId, 'course', e.target.value)}
              disabled={isReadOnly}
              placeholder="How have symptoms progressed over time?"
              rows={3}
            />
          </div>
          <div>
            <Label className={labelClass}>Previous Episodes</Label>
            <Textarea
              className={fieldClass}
              value={data.previous_episodes || ''}
              onChange={(e) => updateField(sectionId, 'previous_episodes', e.target.value)}
              disabled={isReadOnly}
              placeholder="Any previous similar episodes?"
              rows={2}
            />
          </div>
          <div>
            <Label className={labelClass}>Factors that Improve Symptoms</Label>
            <Textarea
              className={fieldClass}
              value={data.improving_factors || ''}
              onChange={(e) => updateField(sectionId, 'improving_factors', e.target.value)}
              disabled={isReadOnly}
              placeholder="What helps reduce the symptoms?"
              rows={2}
            />
          </div>
          <div>
            <Label className={labelClass}>Factors that Worsen Symptoms</Label>
            <Textarea
              className={fieldClass}
              value={data.worsening_factors || ''}
              onChange={(e) => updateField(sectionId, 'worsening_factors', e.target.value)}
              disabled={isReadOnly}
              placeholder="What makes symptoms worse?"
              rows={2}
            />
          </div>
          <div>
            <Label className={labelClass}>Prior Therapy/Treatment</Label>
            <Textarea
              className={fieldClass}
              value={data.prior_treatment || ''}
              onChange={(e) => updateField(sectionId, 'prior_treatment', e.target.value)}
              disabled={isReadOnly}
              placeholder="Any previous therapy or medication for these issues?"
              rows={2}
            />
          </div>
        </>
      );

    case 'past_psychiatric_history':
      return (
        <>
          <div>
            <Label className={labelClass}>Previous Therapy/Counseling</Label>
            <Textarea
              className={fieldClass}
              value={data.previous_therapy || ''}
              onChange={(e) => updateField(sectionId, 'previous_therapy', e.target.value)}
              disabled={isReadOnly}
              placeholder="Details of any previous therapy or counseling"
              rows={3}
            />
          </div>
          <div>
            <Label className={labelClass}>Previous Diagnosis</Label>
            <Textarea
              className={fieldClass}
              value={data.previous_diagnosis || ''}
              onChange={(e) => updateField(sectionId, 'previous_diagnosis', e.target.value)}
              disabled={isReadOnly}
              placeholder="Any previous psychiatric diagnoses"
              rows={2}
            />
          </div>
          <div>
            <Label className={labelClass}>Hospitalizations</Label>
            <Textarea
              className={fieldClass}
              value={data.hospitalizations || ''}
              onChange={(e) => updateField(sectionId, 'hospitalizations', e.target.value)}
              disabled={isReadOnly}
              placeholder="Any psychiatric hospitalizations"
              rows={2}
            />
          </div>
          <div>
            <Label className={labelClass}>Past Medications</Label>
            <Textarea
              className={fieldClass}
              value={data.past_medications || ''}
              onChange={(e) => updateField(sectionId, 'past_medications', e.target.value)}
              disabled={isReadOnly}
              placeholder="Previous psychiatric medications"
              rows={2}
            />
          </div>
          <div>
            <Label className={labelClass}>Current Medications</Label>
            <Textarea
              className={fieldClass}
              value={data.current_medications || ''}
              onChange={(e) => updateField(sectionId, 'current_medications', e.target.value)}
              disabled={isReadOnly}
              placeholder="Current psychiatric medications"
              rows={2}
            />
          </div>
        </>
      );

    case 'medical_history':
      return (
        <>
          <div>
            <Label className={labelClass}>Chronic Illnesses</Label>
            <Textarea
              className={fieldClass}
              value={data.chronic_illnesses || ''}
              onChange={(e) => updateField(sectionId, 'chronic_illnesses', e.target.value)}
              disabled={isReadOnly}
              placeholder="e.g., Diabetes, Hypertension, Thyroid issues"
              rows={2}
            />
          </div>
          <div>
            <Label className={labelClass}>Current Medications</Label>
            <Textarea
              className={fieldClass}
              value={data.current_medications || ''}
              onChange={(e) => updateField(sectionId, 'current_medications', e.target.value)}
              disabled={isReadOnly}
              placeholder="All current medications (including non-psychiatric)"
              rows={2}
            />
          </div>
          <div>
            <Label className={labelClass}>Sleep Pattern</Label>
            <Select
              value={data.sleep_pattern || ''}
              onValueChange={(value) => updateField(sectionId, 'sleep_pattern', value)}
              disabled={isReadOnly}
            >
              <SelectTrigger className={fieldClass}>
                <SelectValue placeholder="Select sleep pattern" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="normal">Normal (6-8 hours)</SelectItem>
                <SelectItem value="insomnia">Insomnia (difficulty sleeping)</SelectItem>
                <SelectItem value="hypersomnia">Hypersomnia (excessive sleep)</SelectItem>
                <SelectItem value="disturbed">Disturbed/Interrupted</SelectItem>
                <SelectItem value="variable">Variable</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className={labelClass}>Appetite</Label>
            <Select
              value={data.appetite || ''}
              onValueChange={(value) => updateField(sectionId, 'appetite', value)}
              disabled={isReadOnly}
            >
              <SelectTrigger className={fieldClass}>
                <SelectValue placeholder="Select appetite status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="normal">Normal</SelectItem>
                <SelectItem value="increased">Increased</SelectItem>
                <SelectItem value="decreased">Decreased</SelectItem>
                <SelectItem value="variable">Variable</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className={labelClass}>Substance Use</Label>
            <Textarea
              className={fieldClass}
              value={data.substance_use || ''}
              onChange={(e) => updateField(sectionId, 'substance_use', e.target.value)}
              disabled={isReadOnly}
              placeholder="Alcohol, tobacco, caffeine, other substances (frequency and amount)"
              rows={2}
            />
          </div>
        </>
      );

    case 'family_history':
      return (
        <>
          <div>
            <Label className={labelClass}>Family Structure</Label>
            <Textarea
              className={fieldClass}
              value={data.family_structure || ''}
              onChange={(e) => updateField(sectionId, 'family_structure', e.target.value)}
              disabled={isReadOnly}
              placeholder="Describe family members, living situation"
              rows={3}
            />
          </div>
          <div>
            <Label className={labelClass}>Mental Illness in Family</Label>
            <Select
              value={data.family_mental_illness || ''}
              onValueChange={(value) => updateField(sectionId, 'family_mental_illness', value)}
              disabled={isReadOnly}
            >
              <SelectTrigger className={fieldClass}>
                <SelectValue placeholder="Select" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="yes">Yes</SelectItem>
                <SelectItem value="no">No</SelectItem>
                <SelectItem value="unknown">Unknown</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {data.family_mental_illness === 'yes' && (
            <div>
              <Label className={labelClass}>Details of Family Mental Illness</Label>
              <Textarea
                className={fieldClass}
                value={data.family_mental_illness_details || ''}
                onChange={(e) => updateField(sectionId, 'family_mental_illness_details', e.target.value)}
                disabled={isReadOnly}
                placeholder="Who and what conditions"
                rows={2}
              />
            </div>
          )}
          <div>
            <Label className={labelClass}>Relationship Dynamics</Label>
            <Textarea
              className={fieldClass}
              value={data.relationship_dynamics || ''}
              onChange={(e) => updateField(sectionId, 'relationship_dynamics', e.target.value)}
              disabled={isReadOnly}
              placeholder="Quality of relationships with family members"
              rows={3}
            />
          </div>
        </>
      );

    case 'personal_developmental_history':
      return (
        <>
          <div>
            <Label className={labelClass}>Childhood</Label>
            <Textarea
              className={fieldClass}
              value={data.childhood || ''}
              onChange={(e) => updateField(sectionId, 'childhood', e.target.value)}
              disabled={isReadOnly}
              placeholder="Early childhood experiences, developmental milestones"
              rows={3}
            />
          </div>
          <div>
            <Label className={labelClass}>Education History</Label>
            <Textarea
              className={fieldClass}
              value={data.education_history || ''}
              onChange={(e) => updateField(sectionId, 'education_history', e.target.value)}
              disabled={isReadOnly}
              placeholder="Educational journey, any difficulties"
              rows={2}
            />
          </div>
          <div>
            <Label className={labelClass}>Work History</Label>
            <Textarea
              className={fieldClass}
              value={data.work_history || ''}
              onChange={(e) => updateField(sectionId, 'work_history', e.target.value)}
              disabled={isReadOnly}
              placeholder="Employment history, job satisfaction"
              rows={2}
            />
          </div>
          <div>
            <Label className={labelClass}>Major Life Events</Label>
            <Textarea
              className={fieldClass}
              value={data.major_life_events || ''}
              onChange={(e) => updateField(sectionId, 'major_life_events', e.target.value)}
              disabled={isReadOnly}
              placeholder="Significant life events (positive or negative)"
              rows={3}
            />
          </div>
          <div>
            <Label className={labelClass}>Trauma History (Optional)</Label>
            <Textarea
              className={fieldClass}
              value={data.trauma_history || ''}
              onChange={(e) => updateField(sectionId, 'trauma_history', e.target.value)}
              disabled={isReadOnly}
              placeholder="Any history of trauma (only if client wishes to share)"
              rows={2}
            />
          </div>
        </>
      );

    case 'mental_status_examination':
      return (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label className={labelClass}>Appearance</Label>
              <Select
                value={data.appearance || ''}
                onValueChange={(value) => updateField(sectionId, 'appearance', value)}
                disabled={isReadOnly}
              >
                <SelectTrigger className={fieldClass}>
                  <SelectValue placeholder="Select" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="well_groomed">Well Groomed</SelectItem>
                  <SelectItem value="appropriate">Appropriate</SelectItem>
                  <SelectItem value="disheveled">Disheveled</SelectItem>
                  <SelectItem value="unkempt">Unkempt</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className={labelClass}>Behavior</Label>
              <Select
                value={data.behavior || ''}
                onValueChange={(value) => updateField(sectionId, 'behavior', value)}
                disabled={isReadOnly}
              >
                <SelectTrigger className={fieldClass}>
                  <SelectValue placeholder="Select" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="cooperative">Cooperative</SelectItem>
                  <SelectItem value="guarded">Guarded</SelectItem>
                  <SelectItem value="agitated">Agitated</SelectItem>
                  <SelectItem value="withdrawn">Withdrawn</SelectItem>
                  <SelectItem value="hostile">Hostile</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label className={labelClass}>Speech</Label>
              <Select
                value={data.speech || ''}
                onValueChange={(value) => updateField(sectionId, 'speech', value)}
                disabled={isReadOnly}
              >
                <SelectTrigger className={fieldClass}>
                  <SelectValue placeholder="Select" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="normal">Normal</SelectItem>
                  <SelectItem value="rapid">Rapid</SelectItem>
                  <SelectItem value="slow">Slow</SelectItem>
                  <SelectItem value="pressured">Pressured</SelectItem>
                  <SelectItem value="soft">Soft/Low volume</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className={labelClass}>Mood (Client's Report)</Label>
              <Input
                className={fieldClass}
                value={data.mood || ''}
                onChange={(e) => updateField(sectionId, 'mood', e.target.value)}
                disabled={isReadOnly}
                placeholder="e.g., Sad, Anxious, Happy"
              />
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label className={labelClass}>Affect (Observed)</Label>
              <Select
                value={data.affect || ''}
                onValueChange={(value) => updateField(sectionId, 'affect', value)}
                disabled={isReadOnly}
              >
                <SelectTrigger className={fieldClass}>
                  <SelectValue placeholder="Select" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="appropriate">Appropriate</SelectItem>
                  <SelectItem value="flat">Flat</SelectItem>
                  <SelectItem value="blunted">Blunted</SelectItem>
                  <SelectItem value="labile">Labile</SelectItem>
                  <SelectItem value="anxious">Anxious</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className={labelClass}>Thought Process</Label>
              <Select
                value={data.thought_process || ''}
                onValueChange={(value) => updateField(sectionId, 'thought_process', value)}
                disabled={isReadOnly}
              >
                <SelectTrigger className={fieldClass}>
                  <SelectValue placeholder="Select" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="logical">Logical & Goal-directed</SelectItem>
                  <SelectItem value="tangential">Tangential</SelectItem>
                  <SelectItem value="circumstantial">Circumstantial</SelectItem>
                  <SelectItem value="disorganized">Disorganized</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div>
            <Label className={labelClass}>Thought Content</Label>
            <Textarea
              className={fieldClass}
              value={data.thought_content || ''}
              onChange={(e) => updateField(sectionId, 'thought_content', e.target.value)}
              disabled={isReadOnly}
              placeholder="Suicidal/homicidal ideation, delusions, obsessions, phobias"
              rows={2}
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label className={labelClass}>Perception</Label>
              <Input
                className={fieldClass}
                value={data.perception || ''}
                onChange={(e) => updateField(sectionId, 'perception', e.target.value)}
                disabled={isReadOnly}
                placeholder="Hallucinations, illusions (if any)"
              />
            </div>
            <div>
              <Label className={labelClass}>Cognition</Label>
              <Select
                value={data.cognition || ''}
                onValueChange={(value) => updateField(sectionId, 'cognition', value)}
                disabled={isReadOnly}
              >
                <SelectTrigger className={fieldClass}>
                  <SelectValue placeholder="Select" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="intact">Intact</SelectItem>
                  <SelectItem value="impaired">Impaired</SelectItem>
                  <SelectItem value="not_assessed">Not Assessed</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label className={labelClass}>Insight</Label>
              <Select
                value={data.insight || ''}
                onValueChange={(value) => updateField(sectionId, 'insight', value)}
                disabled={isReadOnly}
              >
                <SelectTrigger className={fieldClass}>
                  <SelectValue placeholder="Select" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="good">Good</SelectItem>
                  <SelectItem value="partial">Partial</SelectItem>
                  <SelectItem value="poor">Poor</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className={labelClass}>Judgment</Label>
              <Select
                value={data.judgment || ''}
                onValueChange={(value) => updateField(sectionId, 'judgment', value)}
                disabled={isReadOnly}
              >
                <SelectTrigger className={fieldClass}>
                  <SelectValue placeholder="Select" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="good">Good</SelectItem>
                  <SelectItem value="fair">Fair</SelectItem>
                  <SelectItem value="poor">Poor</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </>
      );

    case 'provisional_formulation':
      return (
        <>
          <div>
            <Label className={labelClass}>Clinical Formulation *</Label>
            <Textarea
              className={fieldClass}
              value={data.clinical_formulation || ''}
              onChange={(e) => updateField(sectionId, 'clinical_formulation', e.target.value)}
              disabled={isReadOnly}
              placeholder="Your clinical understanding of the case - presenting issues, underlying factors, maintaining factors"
              rows={5}
            />
          </div>
          <div>
            <Label className={labelClass}>Precipitating Stressors</Label>
            <Textarea
              className={fieldClass}
              value={data.stressors || ''}
              onChange={(e) => updateField(sectionId, 'stressors', e.target.value)}
              disabled={isReadOnly}
              placeholder="What stressors contributed to current presentation?"
              rows={2}
            />
          </div>
          <div>
            <Label className={labelClass}>Client Strengths</Label>
            <Textarea
              className={fieldClass}
              value={data.strengths || ''}
              onChange={(e) => updateField(sectionId, 'strengths', e.target.value)}
              disabled={isReadOnly}
              placeholder="Protective factors, coping resources, support systems"
              rows={2}
            />
          </div>
          <div>
            <Label className={labelClass}>Risk Indicators</Label>
            <Textarea
              className={fieldClass}
              value={data.risk_indicators || ''}
              onChange={(e) => updateField(sectionId, 'risk_indicators', e.target.value)}
              disabled={isReadOnly}
              placeholder="Any risk factors to monitor (self-harm, substance abuse, etc.)"
              rows={2}
            />
          </div>
        </>
      );

    case 'initial_therapy_plan':
      return (
        <>
          <div>
            <Label className={labelClass}>Recommended Therapy Modality</Label>
            <Select
              value={data.therapy_modality || ''}
              onValueChange={(value) => updateField(sectionId, 'therapy_modality', value)}
              disabled={isReadOnly}
            >
              <SelectTrigger className={fieldClass}>
                <SelectValue placeholder="Select modality" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="cbt">Cognitive Behavioral Therapy (CBT)</SelectItem>
                <SelectItem value="dbt">Dialectical Behavior Therapy (DBT)</SelectItem>
                <SelectItem value="act">Acceptance & Commitment Therapy (ACT)</SelectItem>
                <SelectItem value="emdr">EMDR</SelectItem>
                <SelectItem value="psychodynamic">Psychodynamic Therapy</SelectItem>
                <SelectItem value="supportive">Supportive Counseling</SelectItem>
                <SelectItem value="integrative">Integrative/Eclectic</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className={labelClass}>Session Frequency</Label>
            <Select
              value={data.session_frequency || ''}
              onValueChange={(value) => updateField(sectionId, 'session_frequency', value)}
              disabled={isReadOnly}
            >
              <SelectTrigger className={fieldClass}>
                <SelectValue placeholder="Select frequency" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="weekly">Weekly</SelectItem>
                <SelectItem value="biweekly">Bi-weekly</SelectItem>
                <SelectItem value="monthly">Monthly</SelectItem>
                <SelectItem value="as_needed">As needed</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className={labelClass}>Initial Therapy Goals</Label>
            <Textarea
              className={fieldClass}
              value={data.initial_goals || ''}
              onChange={(e) => updateField(sectionId, 'initial_goals', e.target.value)}
              disabled={isReadOnly}
              placeholder="Short-term and long-term therapy goals"
              rows={4}
            />
          </div>
          <div>
            <Label className={labelClass}>Initial Homework/Recommendations</Label>
            <Textarea
              className={fieldClass}
              value={data.initial_homework || ''}
              onChange={(e) => updateField(sectionId, 'initial_homework', e.target.value)}
              disabled={isReadOnly}
              placeholder="Any initial assignments or recommendations"
              rows={2}
            />
          </div>
        </>
      );

    case 'consent_disclaimer':
      return (
        <>
          <div className="p-4 bg-muted/50 rounded-lg mb-4">
            <p className="text-sm text-muted-foreground">
              Please confirm that informed consent has been taken and confidentiality has been explained to the client.
            </p>
          </div>
          <div className="flex items-start gap-3 p-4 border rounded-lg">
            <Checkbox
              id="informed_consent"
              checked={data.informed_consent_taken || false}
              onCheckedChange={(checked) => updateField(sectionId, 'informed_consent_taken', checked)}
              disabled={isReadOnly}
            />
            <div>
              <Label htmlFor="informed_consent" className="font-medium cursor-pointer">
                Informed Consent Taken *
              </Label>
              <p className="text-sm text-muted-foreground">
                Client has been informed about the therapy process, fees, cancellation policy, and has agreed to proceed.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-4 border rounded-lg">
            <Checkbox
              id="confidentiality"
              checked={data.confidentiality_explained || false}
              onCheckedChange={(checked) => updateField(sectionId, 'confidentiality_explained', checked)}
              disabled={isReadOnly}
            />
            <div>
              <Label htmlFor="confidentiality" className="font-medium cursor-pointer">
                Confidentiality Explained
              </Label>
              <p className="text-sm text-muted-foreground">
                Client understands the limits of confidentiality and when information may need to be disclosed.
              </p>
            </div>
          </div>
          <div>
            <Label className={labelClass}>Consent Date</Label>
            <Input
              type="date"
              className={fieldClass}
              value={data.consent_date || ''}
              onChange={(e) => updateField(sectionId, 'consent_date', e.target.value)}
              disabled={isReadOnly}
            />
          </div>
          <div>
            <Label className={labelClass}>Additional Notes</Label>
            <Textarea
              className={fieldClass}
              value={data.notes || ''}
              onChange={(e) => updateField(sectionId, 'notes', e.target.value)}
              disabled={isReadOnly}
              placeholder="Any additional notes regarding consent"
              rows={2}
            />
          </div>
        </>
      );

    default:
      return <p className="text-muted-foreground">Section not found</p>;
  }
};

export default CaseHistoryForm;
