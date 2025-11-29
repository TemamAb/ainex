import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],

    resolve: {
        alias: {
            '@': path.resolve(__dirname, './app'),
            '@services': path.resolve(__dirname, './services'),
            '@utils': path.resolve(__dirname, './utils'),
        }
    },

    // Environment variable handling
    define: {
        // Make process.env available for compatibility
        'process.env': {}
    },

    // Development server configuration
    server: {
        port: 3000,
        host: true,
        open: false,
    },

    // Build configuration
    build: {
        outDir: 'dist',
        sourcemap: true,
        // Optimize chunks
        rollupOptions: {
            output: {
                manualChunks: {
                    'react-vendor': ['react', 'react-dom'],
                    'web3-vendor': ['ethers'],
                    'charts-vendor': ['recharts'],
                }
            }
        }
    },

    // Preview server (for testing production build)
    preview: {
        port: 3000,
        host: true,
        allowedHosts: ['ainex-0zp.onrender.com', 'onrender.com'],
    }
});
