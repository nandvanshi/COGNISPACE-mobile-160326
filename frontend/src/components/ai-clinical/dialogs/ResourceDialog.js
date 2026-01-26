import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../ui/dialog';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { Textarea } from '../../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';

const ResourceDialog = ({
  open,
  onOpenChange,
  newResource,
  setNewResource,
  handleCreateResource
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>Create New Resource</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <Label>Title *</Label>
            <Input
              value={newResource.title}
              onChange={(e) => setNewResource({...newResource, title: e.target.value})}
              placeholder="e.g., Anxiety Thought Record"
              data-testid="resource-title-input"
            />
          </div>

          <div>
            <Label>Category *</Label>
            <Select 
              value={newResource.category} 
              onValueChange={(v) => setNewResource({...newResource, category: v})}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="worksheet">Worksheet</SelectItem>
                <SelectItem value="exercise">Exercise</SelectItem>
                <SelectItem value="psychoeducation">Psychoeducation</SelectItem>
                <SelectItem value="reading">Reading Material</SelectItem>
                <SelectItem value="meditation">Meditation/Mindfulness</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>Content *</Label>
            <Textarea
              value={newResource.content}
              onChange={(e) => setNewResource({...newResource, content: e.target.value})}
              placeholder="Enter the full content of the resource..."
              rows={10}
              data-testid="resource-content-input"
            />
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateResource} data-testid="save-resource-btn">
              Create Resource
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ResourceDialog;
