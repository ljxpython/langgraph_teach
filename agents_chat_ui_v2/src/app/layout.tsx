// TODO  MC8yOmFIVnBZMlhtblk3a3ZiUG1yS002Um0xUGVBPT06OTQ1M2I5MjI=

import { Inter } from "next/font/google";
import { NuqsAdapter } from "nuqs/adapters/next/app";
import { Toaster } from "sonner";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

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
// eslint-disable  MS8yOmFIVnBZMlhtblk3a3ZiUG1yS002Um0xUGVBPT06OTQ1M2I5MjI=
