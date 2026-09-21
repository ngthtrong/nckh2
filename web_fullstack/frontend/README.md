# Flood Rescue Web

This is the standalone Flutter Web/PWA interface for the flood rescue system. The app:

- runs the ONNX model directly in Chrome with WebGPU and falls back to WASM;
- captures an image and location after the user grants browser permissions;
- stores reports in IndexedDB while offline and syncs automatically when the network returns;
- sends real report data to the FastAPI backend without mocks or no-op adapters;
- exposes the SMS flow only when the backend enables an SMS provider.

Never place API secrets in the frontend. Backend configuration and complete run instructions are in
[`../README.md`](../README.md).
