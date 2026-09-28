import './globals.css';
import { ReactNode } from 'react';
import { AppProviders } from './providers';

export const metadata = {
  title: 'Foresight | AI Deploy-Safety Agent',
  description: 'Hindsight remembers. Foresight prevents. Deploy safety agent for payments and fintech engineering teams.',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0B0D12] text-[#E6E8EE] antialiased selection:bg-[#7C5CFF]/30 selection:text-[#E6E8EE]">
        <AppProviders>
          {children}
        </AppProviders>
      </body>
    </html>
  );
}
