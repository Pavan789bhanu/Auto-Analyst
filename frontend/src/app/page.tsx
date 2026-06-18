import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  BrainCircuit,
  LineChart,
  Shield,
  Sparkles,
  Upload,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const features = [
  {
    icon: Upload,
    title: "Upload your datasets",
    description:
      "Drop CSV files and let AutoAnalyst understand your columns, types, and structure instantly.",
  },
  {
    icon: BrainCircuit,
    title: "Ask in plain English",
    description:
      "Describe the analysis you need. Our multi-agent AI plans preprocessing, statistics, and charts.",
  },
  {
    icon: LineChart,
    title: "Get production-ready code",
    description:
      "Receive combined Python pipelines with pandas, statsmodels, and Plotly visualizations.",
  },
  {
    icon: Shield,
    title: "Secure by design",
    description:
      "JWT authentication, per-user storage, and isolated datasets keep your data protected.",
  },
];

const steps = [
  "Upload a CSV dataset",
  "Describe your analysis goal",
  "AI agents plan the workflow",
  "Review generated Python code",
];

export default function HomePage() {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-50 border-b border-border/70 bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link href="/" className="flex items-center gap-2 font-semibold text-primary">
            <BarChart3 className="h-6 w-6" />
            <span>AutoAnalyst</span>
          </Link>
          <nav className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost">Sign in</Button>
            </Link>
            <Link href="/register">
              <Button>Get started</Button>
            </Link>
          </nav>
        </div>
      </header>

      <main>
        <section className="relative overflow-hidden border-b border-border">
          <div className="absolute inset-0 grid-pattern opacity-40" />
          <div className="relative mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 lg:py-28">
            <div className="mx-auto max-w-3xl text-center">
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-1.5 text-sm text-muted-foreground">
                <Sparkles className="h-4 w-4 text-accent" />
                AI-powered automated data analysis
              </div>
              <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
                Turn datasets into insights with{" "}
                <span className="text-primary">intelligent agents</span>
              </h1>
              <p className="mt-6 text-lg leading-8 text-muted-foreground">
                AutoAnalyst orchestrates specialized AI agents to plan, preprocess,
                analyze, and visualize your data. Upload a CSV, ask a question, and
                get a complete Python analysis pipeline in seconds.
              </p>
              <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
                <Link href="/register">
                  <Button size="lg" className="min-w-[180px]">
                    Start analyzing
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
                <Link href="/login">
                  <Button size="lg" variant="outline" className="min-w-[180px]">
                    Sign in to dashboard
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold tracking-tight">How it works</h2>
            <p className="mt-3 text-muted-foreground">
              A professional workflow from upload to analysis output
            </p>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {steps.map((step, index) => (
              <Card key={step} className="glass-panel">
                <CardHeader>
                  <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground">
                    {index + 1}
                  </div>
                  <CardTitle className="text-base">{step}</CardTitle>
                </CardHeader>
              </Card>
            ))}
          </div>
        </section>

        <section className="border-y border-border bg-card/50 py-20">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mb-12 text-center">
              <h2 className="text-3xl font-bold tracking-tight">
                Built for data teams
              </h2>
              <p className="mt-3 text-muted-foreground">
                Everything you need for AI-assisted analytics in one dashboard
              </p>
            </div>
            <div className="grid gap-6 md:grid-cols-2">
              {features.map((feature) => (
                <Card key={feature.title} className="transition-shadow duration-200 hover:shadow-md">
                  <CardHeader>
                    <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
                      <feature.icon className="h-5 w-5" />
                    </div>
                    <CardTitle>{feature.title}</CardTitle>
                    <CardDescription>{feature.description}</CardDescription>
                  </CardHeader>
                </Card>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-4 py-20 text-center sm:px-6 lg:px-8">
          <Card className="border-primary/20 bg-gradient-to-br from-primary/5 to-accent/5">
            <CardContent className="flex flex-col items-center gap-6 p-10">
              <h2 className="text-3xl font-bold tracking-tight">
                Ready to analyze your data?
              </h2>
              <p className="max-w-2xl text-muted-foreground">
                Create a free account and start uploading datasets. Your AI analyst
                team is ready when you are.
              </p>
              <Link href="/register">
                <Button size="lg">
                  Create your account
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </CardContent>
          </Card>
        </section>
      </main>

      <footer className="border-t border-border py-8">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 text-sm text-muted-foreground sm:flex-row sm:px-6 lg:px-8">
          <div className="flex items-center gap-2 font-medium text-foreground">
            <BarChart3 className="h-4 w-4 text-primary" />
            AutoAnalyst
          </div>
          <p>AI-powered automated data analysis platform</p>
        </div>
      </footer>
    </div>
  );
}
