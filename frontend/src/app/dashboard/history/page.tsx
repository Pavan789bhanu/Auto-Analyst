"use client";

import { useEffect, useState } from "react";
import { api, type Analysis } from "@/lib/api";
import { useAuth } from "@/components/providers/auth-provider";
import { AnalysisResult } from "@/components/dashboard/analysis-result";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDate } from "@/lib/utils";

export default function HistoryPage() {
  const { token } = useAuth();
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    api
      .listAnalyses(token)
      .then((data) => {
        setAnalyses(data.analyses);
        if (data.analyses[0]) {
          setSelectedId(data.analyses[0].id);
        }
      })
      .finally(() => setLoading(false));
  }, [token]);

  const selectedAnalysis = analyses.find((item) => item.id === selectedId) ?? null;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Analysis history</h1>
        <p className="mt-2 text-muted-foreground">
          Review past queries, agent plans, and generated code.
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-[360px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Past analyses</CardTitle>
            <CardDescription>Click an item to view full details</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {loading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((item) => (
                  <div key={item} className="h-20 animate-pulse rounded-lg bg-muted" />
                ))}
              </div>
            ) : analyses.length === 0 ? (
              <p className="text-sm text-muted-foreground">No analyses yet.</p>
            ) : (
              analyses.map((analysis) => (
                <button
                  key={analysis.id}
                  type="button"
                  onClick={() => setSelectedId(analysis.id)}
                  className={`w-full rounded-xl px-4 py-3 text-left ${
                    selectedId === analysis.id ? "glass-selected" : "glass-tile"
                  }`}
                >
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <p className="truncate font-medium">{analysis.query}</p>
                    <Badge
                      variant={
                        analysis.status === "completed"
                          ? "success"
                          : analysis.status === "failed"
                            ? "destructive"
                            : "warning"
                      }
                    >
                      {analysis.status}
                    </Badge>
                  </div>
                  <p className="truncate text-sm text-muted-foreground">
                    {analysis.filename}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {formatDate(analysis.created_at)}
                  </p>
                </button>
              ))
            )}
          </CardContent>
        </Card>

        {selectedAnalysis ? (
          <AnalysisResult analysis={selectedAnalysis} />
        ) : (
          <Card>
            <CardContent className="flex min-h-[320px] items-center justify-center p-10 text-sm text-muted-foreground">
              Select an analysis to view details.
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
