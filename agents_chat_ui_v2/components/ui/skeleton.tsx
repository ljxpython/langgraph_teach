// eslint-disable  MC8yOmFIVnBZMlhtblk3a3ZiUG1yS002WVhwR1FnPT06MzAzZmUwMDQ=

import { cn } from "@/lib/utils";

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-muted", className)}
      {...props}
    />
  );
}
// NOTE  MS8yOmFIVnBZMlhtblk3a3ZiUG1yS002WVhwR1FnPT06MzAzZmUwMDQ=

export { Skeleton };
