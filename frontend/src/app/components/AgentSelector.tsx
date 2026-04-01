"use client";

import { Loader2, Bot } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAgents } from "@/app/hooks/useAgents";
import { getConfig, saveConfig, StandaloneConfig } from "@/lib/config";

interface AgentSelectorProps {
  onAgentChange?: (agentId: string) => void;
}

export function AgentSelector({ onAgentChange }: AgentSelectorProps) {
  const { agentGraphIds, isLoading, error } = useAgents();

  const config = getConfig();
  const currentAgentId = config?.assistantId ?? "";

  const handleValueChange = (value: string) => {
    const newConfig: StandaloneConfig = {
      ...config,
      assistantId: value,
    } as StandaloneConfig;
    saveConfig(newConfig);
    onAgentChange?.(value);
  };

  if (error) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <span className="text-red-500">Failed to load agents</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <Bot className="h-4 w-4 text-muted-foreground" />
      <Select
        value={currentAgentId}
        onValueChange={handleValueChange}
        disabled={isLoading}
      >
        <SelectTrigger className="w-[180px]">
          {isLoading ? (
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Loading...</span>
            </div>
          ) : (
            <SelectValue placeholder="Select agent" />
          )}
        </SelectTrigger>
        <SelectContent>
          {agentGraphIds.length === 0 && !isLoading && (
            <SelectItem value="empty" disabled>
              No agents found
            </SelectItem>
          )}
          {agentGraphIds.map((agentId) => (
            <SelectItem key={agentId} value={agentId}>
              {agentId}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
