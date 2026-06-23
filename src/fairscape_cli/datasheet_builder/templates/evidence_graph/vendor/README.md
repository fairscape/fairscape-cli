# Vendored JS libraries for the evidence graph visualization

These files are inlined into the generated evidence-graph HTML so the output is
a fully self-contained, offline-shareable single file (no CDN dependency).

| File | Package | Version | Source | License |
|------|---------|---------|--------|---------|
| `react.production.min.js` | react | 18.3.1 | https://unpkg.com/react@18.3.1/umd/react.production.min.js | MIT |
| `react-dom.production.min.js` | react-dom | 18.3.1 | https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js | MIT |
| `dagre.min.js` | @dagrejs/dagre | 1.0.2 | https://cdn.jsdelivr.net/npm/@dagrejs/dagre@1.0.2/dist/dagre.min.js | MIT |

To update, download the new UMD build from the URL above (bump the version) and
update this table. License headers are kept in the files themselves.
