import './globals.css';

export const metadata = {
  title: 'Gadio Dig',
  description: 'Discover and filter Gcores podcast episodes',
  icons: {
    icon: '/gboy.ico',
  },
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="bg-gray-50">{children}</body>
    </html>
  )
}
