import { useCallback } from "react";
import useSWRMutation from "swr/mutation";
import { Client } from "@langchain/langgraph-sdk";
import { getConfig } from "@/lib/config";

async function deleteThreadFetcher(
  url: string,
  { arg }: { arg: string }
) {
  const config = getConfig();
  const deploymentUrl = config?.deploymentUrl || "";
  const apiKey = config?.langsmithApiKey || process.env.NEXT_PUBLIC_LANGSMITH_API_KEY || "";

  const client = new Client({
    apiUrl: deploymentUrl,
    defaultHeaders: apiKey ? { "X-Api-Key": apiKey } : {},
  });

  await client.threads.delete(arg);
  return arg;
}

export function useDeleteThread() {
  return useSWRMutation<string, unknown, string, string>(
    "delete-thread",
    deleteThreadFetcher
  );
}
