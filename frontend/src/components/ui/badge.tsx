import { cn } from "@/lib/utils";

export function Badge({
  className,
  variant = "default",
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & {
  variant?: "default" | "success" | "warning" | "destructive" | "muted";
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium backdrop-blur-md",
        variant === "default" && "border-primary/30 bg-primary/15 text-fuchsia-200",
        variant === "success" && "border-emerald-400/30 bg-emerald-400/15 text-emerald-200",
        variant === "warning" && "border-amber-400/30 bg-amber-400/15 text-amber-200",
        variant === "destructive" && "border-rose-400/30 bg-rose-400/15 text-rose-200",
        variant === "muted" && "border-white/15 bg-white/8 text-muted-foreground",
        className,
      )}
      {...props}
    />
  );
}
