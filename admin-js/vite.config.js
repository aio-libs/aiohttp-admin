import { defineConfig } from "vite";

export default defineConfig({
    server: {
        cors: {
            // the origin you will be accessing via browser
            origin: "http://localhost",
        },
    },
    build: {
        outDir: "../aiohttp_admin/static/",
        rollupOptions: {
            input: "src/index.jsx",
            output: {
                file: "admin.js"
            }
        },
        sourcemap: true,
    },
})
