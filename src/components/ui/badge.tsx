import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.3em]',
  {
    variants: {
      variant: {
        default: 'border-white/10 bg-white/5 text-gray-300',
        glow: 'border-accent/40 bg-accent/20 text-accent-soft',
        success: 'border-emerald-400/40 bg-emerald-500/15 text-emerald-200',
        danger: 'border-rose-500/40 bg-rose-500/20 text-rose-200'
      }
    },
    defaultVariants: {
      variant: 'default'
    }
  }
);

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(({ className, variant, ...props }, ref) => (
  <div ref={ref} className={cn(badgeVariants({ variant, className }))} {...props} />
));

Badge.displayName = 'Badge';

export { Badge, badgeVariants };
