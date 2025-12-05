// NOTE  MC8yOmFIVnBZMlhtblk3a3ZiUG1yS002YWs1a2J3PT06NmNkNTNhNjM=

import { Inter } from "next/font/google";
import { NuqsAdapter } from "nuqs/adapters/next/app";
import { Toaster } from "sonner";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });
// eslint-disable  MS8yOmFIVnBZMlhtblk3a3ZiUG1yS002YWs1a2J3PT06NmNkNTNhNjM=

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="zh-CN"
      suppressHydrationWarning
    >
      <body
        className={inter.className}
        suppressHydrationWarning
      >
        <NuqsAdapter>{children}</NuqsAdapter>
        <Toaster />
      </body>
    </html>
  );
}
