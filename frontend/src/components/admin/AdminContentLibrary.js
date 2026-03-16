import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { API } from '../../App';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../ui/dialog';
import { toast } from 'sonner';
import { Plus, Trash2, Edit2, BookOpen, FileText, ClipboardList, Lightbulb, ScrollText, Search, Sparkles, Loader2 } from 'lucide-react';

const CONTENT_TYPES = [
  { id: 'homework_template', label: 'Homework Templates', icon: BookOpen, color: 'bg-blue-500' },
  { id: 'protocol_template', label: 'Protocol Templates', icon: ClipboardList, color: 'bg-purple-500' },
  { id: 'resource', label: 'Resources', icon: FileText, color: 'bg-green-500' },
  { id: 'assessment', label: 'Assessments', icon: ScrollText, color: 'bg-orange-500' },
  { id: 'note_template', label: 'Note Templates', icon: Lightbulb, color: 'bg-pink-500' },
];

const CATEGORIES = {
  homework_template: ['mindfulness', 'cbt', 'relaxation', 'journaling', 'behavioral', 'custom'],
  protocol_template: ['CBT', 'DBT', 'ACT', 'EMDR', 'Psychodynamic', 'Behavioral', 'Custom'],
  resource: ['worksheet', 'exercise', 'psychoeducation', 'reading', 'meditation', 'custom'],
  assessment: ['anxiety', 'depression', 'trauma', 'personality', 'general', 'custom'],
  note_template: ['SOAP', 'DAP', 'BIRP', 'progress', 'intake', 'custom'],
};

const AdminContentLibrary = () => {
  const [activeType, setActiveType] = useState('homework_template');
  const [items, setItems] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(false);
  const [showDialog, setShowDialog] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [formData, setFormData] = useState({
    title: '', description: '', category: '', tags: '', content: {}
  });
  const [aiTopic, setAiTopic] = useState('');
  const [aiLanguage, setAiLanguage] = useState('hindi');
  const [aiExtraInstructions, setAiExtraInstructions] = useState('');
  const [aiGenerating, setAiGenerating] = useState(false);
  const [showAiDialog, setShowAiDialog] = useState(false);

  const fetchStats = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/admin/content`);
      setStats(res.data);
    } catch (err) {
      console.error(err);
    }
  }, []);

  const fetchItems = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/admin/content/${activeType}`);
      setItems(res.data);
    } catch (err) {
      toast.error('Content load nahi ho paya');
    } finally {
      setLoading(false);
    }
  }, [activeType]);

  useEffect(() => { fetchStats(); }, [fetchStats]);
  useEffect(() => { fetchItems(); }, [fetchItems]);

  const openCreate = () => {
    setEditingItem(null);
    setFormData({ title: '', description: '', category: CATEGORIES[activeType]?.[0] || '', tags: '', content: {} });
    setShowDialog(true);
  };

  const openEdit = (item) => {
    setEditingItem(item);
    setFormData({
      title: item.title,
      description: item.description || '',
      category: item.category || '',
      tags: (item.tags || []).join(', '),
      content: item.content || {}
    });
    setShowDialog(true);
  };

  const handleSave = async () => {
    if (!formData.title.trim()) { toast.error('Title required'); return; }
    
    const payload = {
      type: activeType,
      title: formData.title.trim(),
      description: formData.description.trim(),
      category: formData.category,
      tags: formData.tags.split(',').map(t => t.trim()).filter(Boolean),
      content: formData.content
    };

    try {
      if (editingItem) {
        await axios.put(`${API}/admin/content/${activeType}/${editingItem.id}`, {
          title: payload.title, description: payload.description,
          category: payload.category, tags: payload.tags, content: payload.content
        });
        toast.success('Content updated');
      } else {
        await axios.post(`${API}/admin/content/${activeType}`, payload);
        toast.success('Content created');
      }
      setShowDialog(false);
      fetchItems();
      fetchStats();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error saving');
    }
  };

  const handleDelete = async (itemId) => {
    if (!window.confirm('Delete this content?')) return;
    try {
      await axios.delete(`${API}/admin/content/${activeType}/${itemId}`);
      toast.success('Deleted');
      fetchItems();
      fetchStats();
    } catch (err) {
      toast.error('Delete failed');
    }
  };

  const handleAiGenerate = async () => {
    if (!aiTopic.trim()) { toast.error('Topic enter karein'); return; }
    setAiGenerating(true);
    try {
      const res = await axios.post(`${API}/admin/content/${activeType}/ai-generate`, {
        type: activeType,
        topic: aiTopic.trim(),
        language: aiLanguage,
        additional_instructions: aiExtraInstructions.trim()
      });
      if (res.data.generated) {
        const generated = res.data.data;
        // Pre-fill the create form with AI-generated data
        setFormData({
          title: generated.title || '',
          description: generated.description || '',
          category: generated.category || CATEGORIES[activeType]?.[0] || '',
          tags: (generated.tags || []).join(', '),
          content: generated.content || {}
        });
        setShowAiDialog(false);
        setEditingItem(null);
        setShowDialog(true);
        toast.success('AI ne content generate kiya! Review karke save karein.');
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'AI generation failed');
    } finally {
      setAiGenerating(false);
    }
  };

  const filteredItems = items.filter(item =>
    item.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const activeConfig = CONTENT_TYPES.find(t => t.id === activeType);

  // Render extra fields for specific content types
  const renderExtraFields = () => {
    if (activeType === 'protocol_template') {
      const sessions = formData.content?.sessions || [];
      return (
        <div className="space-y-3">
          <label className="text-sm font-medium text-gray-700">Protocol Sessions</label>
          {sessions.map((s, i) => (
            <div key={i} className="flex gap-2 items-start">
              <span className="text-xs font-bold text-gray-500 mt-2 w-6">{i + 1}.</span>
              <div className="flex-1 space-y-1">
                <Input
                  placeholder="Session Title"
                  value={s.title || ''}
                  onChange={e => {
                    const updated = [...sessions];
                    updated[i] = { ...updated[i], title: e.target.value, session_number: i + 1 };
                    setFormData(prev => ({ ...prev, content: { ...prev.content, sessions: updated } }));
                  }}
                />
                <Input
                  placeholder="Goals (comma separated)"
                  value={(s.goals || []).join(', ')}
                  onChange={e => {
                    const updated = [...sessions];
                    updated[i] = { ...updated[i], goals: e.target.value.split(',').map(g => g.trim()) };
                    setFormData(prev => ({ ...prev, content: { ...prev.content, sessions: updated } }));
                  }}
                />
              </div>
              <Button variant="ghost" size="sm" onClick={() => {
                const updated = sessions.filter((_, idx) => idx !== i);
                setFormData(prev => ({ ...prev, content: { ...prev.content, sessions: updated } }));
              }}><Trash2 size={14} /></Button>
            </div>
          ))}
          <Button variant="outline" size="sm" onClick={() => {
            const updated = [...sessions, { session_number: sessions.length + 1, title: '', goals: [] }];
            setFormData(prev => ({ ...prev, content: { ...prev.content, sessions: updated } }));
          }}><Plus size={14} className="mr-1" /> Add Session</Button>
        </div>
      );
    }

    if (activeType === 'assessment') {
      const questions = formData.content?.questions || [];
      return (
        <div className="space-y-3">
          <label className="text-sm font-medium text-gray-700">Assessment Questions</label>
          {questions.map((q, i) => (
            <div key={i} className="flex gap-2 items-center">
              <span className="text-xs font-bold text-gray-500 w-6">{i + 1}.</span>
              <Input
                className="flex-1"
                placeholder="Question text"
                value={q.text || q}
                onChange={e => {
                  const updated = [...questions];
                  updated[i] = { text: e.target.value, options: q.options || [0, 1, 2, 3] };
                  setFormData(prev => ({ ...prev, content: { ...prev.content, questions: updated } }));
                }}
              />
              <Button variant="ghost" size="sm" onClick={() => {
                const updated = questions.filter((_, idx) => idx !== i);
                setFormData(prev => ({ ...prev, content: { ...prev.content, questions: updated } }));
              }}><Trash2 size={14} /></Button>
            </div>
          ))}
          <Button variant="outline" size="sm" onClick={() => {
            const updated = [...questions, { text: '', options: [0, 1, 2, 3] }];
            setFormData(prev => ({ ...prev, content: { ...prev.content, questions: updated } }));
          }}><Plus size={14} className="mr-1" /> Add Question</Button>
        </div>
      );
    }

    return null;
  };

  return (
    <div data-testid="admin-content-library">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Content Library</h1>
          <p className="text-sm text-gray-500 mt-1">Manage global content visible to all therapists</p>
        </div>
      </div>

      {/* Type Tabs */}
      <div className="flex gap-2 mb-6 flex-wrap">
        {CONTENT_TYPES.map(ct => {
          const Icon = ct.icon;
          return (
            <button
              key={ct.id}
              data-testid={`content-tab-${ct.id}`}
              onClick={() => { setActiveType(ct.id); setSearchQuery(''); }}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeType === ct.id
                  ? 'bg-primary text-white shadow-sm'
                  : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
              }`}
            >
              <Icon size={16} />
              {ct.label}
              <span className={`ml-1 text-xs px-1.5 py-0.5 rounded-full ${
                activeType === ct.id ? 'bg-white/20' : 'bg-gray-100'
              }`}>{stats[ct.id] || 0}</span>
            </button>
          );
        })}
      </div>

      {/* Search + Create */}
      <div className="flex items-center gap-3 mb-4">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <Input
            placeholder={`Search ${activeConfig?.label || ''}...`}
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="pl-9"
            data-testid="content-search"
          />
        </div>
        <Button onClick={openCreate} data-testid="create-content-btn">
          <Plus size={16} className="mr-1" /> Manual
        </Button>
        <Button 
          onClick={() => { setAiTopic(''); setAiExtraInstructions(''); setShowAiDialog(true); }}
          className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700"
          data-testid="ai-generate-btn"
        >
          <Sparkles size={16} className="mr-1" /> AI Generate
        </Button>
      </div>

      {/* Content List */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : filteredItems.length === 0 ? (
        <Card className="p-12 text-center">
          <p className="text-gray-400 mb-4">No {activeConfig?.label || 'content'} yet</p>
          <Button onClick={openCreate} variant="outline">
            <Plus size={16} className="mr-1" /> Create First
          </Button>
        </Card>
      ) : (
        <div className="grid gap-3">
          {filteredItems.map(item => (
            <Card key={item.id} className="p-4 hover:shadow-md transition-shadow" data-testid={`content-item-${item.id}`}>
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-gray-900 truncate">{item.title}</h3>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium shrink-0">
                      {item.category}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 line-clamp-2">{item.description}</p>
                  {item.tags?.length > 0 && (
                    <div className="flex gap-1 mt-2 flex-wrap">
                      {item.tags.map((tag, i) => (
                        <span key={i} className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600">{tag}</span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex gap-1 ml-3 shrink-0">
                  <Button variant="ghost" size="sm" onClick={() => openEdit(item)} data-testid={`edit-content-${item.id}`}>
                    <Edit2 size={14} />
                  </Button>
                  <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-700" onClick={() => handleDelete(item.id)} data-testid={`delete-content-${item.id}`}>
                    <Trash2 size={14} />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-lg max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingItem ? 'Edit' : 'Create'} {activeConfig?.label?.replace(/s$/, '')}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium text-gray-700">Title *</label>
              <Input
                value={formData.title}
                onChange={e => setFormData(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Enter title"
                data-testid="content-title-input"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Category</label>
              <select
                value={formData.category}
                onChange={e => setFormData(prev => ({ ...prev, category: e.target.value }))}
                className="w-full border rounded-lg px-3 py-2 text-sm"
                data-testid="content-category-select"
              >
                {(CATEGORIES[activeType] || []).map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Description / Content</label>
              <Textarea
                value={formData.description}
                onChange={e => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Enter detailed description or content..."
                rows={5}
                data-testid="content-description-input"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Tags (comma separated)</label>
              <Input
                value={formData.tags}
                onChange={e => setFormData(prev => ({ ...prev, tags: e.target.value }))}
                placeholder="e.g., anxiety, cbt, worksheet"
                data-testid="content-tags-input"
              />
            </div>
            {renderExtraFields()}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>Cancel</Button>
            <Button onClick={handleSave} data-testid="save-content-btn">
              {editingItem ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* AI Generate Dialog */}
      <Dialog open={showAiDialog} onOpenChange={setShowAiDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles size={20} className="text-violet-600" />
              AI se {activeConfig?.label?.replace(/s$/, '')} Generate
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium text-gray-700">Topic / Subject *</label>
              <Input
                value={aiTopic}
                onChange={e => setAiTopic(e.target.value)}
                placeholder="e.g., Social Anxiety, Grief Counseling, Sleep Hygiene..."
                data-testid="ai-topic-input"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Language</label>
              <select
                value={aiLanguage}
                onChange={e => setAiLanguage(e.target.value)}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              >
                <option value="hindi">Hindi</option>
                <option value="english">English</option>
                <option value="hinglish">Hinglish</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Extra Instructions (optional)</label>
              <Textarea
                value={aiExtraInstructions}
                onChange={e => setAiExtraInstructions(e.target.value)}
                placeholder="e.g., For children ages 8-12, Include visual exercises..."
                rows={3}
              />
            </div>
            <p className="text-xs text-gray-400">AI generate karega → aap review karenge → phir save</p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAiDialog(false)} disabled={aiGenerating}>Cancel</Button>
            <Button 
              onClick={handleAiGenerate} 
              disabled={aiGenerating || !aiTopic.trim()}
              className="bg-gradient-to-r from-violet-600 to-indigo-600"
              data-testid="ai-generate-submit-btn"
            >
              {aiGenerating ? (
                <><Loader2 size={16} className="mr-1 animate-spin" /> Generating...</>
              ) : (
                <><Sparkles size={16} className="mr-1" /> Generate</>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminContentLibrary;
