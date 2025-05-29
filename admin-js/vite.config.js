export default defineConfig({
    server: {
        cors: {
            // the origin you will be accessing via browser
            origin: "http://localhost",
        },
    },
    build: {
        manifest: true,
        rollupOptions: {
            input: "src/index.js",
        },
    },
})
