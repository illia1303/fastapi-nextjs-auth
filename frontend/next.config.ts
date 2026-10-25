import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Минимальная сборка с server.js — используется в Docker-образе
  output: "standalone",
};

export default nextConfig;
