import react from "@vitejs/plugin-react";
import {defineConfig} from "vite";

export default defineConfig({
    build: {
        minify: "terser",
        outDir: "../aiohttp_admin/static/",
        rollupOptions: {
            input: "src/admin.jsx",
            output: {
                entryFileNames: "[name].js"
            }
        },
        sourcemap: true,
    },
    plugins: [react()],
    test: {
        clearMocks: true,
        coverage: {
            exclude: [],
        },
        environment: "jsdom",
        environmentOptions: {
            url: "http://localhost:8080",
            pretendToBeVisual: true,
            testURL: "http://localhost:8080"
        },
        expect: {
            requireAssertions: true
        },
        fileParallelism: false,
        mockReset: true,
        restoreMocks: true,
        setupFiles: "tests/setupTests.jsx",
    }
})
