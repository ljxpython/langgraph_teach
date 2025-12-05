// @ts-expect-error  MC8yOmFIVnBZMlhtblk3a3ZiUG1yS002UVU1cmVnPT06MjYyNjQyZjg=

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

export { Skeleton };
// NOTE  MS8yOmFIVnBZMlhtblk3a3ZiUG1yS002UVU1cmVnPT06MjYyNjQyZjg=
