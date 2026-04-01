"use client";

import useSWR from "swr";
import { useClient } from "@/providers/ClientProvider";

export interface Agent {
  assistant_id: string;
  graph_id: string;
  name?: string;
}

export function useAgents() {
  const client = useClient();

  const { data, error, isLoading, mutate } = useSWR<Agent[]>(
    "agents-list",
    async () => {
      const assistants = await client.assistants.search({ limit: 100 });
      return assistants.filter((a) => a.graph_id);
    },
    {
      revalidateOnFocus: false,
      dedupingInterval: 60000,
    }
  );

  const agentGraphIds = data?.map((a) => a.graph_id).filter(Boolean) ?? [];

  return {
    agents: data ?? [],
    agentGraphIds,
    isLoading,
    error,
    mutate,
  };
}
