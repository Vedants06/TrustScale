import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Toaster } from "sonner";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "TrustScale Live Dashboard",
  description: "Byzantine-aware distributed load balancer",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} min-h-screen bg-background`}>
        {children}
        <Toaster
          theme="dark"
          position="bottom-right"
          richColors
          closeButton
        />
      </body>
    </html>
  );
}