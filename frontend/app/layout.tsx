export const metadata = {
  title: 'LegoCV',
  description: 'Capture a photo and analyze your LEGO lookalike',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body style={{ margin: 0 }}>{children}</body>
    </html>
  )
}
