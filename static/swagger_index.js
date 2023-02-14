window.onload = () => {
    window.ui = SwaggerUIBundle({
        urls: [
            { url: "openapi.yaml", name: "EduLint API" },
        ],
        dom_id: '#swagger-ui',

        deepLinking: true,
        presets: [
            SwaggerUIBundle.presets.apis,
            SwaggerUIStandalonePreset
        ],
        plugins: [
            SwaggerUIBundle.plugins.DownloadUrl
        ],
        layout: "StandaloneLayout",
    });
};