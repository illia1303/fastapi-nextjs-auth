import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin", "cyrillic"] });

export const metadata: Metadata = {
  title: "Auth & Products App",
  description: "Учебный проект для авторизации и управления продуктами",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru" className="scheme-light-dark">
      <body
        className={`${inter.className} min-h-screen bg-white text-neutral-900 dark:bg-neutral-950 dark:text-[#ededed]`}
      >
        {children}
      </body>
    </html>
  );
}