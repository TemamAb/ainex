import './globals.css'

export const metadata = {
  title: 'AINEX Dashboard',
  description: 'AI Dashboard',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
