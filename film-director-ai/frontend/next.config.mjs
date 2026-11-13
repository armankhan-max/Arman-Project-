const dev = process.env.NODE_ENV === "development";
const backend = process.env.BACKEND_URL || "http://localhost:8000";
/** Production: static export served by the FastAPI container (one origin, no proxy). Dev: proxy /api to the backend. */
/** @type {import('next').NextConfig} */
const nextConfig = dev
  ? { reactStrictMode: true, async rewrites() { return [{ source: "/api/:path*", destination: `${backend}/api/:path*` }]; } }
  : { reactStrictMode: true, output: "export", trailingSlash: true, images: { unoptimized: true } };
export default nextConfig;
