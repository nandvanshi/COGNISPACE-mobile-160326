import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Checkbox } from './ui/checkbox';
import { toast } from 'sonner';
import { 
  ChevronLeft, 
  ChevronRight, 
  Save, 
  Check, 
  AlertCircle,
  User,
  MessageSquare,
  History,
  Brain,
  Stethoscope,
  Users,
  BookOpen,
  ClipboardCheck,
  Target,
  FileCheck,
  ChevronDown,
  ChevronUp,
  Loader2
} from 'lucide-react';
import debounce from 'lodash/debounce';

const STEPS = [
  { id: 'basic_identification', label: 'Basic Identification', icon: User, required: true },
  { id: 'presenting_complaints', label: 'Presenting Complaints', icon: MessageSquare, required: true },
  { id: 'history_of_present_illness', label: 'History of Present Illness', icon: History, required: false },
  { id: 'past_psychiatric_history', label: 'Past Psychiatric History', icon: Brain, required: false },
  { id: 'medical_history', label: 'Medical History', icon: Stethoscope, required: false },
  { id: 'family_history', label: 'Family History', icon: Users, required: false },
  { id: 'personal_developmental_history', label: 'Personal & Developmental', icon: BookOpen, required: false },
  { id: 'mental_status_examination', label: 'Mental Status Examination', icon: ClipboardCheck, required: false },
  { id: 'provisional_formulation', label: 'Provisional Formulation', icon: Target, required: false },
  { id: 'initial_therapy_plan', label: 'Initial Therapy Plan', icon: Target, required: false },
  { id: 'consent_disclaimer', label: 'Consent & Disclaimer', icon: FileCheck, required: true },
];

const CaseHistoryWizard = ({ clientId, clientName, onComplete, onClose, isReadOnly = false }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState({
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
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [expandedSections, setExpandedSections] = useState({});
  const [caseHistoryExists, setCaseHistoryExists] = useState(false);

  // Fetch existing case history
  useEffect(() => {
    const fetchCaseHistory = async () => {
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
          setCaseHistoryExists(true);
        }
      } catch (error) {
        if (error.response?.status !== 404) {
          console.error('Error fetching case history:', error);
        }
        // Pre-fill name from client
        setFormData(prev => ({
          ...prev,
          basic_identification: { ...prev.basic_identification, name: clientName || '' }
        }));
      } finally {
        setLoading(false);
      }
    };

    if (clientId) {
      fetchCaseHistory();
    }
  }, [clientId, clientName]);

  // Auto-save with debounce
  const autoSave = useCallback(
    debounce(async (section, data) => {
      if (isReadOnly) return;
      
      try {
        await axios.patch(`${API}/case-history/${clientId}/section?section=${section}`, data);
        // Silent save - no toast for auto-save
      } catch (error) {
        console.error('Auto-save failed:', error);
      }
    }, 2000),
    [clientId, isReadOnly]
  );

  const updateField = (section, field, value) => {
    setFormData(prev => {
      const newData = {
        ...prev,
        [section]: {
          ...prev[section],
          [field]: value
        }
      };
      
      // Trigger auto-save
      autoSave(section, newData[section]);
      
      return newData;
    });
  };

  const handleSaveSection = async () => {
    if (isReadOnly) return;
    
    setSaving(true);
    const section = STEPS[currentStep].id;
    
    try {
      await axios.patch(`${API}/case-history/${clientId}/section?section=${section}`, formData[section]);
      toast.success('Section saved');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save section');
    } finally {
      setSaving(false);
    }
  };

  const handleComplete = async () => {
    if (isReadOnly) return;
    
    // Validate required fields
    if (!formData.basic_identification?.name) {
      toast.error('Please enter client name in Basic Identification');
      setCurrentStep(0);
      return;
    }
    
    if (!formData.presenting_complaints?.main_problems) {
      toast.error('Please enter main problems in Presenting Complaints');
      setCurrentStep(1);
      return;
    }
    
    if (!formData.consent_disclaimer?.informed_consent_taken) {
      toast.error('Informed consent must be taken');
      setCurrentStep(10);
      return;
    }
    
    setSaving(true);
    
    try {
      // First save all data
      const savePayload = {
        client_id: clientId,
        ...formData,
        is_complete: true
      };
      
      if (caseHistoryExists) {
        await axios.put(`${API}/case-history/${clientId}`, savePayload);
      } else {
        await axios.post(`${API}/case-history`, savePayload);
      }
      
      // Then mark as complete
      await axios.patch(`${API}/case-history/${clientId}/complete`);
      
      toast.success('Case history completed successfully!');
      setIsComplete(true);
      
      if (onComplete) {
        onComplete();
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to complete case history');
    } finally {
      setSaving(false);
    }
  };

  const toggleSection = (sectionId) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionId]: !prev[sectionId]
    }));
  };

  const renderBasicIdentification = () => (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label>Full Name *</Label>
          <Input
            value={formData.basic_identification?.name || ''}
            onChange={(e) => updateField('basic_identification', 'name', e.target.value)}
            placeholder="Client's full name"
            disabled={isReadOnly}
            data-testid="case-history-name"
          />
        </div>
        <div>
          <Label>Age</Label>
          <Input
            type="number"
            value={formData.basic_identification?.age || ''}
            onChange={(e) => updateField('basic_identification', 'age', parseInt(e.target.value) || '')}
            placeholder="Age"
            disabled={isReadOnly}
          />
        </div>
        <div>
          <Label>Date of Birth</Label>
          <Input
            type="date"
            value={formData.basic_identification?.dob || ''}
            onChange={(e) => updateField('basic_identification', 'dob', e.target.value)}
            disabled={isReadOnly}
          />
        </div>
        <div>
          <Label>Gender</Label>
          <Select
            value={formData.basic_identification?.gender || undefined}
            onValueChange={(v) => updateField('basic_identification', 'gender', v)}
            disabled={isReadOnly}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select gender" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Male">Male</SelectItem>
              <SelectItem value="Female">Female</SelectItem>
              <SelectItem value="Other">Other</SelectItem>
              <SelectItem value="Prefer not to say">Prefer not to say</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Marital Status</Label>
          <Select
            value={formData.basic_identification?.marital_status || undefined}
            onValueChange={(v) => updateField('basic_identification', 'marital_status', v)}
            disabled={isReadOnly}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Single">Single</SelectItem>
              <SelectItem value="Married">Married</SelectItem>
              <SelectItem value="Divorced">Divorced</SelectItem>
              <SelectItem value="Widowed">Widowed</SelectItem>
              <SelectItem value="Separated">Separated</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Education</Label>
          <Input
            value={formData.basic_identification?.education || ''}
            onChange={(e) => updateField('basic_identification', 'education', e.target.value)}
            placeholder="Highest education"
            disabled={isReadOnly}
          />
        </div>
        <div>
          <Label>Occupation</Label>
          <Input
            value={formData.basic_identification?.occupation || ''}
            onChange={(e) => updateField('basic_identification', 'occupation', e.target.value)}
            placeholder="Current occupation"
            disabled={isReadOnly}
          />
        </div>
        <div>
          <Label>City</Label>
          <Input
            value={formData.basic_identification?.city || ''}
            onChange={(e) => updateField('basic_identification', 'city', e.target.value)}
            placeholder="City"
            disabled={isReadOnly}
          />
        </div>
        <div className="md:col-span-2">
          <Label>Address</Label>
          <Textarea
            value={formData.basic_identification?.address || ''}
            onChange={(e) => updateField('basic_identification', 'address', e.target.value)}
            placeholder="Full address"
            rows={2}
            disabled={isReadOnly}
          />
        </div>
        <div>
          <Label>Contact Number</Label>
          <Input
            value={formData.basic_identification?.contact || ''}
            onChange={(e) => updateField('basic_identification', 'contact', e.target.value)}
            placeholder="Phone number"
            disabled={isReadOnly}
          />
        </div>
        <div>
          <Label>Emergency Contact</Label>
          <Input
            value={formData.basic_identification?.emergency_contact || ''}
            onChange={(e) => updateField('basic_identification', 'emergency_contact', e.target.value)}
            placeholder="Emergency contact number"
            disabled={isReadOnly}
          />
        </div>
        <div>
          <Label>Emergency Contact Relation</Label>
          <Input
            value={formData.basic_identification?.emergency_contact_relation || ''}
            onChange={(e) => updateField('basic_identification', 'emergency_contact_relation', e.target.value)}
            placeholder="Relationship to client"
            disabled={isReadOnly}
          />
        </div>
        <div>
          <Label>Referred By</Label>
          <Input
            value={formData.basic_identification?.referred_by || ''}
            onChange={(e) => updateField('basic_identification', 'referred_by', e.target.value)}
            placeholder="Referral source"
            disabled={isReadOnly}
          />
        </div>
      </div>
    </div>
  );

  const renderPresentingComplaints = () => (
    <div className="space-y-4">
      <div>
        <Label>Main Problems (in client's own words) *</Label>
        <Textarea
          value={formData.presenting_complaints?.main_problems || ''}
          onChange={(e) => updateField('presenting_complaints', 'main_problems', e.target.value)}
          placeholder="Describe the client's main problems in their own words..."
          rows={4}
          disabled={isReadOnly}
          data-testid="case-history-main-problems"
        />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label>Duration</Label>
          <Input
            value={formData.presenting_complaints?.duration || ''}
            onChange={(e) => updateField('presenting_complaints', 'duration', e.target.value)}
            placeholder="How long has this been going on?"
            disabled={isReadOnly}
          />
        </div>
        <div>
          <Label>Severity</Label>
          <Select
            value={formData.presenting_complaints?.severity || undefined}
            onValueChange={(v) => updateField('presenting_complaints', 'severity', v)}
            disabled={isReadOnly}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select severity" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Mild">Mild</SelectItem>
              <SelectItem value="Moderate">Moderate</SelectItem>
              <SelectItem value="Severe">Severe</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Frequency</Label>
          <Select
            value={formData.presenting_complaints?.frequency || undefined}
            onValueChange={(v) => updateField('presenting_complaints', 'frequency', v)}
            disabled={isReadOnly}
          >
            <SelectTrigger>
              <SelectValue placeholder="How often?" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Constantly">Constantly</SelectItem>
              <SelectItem value="Daily">Daily</SelectItem>
              <SelectItem value="Several times a week">Several times a week</SelectItem>
              <SelectItem value="Weekly">Weekly</SelectItem>
              <SelectItem value="Occasionally">Occasionally</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <div>
        <Label>Triggers</Label>
        <Textarea
          value={formData.presenting_complaints?.triggers || ''}
          onChange={(e) => updateField('presenting_complaints', 'triggers', e.target.value)}
          placeholder="What triggers or worsens the problem?"
          rows={3}
          disabled={isReadOnly}
        />
      </div>
    </div>
  );

  const renderHistoryOfPresentIllness = () => (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label>Onset</Label>
          <Textarea
            value={formData.history_of_present_illness?.onset || ''}
            onChange={(e) => updateField('history_of_present_illness', 'onset', e.target.value)}
            placeholder="When did the symptoms first appear?"
            rows={2}
            disabled={isReadOnly}
          />
        </div>
        <div>
          <Label>Course</Label>
          <Textarea
            value={formData.history_of_present_illness?.course || ''}
            onChange={(e) => updateField('history_of_present_illness', 'course', e.target.value)}
            placeholder="How has it progressed over time?"
            rows={2}
            disabled={isReadOnly}
          />
        </div>
      </div>
      <div>
        <Label>Previous Episodes</Label>
        <Textarea
          value={formData.history_of_present_illness?.previous_episodes || ''}
          onChange={(e) => updateField('history_of_present_illness', 'previous_episodes', e.target.value)}
          placeholder="Any previous similar episodes?"
          rows={2}
          disabled={isReadOnly}
        />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label>Factors Improving Symptoms</Label>
          <Textarea
            value={formData.history_of_present_illness?.factors_improving || ''}
            onChange={(e) => updateField('history_of_present_illness', 'factors_improving', e.target.value)}
            placeholder="What makes it better?"
            rows={2}
            disabled={isReadOnly}
          />
        </div>
        <div>
          <Label>Factors Worsening Symptoms</Label>
          <Textarea
            value={formData.history_of_present_illness?.factors_worsening || ''}
            onChange={(e) => updateField('history_of_present_illness', 'factors_worsening', e.target.value)}
            placeholder="What makes it worse?"
            rows={2}
            disabled={isReadOnly}
          />
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label>Prior Therapy</Label>
          <Textarea
            value={formData.history_of_present_illness?.prior_therapy || ''}
            onChange={(e) => updateField('history_of_present_illness', 'prior_therapy', e.target.value)}
            placeholder="Previous therapy or counseling received"
            rows={2}
            disabled={isReadOnly}
          />
        </div>
        <div>
          <Label>Prior Medication</Label>
          <Textarea
            value={formData.history_of_present_illness?.prior_medication || ''}
            onChange={(e) => updateField('history_of_present_illness', 'prior_medication', e.target.value)}
            placeholder="Previous psychiatric medications"
            rows={2}
            disabled={isReadOnly}
          />
        </div>
      </div>
    </div>
  );

  const renderPastPsychiatricHistory = () => (
    <div className="space-y-4">
      <div>
        <Label>Previous Therapy</Label>
        <Textarea
          value={formData.past_psychiatric_history?.previous_therapy || ''}
          onChange={(e) => updateField('past_psychiatric_history', 'previous_therapy', e.target.value)}
          placeholder="Details of any previous therapy or counseling"
          rows={3}
          disabled={isReadOnly}
        />
      </div>
      <div>
        <Label>Previous Diagnosis</Label>
        <Textarea
          value={formData.past_psychiatric_history?.previous_diagnosis || ''}
          onChange={(e) => updateField('past_psychiatric_history', 'previous_diagnosis', e.target.value)}
          placeholder="Any previous psychiatric diagnoses"
          rows={2}
          disabled={isReadOnly}
        />
      </div>
      <div>
        <Label>Hospitalizations</Label>
        <Textarea
          value={formData.past_psychiatric_history?.hospitalizations || ''}
          onChange={(e) => updateField('past_psychiatric_history', 'hospitalizations', e.target.value)}
          placeholder="Any psychiatric hospitalizations"
          rows={2}
          disabled={isReadOnly}
        />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label>Past Medications</Label>
          <Textarea
            value={formData.past_psychiatric_history?.past_medications || ''}
            onChange={(e) => updateField('past_psychiatric_history', 'past_medications', e.target.value)}
            placeholder="Previous psychiatric medications"
            rows={2}
            disabled={isReadOnly}
          />
        </div>
        <div>
          <Label>Current Medications</Label>
          <Textarea
            value={formData.past_psychiatric_history?.current_medications || ''}
            onChange={(e) => updateField('past_psychiatric_history', 'current_medications', e.target.value)}
            placeholder="Current psychiatric medications"
            rows={2}
            disabled={isReadOnly}
          />
        </div>
      </div>
    </div>
  );

  const renderMedicalHistory = () => (
    <div className="space-y-4">
      <div>
        <Label>Chronic Illnesses</Label>
        <Textarea
          value={formData.medical_history?.chronic_illnesses || ''}
          onChange={(e) => updateField('medical_history', 'chronic_illnesses', e.target.value)}
          placeholder="Any chronic medical conditions"
          rows={2}
          disabled={isReadOnly}
        />
      </div>
      <div>
        <Label>Current Medications</Label>
        <Textarea
          value={formData.medical_history?.current_medications || ''}
          onChange={(e) => updateField('medical_history', 'current_medications', e.target.value)}
          placeholder="Current non-psychiatric medications"
          rows={2}
          disabled={isReadOnly}
        />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <Label>Sleep Pattern</Label>
          <Select
            value={formData.medical_history?.sleep_pattern || undefined}
            onValueChange={(v) => updateField('medical_history', 'sleep_pattern', v)}
            disabled={isReadOnly}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Good">Good</SelectItem>
              <SelectItem value="Poor">Poor</SelectItem>
              <SelectItem value="Insomnia">Insomnia</SelectItem>
              <SelectItem value="Hypersomnia">Hypersomnia</SelectItem>
              <SelectItem value="Irregular">Irregular</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Appetite</Label>
          <Select
            value={formData.medical_history?.appetite || undefined}
            onValueChange={(v) => updateField('medical_history', 'appetite', v)}
            disabled={isReadOnly}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Normal">Normal</SelectItem>
              <SelectItem value="Increased">Increased</SelectItem>
              <SelectItem value="Decreased">Decreased</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Substance Use</Label>
          <Select
            value={formData.medical_history?.substance_use || undefined}
            onValueChange={(v) => updateField('medical_history', 'substance_use', v)}
            disabled={isReadOnly}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="None">None</SelectItem>
              <SelectItem value="Alcohol">Alcohol</SelectItem>
              <SelectItem value="Tobacco">Tobacco</SelectItem>
              <SelectItem value="Cannabis">Cannabis</SelectItem>
              <SelectItem value="Multiple">Multiple substances</SelectItem>
              <SelectItem value="Other">Other</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  );

  const renderFamilyHistory = () => (
    <div className="space-y-4">
      <div>
        <Label>Family Structure</Label>
        <Textarea
          value={formData.family_history?.family_structure || ''}
          onChange={(e) => updateField('family_history', 'family_structure', e.target.value)}
          placeholder="Describe family structure (parents, siblings, etc.)"
          rows={3}
          disabled={isReadOnly}
        />
      </div>
      <div>
        <Label>Mental Illness in Family</Label>
        <Select
          value={formData.family_history?.mental_illness_in_family?.startsWith('Yes') ? 'yes' : 
                 formData.family_history?.mental_illness_in_family === 'No' ? 'no' : undefined}
          onValueChange={(v) => updateField('family_history', 'mental_illness_in_family', v === 'yes' ? 'Yes - ' : 'No')}
          disabled={isReadOnly}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="no">No</SelectItem>
            <SelectItem value="yes">Yes</SelectItem>
          </SelectContent>
        </Select>
        {formData.family_history?.mental_illness_in_family?.startsWith('Yes') && (
          <Textarea
            className="mt-2"
            value={formData.family_history?.mental_illness_in_family?.replace('Yes - ', '') || ''}
            onChange={(e) => updateField('family_history', 'mental_illness_in_family', `Yes - ${e.target.value}`)}
            placeholder="Please provide details..."
            rows={2}
            disabled={isReadOnly}
          />
        )}
      </div>
      <div>
        <Label>Relationship Dynamics</Label>
        <Textarea
          value={formData.family_history?.relationship_dynamics || ''}
          onChange={(e) => updateField('family_history', 'relationship_dynamics', e.target.value)}
          placeholder="Quality of family relationships"
          rows={3}
          disabled={isReadOnly}
        />
      </div>
    </div>
  );

  const renderPersonalDevelopmentalHistory = () => (
    <div className="space-y-4">
      <div>
        <Label>Childhood</Label>
        <Textarea
          value={formData.personal_developmental_history?.childhood || ''}
          onChange={(e) => updateField('personal_developmental_history', 'childhood', e.target.value)}
          placeholder="Relevant childhood history"
          rows={3}
          disabled={isReadOnly}
        />
      </div>
      <div>
        <Label>Education History</Label>
        <Textarea
          value={formData.personal_developmental_history?.education_history || ''}
          onChange={(e) => updateField('personal_developmental_history', 'education_history', e.target.value)}
          placeholder="Educational background and experiences"
          rows={2}
          disabled={isReadOnly}
        />
      </div>
      <div>
        <Label>Work History</Label>
        <Textarea
          value={formData.personal_developmental_history?.work_history || ''}
          onChange={(e) => updateField('personal_developmental_history', 'work_history', e.target.value)}
          placeholder="Employment history"
          rows={2}
          disabled={isReadOnly}
        />
      </div>
      <div>
        <Label>Major Life Events (Optional - Sensitive)</Label>
        <Textarea
          value={formData.personal_developmental_history?.major_life_events || ''}
          onChange={(e) => updateField('personal_developmental_history', 'major_life_events', e.target.value)}
          placeholder="Significant life events (handle sensitively)"
          rows={2}
          disabled={isReadOnly}
        />
      </div>
      <div>
        <Label>Trauma History (Optional - Sensitive)</Label>
        <Textarea
          value={formData.personal_developmental_history?.trauma_history || ''}
          onChange={(e) => updateField('personal_developmental_history', 'trauma_history', e.target.value)}
          placeholder="History of trauma (handle sensitively)"
          rows={2}
          disabled={isReadOnly}
        />
      </div>
    </div>
  );

  const renderMentalStatusExamination = () => (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground mb-4">
        Mental Status Examination (MSE) - Clinical observations during assessment
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label>Appearance</Label>
          <Select
            value={formData.mental_status_examination?.appearance || undefined}
            onValueChange={(v) => updateField('mental_status_examination', 'appearance', v)}
            disabled={isReadOnly}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Well-groomed">Well-groomed</SelectItem>
              <SelectItem value="Casually dressed">Casually dressed</SelectItem>
              <SelectItem value="Disheveled">Disheveled</SelectItem>
              <SelectItem value="Inappropriate attire">Inappropriate attire</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Behavior</Label>
          <Select
            value={formData.mental_status_examination?.behavior || undefined}
            onValueChange={(v) => updateField('mental_status_examination', 'behavior', v)}
            disabled={isReadOnly}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Cooperative">Cooperative</SelectItem>
              <SelectItem value="Guarded">Guarded</SelectItem>
              <SelectItem value="Agitated">Agitated</SelectItem>
              <SelectItem value="Withdrawn">Withdrawn</SelectItem>
              <SelectItem value="Hostile">Hostile</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Speech</Label>
          <Select
            value={formData.mental_status_examination?.speech || undefined}
            onValueChange={(v) => updateField('mental_status_examination', 'speech', v)}
            disabled={isReadOnly}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Normal">Normal</SelectItem>
              <SelectItem value="Pressured">Pressured</SelectItem>
              <SelectItem value="Slow">Slow</SelectItem>
              <SelectItem value="Soft">Soft</SelectItem>
              <SelectItem value="Loud">Loud</SelectItem>
              <SelectItem value="Monotone">Monotone</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Mood (Client's description)</Label>
          <Select
            value={formData.mental_status_examination?.mood || undefined}
            onValueChange={(v) => updateField('mental_status_examination', 'mood', v)}
            disabled={isReadOnly}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Euthymic">Euthymic (Normal)</SelectItem>
              <SelectItem value="Depressed">Depressed</SelectItem>
              <SelectItem value="Anxious">Anxious</SelectItem>
              <SelectItem value="Irritable">Irritable</SelectItem>
              <SelectItem value="Euphoric">Euphoric</SelectItem>
              <SelectItem value="Angry">Angry</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Affect (Observed)</Label>
          <Select
            value={formData.mental_status_examination?.affect || undefined}
            onValueChange={(v) => updateField('mental_status_examination', 'affect', v)}
            disabled={isReadOnly}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Appropriate">Appropriate</SelectItem>
              <SelectItem value="Flat">Flat</SelectItem>
              <SelectItem value="Blunted">Blunted</SelectItem>
              <SelectItem value="Labile">Labile</SelectItem>
              <SelectItem value="Incongruent">Incongruent</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Thought Process</Label>
          <Select
            value={formData.mental_status_examination?.thought_process || undefined}
            onValueChange={(v) => updateField('mental_status_examination', 'thought_process', v)}
            disabled={isReadOnly}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Logical">Logical / Goal-directed</SelectItem>
              <SelectItem value="Tangential">Tangential</SelectItem>
              <SelectItem value="Circumstantial">Circumstantial</SelectItem>
              <SelectItem value="Disorganized">Disorganized</SelectItem>
              <SelectItem value="Flight of ideas">Flight of ideas</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Thought Content</Label>
          <Select
            value={formData.mental_status_examination?.thought_content || undefined}
            onValueChange={(v) => updateField('mental_status_examination', 'thought_content', v)}
            disabled={isReadOnly}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Normal">Normal</SelectItem>
              <SelectItem value="Obsessions">Obsessions</SelectItem>
              <SelectItem value="Phobias">Phobias</SelectItem>
              <SelectItem value="Delusions">Delusions</SelectItem>
              <SelectItem value="Suicidal ideation">Suicidal ideation</SelectItem>
              <SelectItem value="Homicidal ideation">Homicidal ideation</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Perception</Label>
          <Select
            value={formData.mental_status_examination?.perception || undefined}
            onValueChange={(v) => updateField('mental_status_examination', 'perception', v)}
            disabled={isReadOnly}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Normal">Normal</SelectItem>
              <SelectItem value="Auditory hallucinations">Auditory hallucinations</SelectItem>
              <SelectItem value="Visual hallucinations">Visual hallucinations</SelectItem>
              <SelectItem value="Illusions">Illusions</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Cognition</Label>
          <Select
            value={formData.mental_status_examination?.cognition || undefined}
            onValueChange={(v) => updateField('mental_status_examination', 'cognition', v)}
            disabled={isReadOnly}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Intact">Intact</SelectItem>
              <SelectItem value="Impaired - Memory">Impaired - Memory</SelectItem>
              <SelectItem value="Impaired - Attention">Impaired - Attention</SelectItem>
              <SelectItem value="Impaired - Orientation">Impaired - Orientation</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Insight</Label>
          <Select
            value={formData.mental_status_examination?.insight || undefined}
            onValueChange={(v) => updateField('mental_status_examination', 'insight', v)}
            disabled={isReadOnly}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Good">Good</SelectItem>
              <SelectItem value="Partial">Partial</SelectItem>
              <SelectItem value="Poor">Poor</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Judgment</Label>
          <Select
            value={formData.mental_status_examination?.judgment || undefined}
            onValueChange={(v) => updateField('mental_status_examination', 'judgment', v)}
            disabled={isReadOnly}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Good">Good</SelectItem>
              <SelectItem value="Fair">Fair</SelectItem>
              <SelectItem value="Poor">Poor</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  );

  const renderProvisionalFormulation = () => (
    <div className="space-y-4">
      <div>
        <Label>Clinical Formulation *</Label>
        <Textarea
          value={formData.provisional_formulation?.clinical_formulation || ''}
          onChange={(e) => updateField('provisional_formulation', 'clinical_formulation', e.target.value)}
          placeholder="Working clinical formulation (not auto-diagnosis). Summarize your understanding of the client's presentation."
          rows={4}
          disabled={isReadOnly}
        />
      </div>
      <div>
        <Label>Current Stressors</Label>
        <Textarea
          value={formData.provisional_formulation?.stressors || ''}
          onChange={(e) => updateField('provisional_formulation', 'stressors', e.target.value)}
          placeholder="Identify current stressors contributing to the presentation"
          rows={2}
          disabled={isReadOnly}
        />
      </div>
      <div>
        <Label>Strengths</Label>
        <Textarea
          value={formData.provisional_formulation?.strengths || ''}
          onChange={(e) => updateField('provisional_formulation', 'strengths', e.target.value)}
          placeholder="Client's strengths and protective factors"
          rows={2}
          disabled={isReadOnly}
        />
      </div>
      <div>
        <Label>Risk Indicators</Label>
        <Textarea
          value={formData.provisional_formulation?.risk_indicators || ''}
          onChange={(e) => updateField('provisional_formulation', 'risk_indicators', e.target.value)}
          placeholder="Any risk factors (self-harm, harm to others, etc.)"
          rows={2}
          disabled={isReadOnly}
        />
      </div>
    </div>
  );

  const renderInitialTherapyPlan = () => (
    <div className="space-y-4">
      <div>
        <Label>Therapy Modality</Label>
        <Select
          value={formData.initial_therapy_plan?.therapy_modality || undefined}
          onValueChange={(v) => updateField('initial_therapy_plan', 'therapy_modality', v)}
          disabled={isReadOnly}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select modality" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="CBT">CBT (Cognitive Behavioral Therapy)</SelectItem>
            <SelectItem value="DBT">DBT (Dialectical Behavior Therapy)</SelectItem>
            <SelectItem value="ACT">ACT (Acceptance & Commitment Therapy)</SelectItem>
            <SelectItem value="EMDR">EMDR</SelectItem>
            <SelectItem value="Psychodynamic">Psychodynamic</SelectItem>
            <SelectItem value="Person-Centered">Person-Centered</SelectItem>
            <SelectItem value="Integrative">Integrative</SelectItem>
            <SelectItem value="Mindfulness-Based">Mindfulness-Based</SelectItem>
            <SelectItem value="Other">Other</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div>
        <Label>Session Frequency</Label>
        <Select
          value={formData.initial_therapy_plan?.session_frequency || undefined}
          onValueChange={(v) => updateField('initial_therapy_plan', 'session_frequency', v)}
          disabled={isReadOnly}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select frequency" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="Weekly">Weekly</SelectItem>
            <SelectItem value="Bi-weekly">Bi-weekly</SelectItem>
            <SelectItem value="Monthly">Monthly</SelectItem>
            <SelectItem value="As needed">As needed</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div>
        <Label>Initial Goals</Label>
        <Textarea
          value={formData.initial_therapy_plan?.initial_goals || ''}
          onChange={(e) => updateField('initial_therapy_plan', 'initial_goals', e.target.value)}
          placeholder="Initial therapy goals"
          rows={3}
          disabled={isReadOnly}
        />
      </div>
      <div>
        <Label>Homework (if any)</Label>
        <Textarea
          value={formData.initial_therapy_plan?.homework || ''}
          onChange={(e) => updateField('initial_therapy_plan', 'homework', e.target.value)}
          placeholder="Initial homework assignment"
          rows={2}
          disabled={isReadOnly}
        />
      </div>
    </div>
  );

  const renderConsentDisclaimer = () => (
    <div className="space-y-4">
      <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
        <p className="text-sm text-amber-800">
          <AlertCircle className="inline mr-2" size={16} />
          Please ensure informed consent is obtained before proceeding with therapy.
        </p>
      </div>
      
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Checkbox
            id="informed_consent"
            checked={formData.consent_disclaimer?.informed_consent_taken || false}
            onCheckedChange={(checked) => updateField('consent_disclaimer', 'informed_consent_taken', checked)}
            disabled={isReadOnly}
            data-testid="case-history-consent"
          />
          <Label htmlFor="informed_consent" className="text-sm font-normal">
            Informed consent has been obtained from the client *
          </Label>
        </div>
        
        <div className="flex items-center space-x-2">
          <Checkbox
            id="confidentiality"
            checked={formData.consent_disclaimer?.confidentiality_explained || false}
            onCheckedChange={(checked) => updateField('consent_disclaimer', 'confidentiality_explained', checked)}
            disabled={isReadOnly}
          />
          <Label htmlFor="confidentiality" className="text-sm font-normal">
            Confidentiality and its limits have been explained
          </Label>
        </div>
      </div>
      
      <div>
        <Label>Consent Date</Label>
        <Input
          type="date"
          value={formData.consent_disclaimer?.consent_date || ''}
          onChange={(e) => updateField('consent_disclaimer', 'consent_date', e.target.value)}
          disabled={isReadOnly}
        />
      </div>
      
      <div>
        <Label>Additional Notes</Label>
        <Textarea
          value={formData.consent_disclaimer?.additional_notes || ''}
          onChange={(e) => updateField('consent_disclaimer', 'additional_notes', e.target.value)}
          placeholder="Any additional notes regarding consent or disclaimers"
          rows={2}
          disabled={isReadOnly}
        />
      </div>
    </div>
  );

  const renderCurrentSection = () => {
    switch (STEPS[currentStep].id) {
      case 'basic_identification': return renderBasicIdentification();
      case 'presenting_complaints': return renderPresentingComplaints();
      case 'history_of_present_illness': return renderHistoryOfPresentIllness();
      case 'past_psychiatric_history': return renderPastPsychiatricHistory();
      case 'medical_history': return renderMedicalHistory();
      case 'family_history': return renderFamilyHistory();
      case 'personal_developmental_history': return renderPersonalDevelopmentalHistory();
      case 'mental_status_examination': return renderMentalStatusExamination();
      case 'provisional_formulation': return renderProvisionalFormulation();
      case 'initial_therapy_plan': return renderInitialTherapyPlan();
      case 'consent_disclaimer': return renderConsentDisclaimer();
      default: return null;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="animate-spin text-primary" size={32} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Case History</h2>
          <p className="text-muted-foreground">Client: {clientName}</p>
        </div>
        {isComplete && (
          <span className="flex items-center gap-2 text-green-600 bg-green-50 px-3 py-1 rounded-full text-sm">
            <Check size={16} /> Complete
          </span>
        )}
      </div>

      {/* Progress Steps */}
      <div className="flex items-center gap-1 overflow-x-auto pb-2">
        {STEPS.map((step, index) => {
          const Icon = step.icon;
          const isCurrent = index === currentStep;
          const isCompleted = index < currentStep;
          
          return (
            <button
              key={step.id}
              onClick={() => setCurrentStep(index)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm whitespace-nowrap transition-all ${
                isCurrent 
                  ? 'bg-primary text-primary-foreground' 
                  : isCompleted 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
              }`}
            >
              <Icon size={14} />
              <span className="hidden md:inline">{step.label}</span>
              <span className="md:hidden">{index + 1}</span>
              {step.required && <span className="text-red-500">*</span>}
            </button>
          );
        })}
      </div>

      {/* Current Section */}
      <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40">
        <div className="flex items-center gap-3 mb-6">
          {React.createElement(STEPS[currentStep].icon, { size: 24, className: 'text-primary' })}
          <div>
            <h3 className="text-lg font-semibold">{STEPS[currentStep].label}</h3>
            {STEPS[currentStep].required && (
              <span className="text-xs text-red-500">* Required section</span>
            )}
          </div>
        </div>

        {renderCurrentSection()}

        {/* Navigation */}
        <div className="flex items-center justify-between mt-6 pt-4 border-t">
          <Button
            variant="outline"
            onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
            disabled={currentStep === 0}
          >
            <ChevronLeft size={16} className="mr-2" /> Previous
          </Button>

          <div className="flex items-center gap-2">
            {!isReadOnly && (
              <Button variant="outline" onClick={handleSaveSection} disabled={saving}>
                {saving ? <Loader2 className="animate-spin mr-2" size={16} /> : <Save size={16} className="mr-2" />}
                Save Section
              </Button>
            )}

            {currentStep < STEPS.length - 1 ? (
              <Button onClick={() => setCurrentStep(currentStep + 1)}>
                Next <ChevronRight size={16} className="ml-2" />
              </Button>
            ) : (
              !isReadOnly && !isComplete && (
                <Button 
                  onClick={handleComplete} 
                  disabled={saving}
                  className="bg-green-600 hover:bg-green-700"
                  data-testid="complete-case-history-btn"
                >
                  {saving ? <Loader2 className="animate-spin mr-2" size={16} /> : <Check size={16} className="mr-2" />}
                  Complete Case History
                </Button>
              )
            )}
          </div>
        </div>
      </Card>
    </div>
  );
};

export default CaseHistoryWizard;
