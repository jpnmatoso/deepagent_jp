"use client";

import { useEffect, useState, Suspense } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, MessageSquare, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Message } from "@langchain/langgraph-sdk";
import { cn } from "@/lib/utils";
import { getConfig, StandaloneConfig } from "@/lib/config";
import { ClientProvider, useClient } from "@/providers/ClientProvider";
import { MarkdownContent } from "@/app/components/MarkdownContent";

interface ThreadMessage {
  id: string;
  type: "human" | "ai" | "system" | "tool";
  content: string;
  created_at: string;
  name?: string;
}

function extractStringFromMessageContent(message: Message): string {
  const content = message.content;
  if (typeof content === "string") {
    return content;
  }
  if (Array.isArray(content)) {
    return content
      .map((c: any) => {
        if (c.type === "text") return c.text;
        if (c.type === "image" && "image_url" in c) return "[Image]";
        return "";
      })
      .filter(Boolean)
      .join("\n");
  }
  return "";
}

function MessageBubble({ message }: { message: ThreadMessage }) {
  const isUser = message.type === "human";
  const hasContent = message.content && message.content.trim() !== "";

  return (
    <div
      className={cn(
        "flex w-full max-w-full overflow-x-hidden",
        isUser && "flex-row-reverse"
      )}
    >
      <div
        className={cn(
          "min-w-0 max-w-full",
          isUser ? "max-w-[70%]" : "w-full"
        )}
      >
        {hasContent && (
          <div className={cn("relative flex items-end gap-0")}>
            <div
              className={cn(
                "mt-4 overflow-hidden break-words text-sm font-normal leading-[150%]",
                isUser
                  ? "rounded-xl rounded-br-none border border-border px-3 py-2"
                  : "text-primary"
              )}
              style={
                isUser
                  ? { backgroundColor: "var(--color-user-message-bg)" }
                  : undefined
              }
            >
              {isUser ? (
                <p className="m-0 whitespace-pre-wrap break-words text-sm leading-relaxed">
                  {message.content}
                </p>
              ) : (
                <MarkdownContent content={message.content} />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function ThreadHeader({ threadId, title, status }: { threadId: string; title: string; status: string }) {
  return (
    <div className="flex h-16 flex-shrink-0 items-center justify-between border-b border-border px-6">
      <div className="flex items-center gap-4">
        <Link href="/threads">
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex flex-col">
          <h1 className="text-lg font-semibold truncate max-w-[400px]">{title || "Untitled Thread"}</h1>
          <span className="text-xs text-muted-foreground">
            ID: {threadId.slice(0, 8)}... · Status: {status}
          </span>
        </div>
      </div>
    </div>
  );
}

function ThreadContent() {
  const params = useParams();
  const threadId = params.threadId as string;
  const client = useClient();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [threadData, setThreadData] = useState<{
    thread: any;
    messages: ThreadMessage[];
  } | null>(null);

  useEffect(() => {
    async function fetchThread() {
      if (!threadId || !client) return;
      
      try {
        setLoading(true);
        const thread = await client.threads.get(threadId);
        
        const messages: ThreadMessage[] = [];
        
        if (thread.values && typeof thread.values === "object") {
          const values = thread.values as any;
          if (Array.isArray(values.messages)) {
            values.messages.forEach((msg: Message) => {
              messages.push({
                id: msg.id || `msg-${messages.length}`,
                type: msg.type as ThreadMessage["type"],
                content: extractStringFromMessageContent(msg),
                created_at: (msg as any).created_at || new Date().toISOString(),
                name: msg.name,
              });
            });
          }
        }
        
        setThreadData({ thread, messages });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load thread");
      } finally {
        setLoading(false);
      }
    }
    
    fetchThread();
  }, [threadId, client]);

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center">
        <MessageSquare className="mb-4 h-12 w-12 text-red-400" />
        <p className="text-red-500">Error: {error}</p>
        <Link href="/threads">
          <Button className="mt-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Threads
          </Button>
        </Link>
      </div>
    );
  }

  if (!threadData) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center">
        <MessageSquare className="mb-4 h-12 w-12 text-gray-300" />
        <p className="text-muted-foreground">Thread not found</p>
        <Link href="/threads">
          <Button className="mt-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Threads
          </Button>
        </Link>
      </div>
    );
  }

  const { messages } = threadData;
  const title = messages.find(m => m.type === "human")?.content?.slice(0, 50) || "Untitled Thread";

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <ThreadHeader 
        threadId={threadId} 
        title={title} 
        status={threadData.thread.status || "unknown"} 
      />
      
      <ScrollArea className="flex-1 p-6">
        <div className="mx-auto max-w-4xl">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <MessageSquare className="mb-4 h-12 w-12 text-gray-300" />
              <p className="text-muted-foreground">No messages in this thread</p>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

interface ThreadPageContentProps {
  config: StandaloneConfig;
}

function ThreadPageContent({ config }: ThreadPageContentProps) {
  const langsmithApiKey =
    config?.langsmithApiKey || process.env.NEXT_PUBLIC_LANGSMITH_API_KEY || "";

  return (
    <ClientProvider
      deploymentUrl={config.deploymentUrl}
      apiKey={langsmithApiKey}
    >
      <ThreadContent />
    </ClientProvider>
  );
}

function ThreadPageLoader() {
  return (
    <div className="flex flex-1 flex-col">
      <div className="flex h-16 flex-shrink-0 items-center justify-between border-b border-border px-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-8 w-8" />
          <div className="flex flex-col gap-2">
            <Skeleton className="h-5 w-48" />
            <Skeleton className="h-3 w-32" />
          </div>
        </div>
      </div>
      <div className="flex-1 p-6">
        <div className="mx-auto max-w-4xl space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      </div>
    </div>
  );
}

export default function ThreadPage() {
  const [config, setConfig] = useState<StandaloneConfig | null>(null);

  useEffect(() => {
    const savedConfig = getConfig();
    if (savedConfig) {
      setConfig(savedConfig);
    }
  }, []);

  if (!config) {
    return (
      <div className="flex h-full flex-col items-center justify-center">
        <MessageSquare className="mb-4 h-16 w-16 text-gray-300" />
        <h2 className="text-xl font-semibold">No Configuration</h2>
        <p className="mt-2 text-muted-foreground">
          Please configure your deployment in the main page first.
        </p>
        <Link href="/">
          <Button className="mt-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Go to Main Page
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <Suspense fallback={<ThreadPageLoader />}>
      <ThreadPageContent config={config} />
    </Suspense>
  );
}
