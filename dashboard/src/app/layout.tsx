import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
    title: 'SwarmGrid Dashboard',
    description: 'Risk Early Warning Platform',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="tr">
            <body>{children}</body>
        </html>
    );
}
