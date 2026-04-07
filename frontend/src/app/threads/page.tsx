"use client";

import React, { useState, useEffect, useMemo, Suspense } from "react";
import Link from "next/link";
import { useQueryState } from "nuqs";
import { format } from "date-fns";
import { MessageSquare, ArrowLeft, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectLabel,
  SelectItem,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import type { ThreadItem } from "@/app/hooks/useThreads";
import { useThreads } from "@/app/hooks/useThreads";
import { useDeleteThread } from "@/app/hooks/useDeleteThread";
import { getConfig, StandaloneConfig } from "@/lib/config";
import { ClientProvider } from "@/providers/ClientProvider";
import type { Thread } from "@langchain/langgraph-sdk";

type StatusFilter = "all" | "idle" | "busy" | "interrupted" | "error";
export type { StatusFilter };

const GROUP_LABELS = {
  interrupted: "Requiring Attention",
  today: "Today",
  yesterday: "Yesterday",
  week: "This Week",
  older: "Older",
} as const;

const STATUS_COLORS: Record<ThreadItem["status"], string> = {
  idle: "bg-green-500",
  busy: "bg-blue-500",
  interrupted: "bg-orange-500",
  error: "bg-red-600",
};

function getThreadColor(status: ThreadItem["status"]): string {
  return STATUS_COLORS[status] ?? "bg-gray-400";
}

function formatTime(date: Date, now = new Date()): string {
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === 0) return format(date, "HH:mm");
  if (days === 1) return "Yesterday";
  if (days < 7) return format(date, "EEEE");
  return format(date, "MM/dd");
}

function StatusFilterItem({
  status,
  label,
}: {
  status: ThreadItem["status"];
  label: string;
}) {
  return (
    <span className="inline-flex items-center gap-2">
      <span
        className={cn(
          "inline-block size-2 rounded-full",
          getThreadColor(status)
        )}
      />
      {label}
    </span>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <p className="text-sm text-red-600">Failed to load threads</p>
      <p className="mt-1 text-xs text-muted-foreground">{message}</p>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="space-y-2 p-4">
      {Array.from({ length: 10 }).map((_, i) => (
        <Skeleton key={i} className="h-16 w-full" />
      ))}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <MessageSquare className="mb-2 h-12 w-12 text-gray-300" />
      <p className="text-sm text-muted-foreground">No threads found</p>
    </div>
  );
}

function ThreadListContent() {
  const [statusFilter, setStatusFilter] = useQueryState("status");
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [threadToDelete, setThreadToDelete] = useState<ThreadItem | null>(null);

  const threads = useThreads({
    status: (statusFilter === "all" || !statusFilter) 
      ? undefined 
      : statusFilter as Thread["status"],
    limit: 50,
  });

  const deleteMutation = useDeleteThread();

  const handleDeleteClick = (thread: ThreadItem) => {
    setThreadToDelete(thread);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (threadToDelete) {
      await deleteMutation.trigger(threadToDelete.id);
      setDeleteDialogOpen(false);
      setThreadToDelete(null);
    }
  };

  const flattened = useMemo(() => {
    return threads.data?.flat() ?? [];
  }, [threads.data]);

  const isEmpty = threads.data?.at(0)?.length === 0;

  const grouped = useMemo(() => {
    const now = new Date();
    const groups: Record<keyof typeof GROUP_LABELS, ThreadItem[]> = {
      interrupted: [],
      today: [],
      yesterday: [],
      week: [],
      older: [],
    };

    flattened.forEach((thread) => {
      if (thread.status === "interrupted") {
        groups.interrupted.push(thread);
        return;
      }

      const diff = now.getTime() - thread.updatedAt.getTime();
      const days = Math.floor(diff / (1000 * 60 * 60 * 24));

      if (days === 0) {
        groups.today.push(thread);
      } else if (days === 1) {
        groups.yesterday.push(thread);
      } else if (days < 7) {
        groups.week.push(thread);
      } else {
        groups.older.push(thread);
      }
    });

    return groups;
  }, [flattened]);

  return (
    <div className="flex h-full flex-col">
      <div className="grid flex-shrink-0 grid-cols-[1fr_auto] items-center gap-3 border-b border-border p-4">
        <h2 className="text-lg font-semibold tracking-tight">All Threads</h2>
        <div className="flex items-center gap-2">
          <Select
            value={statusFilter ?? "all"}
            onValueChange={(v) => setStatusFilter(v === "all" ? null : v)}
          >
            <SelectTrigger className="w-fit">
              <SelectValue />
            </SelectTrigger>
            <SelectContent align="end">
              <SelectItem value="all">All statuses</SelectItem>
              <SelectSeparator />
              <SelectGroup>
                <SelectLabel>Active</SelectLabel>
                <SelectItem value="idle">
                  <StatusFilterItem status="idle" label="Idle" />
                </SelectItem>
                <SelectItem value="busy">
                  <StatusFilterItem status="busy" label="Busy" />
                </SelectItem>
              </SelectGroup>
              <SelectSeparator />
              <SelectGroup>
                <SelectLabel>Attention</SelectLabel>
                <SelectItem value="interrupted">
                  <StatusFilterItem status="interrupted" label="Interrupted" />
                </SelectItem>
                <SelectItem value="error">
                  <StatusFilterItem status="error" label="Error" />
                </SelectItem>
              </SelectGroup>
            </SelectContent>
          </Select>
        </div>
      </div>

      <ScrollArea className="h-0 flex-1">
        {threads.error && <ErrorState message={threads.error.message} />}

        {!threads.error && !threads.data && threads.isLoading && (
          <LoadingState />
        )}

        {!threads.error && !threads.isLoading && isEmpty && <EmptyState />}

        {!threads.error && !isEmpty && (
          <div className="box-border w-full max-w-full overflow-hidden p-2">
            {(
              Object.keys(GROUP_LABELS) as Array<keyof typeof GROUP_LABELS>
            ).map((group) => {
              const groupThreads = grouped[group];
              if (groupThreads.length === 0) return null;

              return (
                <div key={group} className="mb-4">
                  <h4 className="m-0 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    {GROUP_LABELS[group]}
                  </h4>
                  <div className="flex flex-col gap-1">
                    {groupThreads.map((thread) => (
                      <div
                        key={thread.id}
                        className={cn(
                          "group flex w-full items-center gap-3 rounded-lg px-3 py-3 transition-colors duration-200",
                          "hover:bg-accent",
                          "border border-transparent bg-transparent"
                        )}
                      >
                        <Link
                          href={`/threads/${thread.id}`}
                          className="flex min-w-0 flex-1 cursor-pointer items-center gap-3"
                        >
                          <div className="min-w-0 flex-1">
                            <div className="mb-1 flex items-center justify-between">
                              <h3 className="truncate text-sm font-semibold">
                                {thread.title}
                              </h3>
                              <span className="ml-2 flex-shrink-0 text-xs text-muted-foreground">
                                {formatTime(thread.updatedAt)}
                              </span>
                            </div>
                            <div className="flex items-center justify-between">
                              <p className="flex-1 truncate text-sm text-muted-foreground">
                                {thread.description}
                              </p>
                              <div className="ml-2 flex-shrink-0">
                                <div
                                  className={cn(
                                    "h-2 w-2 rounded-full",
                                    getThreadColor(thread.status)
                                  )}
                                />
                              </div>
                            </div>
                          </div>
                        </Link>
                        <button
                          onClick={(e) => {
                            e.preventDefault();
                            handleDeleteClick(thread);
                          }}
                          className="flex-shrink-0 rounded-md p-2 opacity-0 transition-opacity hover:bg-red-100 hover:text-red-600 group-hover:opacity-100"
                          title="Delete thread"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </ScrollArea>
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Thread</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{threadToDelete?.title}"? 
              This will permanently delete the thread and all its messages.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleConfirmDelete}
              disabled={deleteMutation.isMutating}
            >
              {deleteMutation.isMutating ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

interface ThreadsPageContentProps {
  config: StandaloneConfig;
}

function ThreadsPageContent({ config }: ThreadsPageContentProps) {
  const langsmithApiKey =
    config?.langsmithApiKey || process.env.NEXT_PUBLIC_LANGSMITH_API_KEY || "";

  return (
    <ClientProvider
      deploymentUrl={config.deploymentUrl}
      apiKey={langsmithApiKey}
    >
      <ThreadListContent />
    </ClientProvider>
  );
}

function ThreadsPageLoader() {
  return (
    <div className="flex h-full flex-col">
      <div className="grid flex-shrink-0 grid-cols-[1fr_auto] items-center gap-3 border-b border-border p-4">
        <Skeleton className="h-6 w-24" />
        <Skeleton className="h-8 w-32" />
      </div>
      <div className="flex-1 p-4">
        <Skeleton className="h-16 w-full mb-2" />
        <Skeleton className="h-16 w-full mb-2" />
        <Skeleton className="h-16 w-full mb-2" />
      </div>
    </div>
  );
}

export default function ThreadsPage() {
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
    <Suspense fallback={<ThreadsPageLoader />}>
      <ThreadsPageContent config={config} />
    </Suspense>
  );
}
