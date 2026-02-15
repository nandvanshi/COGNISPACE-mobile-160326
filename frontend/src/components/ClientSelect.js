import React, { useState } from 'react';
import { Check, ChevronsUpDown, Search, User, Phone } from 'lucide-react';
import { cn } from '../lib/utils';
import { Button } from './ui/button';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from './ui/command';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from './ui/popover';

/**
 * Searchable Client Select Component
 * Shows client name with mobile number and supports keyboard search
 */
const ClientSelect = ({ 
  clients = [], 
  value, 
  onValueChange, 
  placeholder = "Select client...",
  disabled = false,
  className = ""
}) => {
  const [open, setOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Find selected client
  const selectedClient = clients.find(client => client.id === value);

  // Filter clients based on search query
  const filteredClients = clients.filter(client => {
    const query = searchQuery.toLowerCase();
    const name = (client.full_name || '').toLowerCase();
    const mobile = (client.mobile || '').toLowerCase();
    const clientCode = (client.client_id || '').toLowerCase();
    return name.includes(query) || mobile.includes(query) || clientCode.includes(query);
  });

  const handleSelect = (clientId) => {
    onValueChange(clientId === value ? "" : clientId);
    setOpen(false);
    setSearchQuery("");
  };

  const formatMobile = (mobile) => {
    if (!mobile) return '';
    // Show last 4 digits with mask
    if (mobile.length >= 4) {
      return `***${mobile.slice(-4)}`;
    }
    return mobile;
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          disabled={disabled}
          className={cn(
            "w-full justify-between font-normal",
            !value && "text-muted-foreground",
            className
          )}
          data-testid="client-select-trigger"
        >
          {selectedClient ? (
            <div className="flex items-center gap-2 truncate">
              <User size={14} className="text-muted-foreground shrink-0" />
              <span className="truncate">{selectedClient.full_name}</span>
              {selectedClient.mobile && (
                <span className="text-xs text-muted-foreground shrink-0">
                  ({formatMobile(selectedClient.mobile)})
                </span>
              )}
            </div>
          ) : (
            <span>{placeholder}</span>
          )}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[350px] p-0" align="start">
        <Command shouldFilter={false}>
          <div className="flex items-center border-b px-3">
            <Search className="mr-2 h-4 w-4 shrink-0 opacity-50" />
            <input
              placeholder="Search by name or mobile..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex h-10 w-full rounded-md bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground"
              data-testid="client-search-input"
            />
          </div>
          <CommandList>
            <CommandEmpty>No client found.</CommandEmpty>
            <CommandGroup className="max-h-[300px] overflow-y-auto">
              {filteredClients.map((client) => (
                <CommandItem
                  key={client.id}
                  value={client.id}
                  onSelect={() => handleSelect(client.id)}
                  className="cursor-pointer"
                  data-testid={`client-option-${client.id}`}
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      value === client.id ? "opacity-100" : "opacity-0"
                    )}
                  />
                  <div className="flex flex-col flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium truncate">{client.full_name}</span>
                      {client.client_id && (
                        <span className="text-xs bg-muted px-1.5 py-0.5 rounded text-muted-foreground shrink-0">
                          {client.client_id}
                        </span>
                      )}
                    </div>
                    {client.mobile && (
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Phone size={10} />
                        <span>{client.mobile}</span>
                      </div>
                    )}
                  </div>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
};

export default ClientSelect;
