/** @type {import('next').NextConfig} */
const nextConfig = {
  output: process.env.NEXT_OUTPUT || 'standalone',
  reactStrictMode: true,
  async rewrites() {
    if (process.env.NEXT_OUTPUT === 'export') {
      return [];
    }
    const target = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';
    return [
      {
        source: '/health',
        destination: `${target}/health`,
      },
      {
        source: '/api/:path*',
        destination: `${target}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
