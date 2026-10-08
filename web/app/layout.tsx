import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin", "cyrillic"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "CNTRL.GAMES — Цифровой баланс и развитие вашего ребёнка",
  description:
    "Интеллектуальная система мониторинга цифровой активности для осознанных родителей. Помогает следить за экранным временем ребёнка, оценивать качество занятий и вовремя находить баланс.",
  keywords: [
    "родительский контроль",
    "экранное время",
    "мониторинг игр",
    "цифровая гигиена",
    "CNTRL.GAMES",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" className={inter.variable}>
      <body className="antialiased">{children}</body>
    </html>
  );
}