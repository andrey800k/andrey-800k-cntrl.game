import "./globals.css";

export const metadata = {
  title: "Game Time Tracker",
  description: "Отслеживание игрового времени",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}