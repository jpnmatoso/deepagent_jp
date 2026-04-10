"use client";

import React, { useState, useEffect, useCallback, Suspense } from "react";
import Link from "next/link";
import { useQueryState } from "nuqs";
import { getConfig, saveConfig, StandaloneConfig } from "@/lib/config";
import { Button } from "@/components/ui/button";
import { AgentSelector } from "@/app/components/AgentSelector";
import { Assistant } from "@langchain/langgraph-sdk";
import { ClientProvider, useClient } from "@/providers/ClientProvider";
import { MessagesSquare, SquarePen, List, LogOut } from "lucide-react";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { ThreadList } from "@/app/components/ThreadList";
import { ChatProvider } from "@/providers/ChatProvider";
import { ChatInterface } from "@/app/components/ChatInterface";
import { useAuth } from "@/providers/AuthProvider";

interface HomePageInnerProps {
  config: StandaloneConfig;
  onAgentChange?: () => void;
}

function HomePageInner({
  config,
  onAgentChange,
}: HomePageInnerProps) {
  const client = useClient();
  const [threadId, setThreadId] = useQueryState("threadId");
  const [sidebar, setSidebar] = useQueryState("sidebar");

  const [mutateThreads, setMutateThreads] = useState<(() => void) | null>(null);
  const [interruptCount, setInterruptCount] = useState(0);
  const [assistant, setAssistant] = useState<Assistant | null>(null);

  const fetchAssistant = useCallback(async () => {
    const isUUID =
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
        config.assistantId
      );

    if (isUUID) {
      // We should try to fetch the assistant directly with this UUID
      try {
        const data = await client.assistants.get(config.assistantId);
        setAssistant(data);
      } catch (error) {
        console.error("Failed to fetch assistant:", error);
        setAssistant({
          assistant_id: config.assistantId,
          graph_id: config.assistantId,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          config: {},
          metadata: {},
          version: 1,
          name: "Assistant",
          context: {},
        });
      }
    } else {
      try {
        // We should try to list out the assistants for this graph, and then use the default one.
        // TODO: Paginate this search, but 100 should be enough for graph name
        const assistants = await client.assistants.search({
          graphId: config.assistantId,
          limit: 100,
        });
        const defaultAssistant = assistants.find(
          (assistant) => assistant.metadata?.["created_by"] === "system"
        );
        if (defaultAssistant === undefined) {
          throw new Error("No default assistant found");
        }
        setAssistant(defaultAssistant);
      } catch (error) {
        console.error(
          "Failed to find default assistant from graph_id: try setting the assistant_id directly:",
          error
        );
        setAssistant({
          assistant_id: config.assistantId,
          graph_id: config.assistantId,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          config: {},
          metadata: {},
          version: 1,
          name: config.assistantId,
          context: {},
        });
      }
    }
  }, [client, config.assistantId]);

  useEffect(() => {
    fetchAssistant();
  }, [fetchAssistant]);

  return (
    <div className="flex h-screen flex-col">
      <header className="flex h-16 items-center justify-between border-b border-border px-6">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-semibold">Deep Agent UI</h1>
          {!sidebar && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSidebar("1")}
              className="rounded-md border border-border bg-card p-3 text-foreground hover:bg-accent"
            >
              <MessagesSquare className="mr-2 h-4 w-4" />
              Threads
              {interruptCount > 0 && (
                <span className="ml-2 inline-flex min-h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] text-destructive-foreground">
                  {interruptCount}
                </span>
              )}
            </Button>
          )}
        </div>
        <div className="flex items-center gap-2">
          <AgentSelector
            onAgentChange={() => {
              onAgentChange?.();
              setThreadId(null);
            }}
          />
          <Link href="/threads">
            <Button variant="outline" size="sm">
              <List className="mr-2 h-4 w-4" />
              All Threads
            </Button>
          </Link>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setThreadId(null)}
            disabled={!threadId}
            className="border-[#2F6868] bg-[#2F6868] text-white hover:bg-[#2F6868]/80"
          >
            <SquarePen className="mr-2 h-4 w-4" />
            New Thread
          </Button>
          <LogoutButton />
        </div>
      </header>

        <div className="flex-1 overflow-hidden">
          <ResizablePanelGroup
            direction="horizontal"
            autoSaveId="standalone-chat"
          >
            {sidebar && (
              <>
                <ResizablePanel
                  id="thread-history"
                  order={1}
                  defaultSize={25}
                  minSize={20}
                  className="relative min-w-[380px]"
                >
                  <ThreadList
                    onThreadSelect={async (id) => {
                      await setThreadId(id);
                    }}
                    onMutateReady={(fn) => setMutateThreads(() => fn)}
                    onClose={() => setSidebar(null)}
                    onInterruptCountChange={setInterruptCount}
                  />
                </ResizablePanel>
                <ResizableHandle />
              </>
            )}

            <ResizablePanel
              id="chat"
              className="relative flex flex-col"
              order={2}
            >
              <ChatProvider
                activeAssistant={assistant}
                onHistoryRevalidate={() => mutateThreads?.()}
              >
                <ChatInterface assistant={assistant} />
              </ChatProvider>
            </ResizablePanel>
          </ResizablePanelGroup>
        </div>
      </div>
  );
}

function LogoutButton() {
  const { logout } = useAuth();

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={logout}
      title="Sair"
    >
      <LogOut className="h-4 w-4" />
    </Button>
  );
}

const DEFAULT_BACKEND_URL =
  typeof process.env.NEXT_PUBLIC_DEPLOYMENT_URL === 'string' && process.env.NEXT_PUBLIC_DEPLOYMENT_URL === ''
    ? `${window.location.protocol}//${window.location.host}/api/lg`
    : process.env.NEXT_PUBLIC_DEPLOYMENT_URL || "http://localhost:8101";

function HomePageContent() {
  const [config, setConfig] = useState<StandaloneConfig | null>(null);
  const [agentChangeCounter, setAgentChangeCounter] = useState(0);
  const [, setAssistantId] = useQueryState("assistantId");

  useEffect(() => {
    const savedConfig = getConfig();
    let configToUse: StandaloneConfig;

    if (savedConfig && savedConfig.assistantId) {
      configToUse = savedConfig;
    } else {
      configToUse = {
        deploymentUrl: DEFAULT_BACKEND_URL,
        assistantId: "",
      };
      saveConfig(configToUse);
    }

    setConfig(configToUse);
    if (configToUse.assistantId) {
      setAssistantId(configToUse.assistantId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleAgentChange = useCallback(() => {
    const savedConfig = getConfig();
    if (savedConfig) {
      setConfig({ ...savedConfig });
      setAgentChangeCounter((c) => c + 1);
    }
  }, []);

  const langsmithApiKey =
    config?.langsmithApiKey || process.env.NEXT_PUBLIC_LANGSMITH_API_KEY || "";

  if (!config) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  return (
    <ClientProvider
      deploymentUrl={config.deploymentUrl}
      apiKey={langsmithApiKey}
      key={agentChangeCounter}
    >
      <HomePageInner
        config={config}
        onAgentChange={handleAgentChange}
      />
    </ClientProvider>
  );
}

export default function HomePage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center">
          <p className="text-muted-foreground">Loading...</p>
        </div>
      }
    >
      <HomePageContent />
    </Suspense>
  );
}
