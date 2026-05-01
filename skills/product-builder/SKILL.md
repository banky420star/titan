# product-builder

Scaffold and manage local products using Titan's 6 templates.

## When to use

When the user wants to create, start, stop, or inspect a product.

## Available templates

1. **python_cli** — Standalone Python script with `main()` entry point
2. **flask_app** — Flask web app on port 5055 with `/` and `/health` routes
3. **static_website** — HTML + CSS static site
4. **api_service** — Flask REST API with JSON endpoints
5. **flask_dashboard** — Full dashboard with sidebar nav and dark theme
6. **landing_page** — Modern landing page with hero, features, CTA

## Workflow

1. Use `create_product` with name, kind (template name), and description.
2. Product files are created in `products/<slug-name>/`.
3. Use `start_product` to launch (runs in background, tracked in `jobs/`).
4. Use `stop_product` to kill the process.
5. Use `product_logs` to see stdout/stderr.
6. Use `list_products` to see all created products.
7. Use `list_product_templates` to show available kinds.

## Customization

After scaffolding, edit files in `products/<name>/` directly. The product is just a directory — no build step needed.

## Dependencies

- flask (for flask_app, api_service, flask_dashboard templates)

## Notes

Product names are slugified (lowercase, dashes). Port 5055 is default for Flask products. Each product runs as a subprocess.