/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  // Critical for Node.js 16 compatibility
  experimental: {
    serverComponentsExternalPackages: [],
  },
}

module.exports = nextConfig
