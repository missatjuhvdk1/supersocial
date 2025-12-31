import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

export interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'error' | 'success' | 'warning';
}

const Alert = forwardRef<HTMLDivElement, AlertProps>(
  ({ className, variant = 'default', children, ...props }, ref) => {
    const variants = {
      default: 'bg-surface border-border text-gray-300',
      error: 'bg-red-950/30 border-error text-red-200',
      success: 'bg-green-950/30 border-success text-green-200',
      warning: 'bg-yellow-950/30 border-warning text-yellow-200',
    };

    return (
      <div
        ref={ref}
        className={cn(
          'rounded-lg border px-4 py-3 text-sm',
          variants[variant],
          className
        )}
        role="alert"
        {...props}
      >
        {children}
      </div>
    );
  }
);

Alert.displayName = 'Alert';

export default Alert;
