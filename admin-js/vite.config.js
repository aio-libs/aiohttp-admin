import { defineConfig } from "vite";

export default defineConfig({
    build: {
        outDir: "../aiohttp_admin/static/",
        rollupOptions: {
            input: "src/admin.jsx",
            output: {
                entryFileNames: "[name].js"
            }
        },
        sourcemap: true,
    },
})
