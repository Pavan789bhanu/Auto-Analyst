"use client";

import { useEffect, useState } from "react";
import { BrainCircuit, Loader2, Sparkles } from "lucide-react";
import { ApiError, api, type Analysis, type Dataset } from "@/lib/api";
import { useAuth } from "@/components/providers/auth-provider";
import { AnalysisResult } from "@/components/dashboard/analysis-result";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

const exampleQueries = [
  "Perform exploratory data analysis with summary statistics and correlations",
  "Build a regression model and show key statistical metrics",
  "Create visualizations to understand trends and distributions",
];

export default function AnalyzePage() {
  const { token, refreshProfile } = useAuth();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<Analysis | null>(null);

  useEffect(() => {
    if (!token) return;
    api.listDatasets(token).then((data) => {
      setDatasets(data.datasets);
      if (data.datasets[0]) {
        setSelectedDatasetId(data.datasets[0].id);
      }
    });
  }, [token]);

  async function handleAnalyze() {
    if (!token || !selectedDatasetId || !query.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const response = await api.createAnalysis(token, {
        dataset_id: selectedDatasetId,
        query: query.trim(),
      });
      setResult(response.analysis);
      await refreshProfile();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Analysis failed.");
    } finally {
      setLoading(false);
    }
  }

  const selectedDataset = datasets.find((item) => item.id === selectedDatasetId);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Run analysis</h1>
        <p className="mt-2 text-muted-foreground">
          Ask a question in plain English and let AI agents generate your analysis pipeline.
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-[380px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Analysis setup</CardTitle>
            <CardDescription>
              Choose a dataset and describe what you want to learn.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="space-y-2">
              <Label>Select dataset</Label>
              {datasets.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  Upload a dataset first to run an analysis.
                </p>
              ) : (
                <div className="space-y-2">
                  {datasets.map((dataset) => (
                    <button
                      key={dataset.id}
                      type="button"
                      onClick={() => setSelectedDatasetId(dataset.id)}
                      className={`w-full rounded-xl px-4 py-3 text-left ${
                        selectedDatasetId === dataset.id ? "glass-selected" : "glass-tile"
                      }`}
                    >
                      <p className="font-medium">{dataset.filename}</p>
                      <p className="text-sm text-muted-foreground">
                        {dataset.row_count} rows · {dataset.column_count} columns
                      </p>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="query">Your question</Label>
              <Textarea
                id="query"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="e.g. Show correlations and create visualizations for key numeric columns"
              />
            </div>

            <div className="space-y-2">
              <Label>Example prompts</Label>
              <div className="flex flex-wrap gap-2">
                {exampleQueries.map((example) => (
                  <button
                    key={example}
                    type="button"
                    onClick={() => setQuery(example)}
                    className="glass-tile rounded-full px-3 py-1.5 text-left text-xs text-muted-foreground hover:text-white"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>

            {selectedDataset ? (
              <div className="glass-tile rounded-xl p-4">
                <p className="mb-2 text-sm font-medium">Dataset preview</p>
                <div className="flex flex-wrap gap-2">
                  {selectedDataset.columns.map((column) => (
                    <Badge key={column} variant="muted">
                      {column}
                    </Badge>
                  ))}
                </div>
              </div>
            ) : null}

            {error ? (
              <p className="rounded-lg border border-rose-400/30 bg-rose-400/10 px-3 py-2 text-sm text-rose-200">
                {error}
              </p>
            ) : null}

            <Button
              className="w-full"
              disabled={loading || !selectedDatasetId || !query.trim()}
              onClick={() => void handleAnalyze()}
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Running agents...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Run analysis
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        <div className="space-y-6">
          {loading ? (
            <Card>
              <CardContent className="flex min-h-[320px] flex-col items-center justify-center gap-4 p-10 text-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <BrainCircuit className="h-8 w-8 animate-pulse" />
                </div>
                <div>
                  <p className="text-lg font-medium">AI agents are working</p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Planning, preprocessing, analyzing, and generating visualizations...
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : result ? (
            <AnalysisResult analysis={result} />
          ) : (
            <Card>
              <CardContent className="flex min-h-[320px] flex-col items-center justify-center gap-3 p-10 text-center">
                <Sparkles className="h-10 w-10 text-primary" />
                <p className="text-lg font-medium">Your analysis will appear here</p>
                <p className="max-w-md text-sm text-muted-foreground">
                  Select a dataset, describe your goal, and Prysm will generate a
                  complete Python analysis pipeline.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
