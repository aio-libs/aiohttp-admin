import { defineConfig } from "vite";

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
    test: {
        coverage: {
            exclude: [],
        },
        environment: "jsdom",
        environmentOptions: {"url": "http://localhost:8080", "pretendToBeVisual": true},
        //maxWorkers: 1,
        setupFiles: ["tests/setupTests.js"],
    }
})
