/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ]
  },
  reactStrictMode: true,
  poweredByHeader: false,
  compress: true,
  images: {
    domains: ['localhost'],
  },
}

module.exports = nextConfig
