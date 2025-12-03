/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    // This allows the build to finish even if there are type errors
    ignoreBuildErrors: true,
  },
  eslint: {
    // This allows the build to finish even if there are linting errors
    ignoreDuringBuilds: true,
  }
};

module.exports = nextConfig;