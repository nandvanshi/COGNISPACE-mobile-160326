import React from 'react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Library, Plus } from 'lucide-react';

const ResourcesTab = ({
  clients,
  resources,
  setShowResourceDialog,
  handleAssignResource,
  isReadOnly
}) => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-lg font-semibold">Resource Library</h3>
          <p className="text-sm text-muted-foreground">Worksheets, exercises, and psychoeducation materials</p>
        </div>
        {!isReadOnly && (
          <Button onClick={() => setShowResourceDialog(true)} data-testid="create-resource-btn">
            <Plus size={16} className="mr-2" /> Add Resource
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {resources.map(resource => (
          <Card key={resource.id} className="p-4 bg-white/70 backdrop-blur-xl border border-border/40">
            <div className="flex items-start justify-between mb-2">
              <span className={`text-xs px-2 py-0.5 rounded-full ${
                resource.category === 'worksheet' ? 'bg-purple-100 text-purple-700' :
                resource.category === 'exercise' ? 'bg-green-100 text-green-700' :
                resource.category === 'psychoeducation' ? 'bg-blue-100 text-blue-700' :
                resource.category === 'meditation' ? 'bg-pink-100 text-pink-700' :
                'bg-gray-100 text-gray-700'
              }`}>
                {resource.category}
              </span>
              <span className="text-xs text-muted-foreground">Used {resource.usage_count}x</span>
            </div>
            <h4 className="font-medium mb-2">{resource.title}</h4>
            <p className="text-sm text-muted-foreground line-clamp-3 mb-3">
              {(resource.content || '').substring(0, 150)}...
            </p>
            <div className="flex gap-2">
              <Select onValueChange={(clientId) => handleAssignResource(resource.id, clientId)}>
                <SelectTrigger className="flex-1" disabled={isReadOnly}>
                  <SelectValue placeholder="Assign to..." />
                </SelectTrigger>
                <SelectContent>
                  {clients.map(c => (
                    <SelectItem key={c.id} value={c.id}>{c.full_name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </Card>
        ))}
      </div>

      {resources.length === 0 && (
        <Card className="p-8 text-center bg-white/70 backdrop-blur-xl border border-border/40">
          <Library className="mx-auto text-muted-foreground mb-4" size={48} />
          <h3 className="font-medium mb-2">No Resources Yet</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Create worksheets, exercises, and educational materials for your clients.
          </p>
          {!isReadOnly && (
            <Button onClick={() => setShowResourceDialog(true)}>
              <Plus size={16} className="mr-2" /> Create First Resource
            </Button>
          )}
        </Card>
      )}
    </div>
  );
};

export default ResourcesTab;
