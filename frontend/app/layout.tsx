import type { Metadata } from "next";
import { IBM_Plex_Mono, Inter } from "next/font/google";
import { ReactQueryProvider } from "@/lib/queryClient";
import "./globals.css";

const ibmPlexMono = IBM_Plex_Mono({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  variable: "--font-ibm-plex-mono",
});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "HoneyNet | Forensics Lab SOC Threat Intelligence",
  description: "Evidence-based cyber deception platform with real-time intent classification, lateral movement graphing, and autonomous canary infrastructure.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${ibmPlexMono.variable} ${inter.variable} dark h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-[#0B0D10] text-[#E8EAED] selection:bg-[#4A9EFF] selection:text-black">
        <ReactQueryProvider>{children}</ReactQueryProvider>
      </body>
    </html>
  );
}
