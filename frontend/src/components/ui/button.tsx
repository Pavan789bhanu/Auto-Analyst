import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-transparent disabled:pointer-events-none disabled:opacity-50 cursor-pointer",
  {
    variants: {
      variant: {
        default:
          "bg-sunset text-white shadow-[0_8px_24px_rgba(236,72,153,0.35)] hover:brightness-110 hover:shadow-[0_10px_30px_rgba(236,72,153,0.5)] active:scale-[0.98]",
        secondary:
          "bg-white/10 text-foreground border border-white/15 backdrop-blur-md hover:bg-white/15 active:scale-[0.98]",
        accent:
          "bg-accent text-accent-foreground shadow-sm hover:brightness-110 active:scale-[0.98]",
        outline:
          "border border-white/20 bg-white/5 text-foreground backdrop-blur-md hover:bg-white/10 hover:border-white/30 active:scale-[0.98]",
        ghost: "text-foreground hover:bg-white/10",
        destructive:
          "bg-destructive text-white hover:brightness-110 active:scale-[0.98]",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-lg px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
