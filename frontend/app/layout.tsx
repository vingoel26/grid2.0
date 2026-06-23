import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Gridlock 2.0 — Traffic Violation Detection",
  description: "AI-powered traffic violation detection for Bengaluru",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased font-sans text-slate-900 bg-white">
        {children}
      </body>
    </html>
  );
}
