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
    test: {
        clearMocks: true,
        coverage: {
            exclude: [],
        },
        environment: "jsdom",
        environmentOptions: {"url": "http://localhost:8080", "pretendToBeVisual": true},
        expect: {
            requireAssertions: true
        },
        //maxWorkers: 1,
        mockReset: true,
        restoreMocks: true,
        setupFiles: "tests/setupTests.jsx",
    }
})
