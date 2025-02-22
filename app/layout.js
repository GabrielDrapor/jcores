import './globals.css';

export const metadata = {
  title: 'JCores',
  description: 'Your personal podcast library',
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
