(function () {
  "use strict";

  const state = {
    session: null,
    initialization: null,
    manifest: null,
    modelUrl: null,
    executionProvider: null,
  };

  function validateManifest(manifest) {
    const expected = ["low", "medium", "high", "non_flood"];
    if (
      manifest.input_size !== 224 ||
      JSON.stringify(manifest.class_order) !== JSON.stringify(expected) ||
      !Array.isArray(manifest.mean) ||
      !Array.isArray(manifest.std) ||
      !Array.isArray(manifest.letterbox_fill)
    ) {
      throw new Error("Model manifest does not match the browser runtime contract.");
    }
  }

  async function createSession(modelUrl, provider) {
    return ort.InferenceSession.create(modelUrl, {
      executionProviders: [provider],
      graphOptimizationLevel: "all",
    });
  }

  async function initialize(modelUrl, manifestUrl) {
    if (state.session) {
      return { executionProvider: state.executionProvider };
    }
    if (state.initialization) return state.initialization;

    state.initialization = (async function () {
      if (typeof ort === "undefined") {
        throw new Error("ONNX Runtime Web was not loaded.");
      }
      ort.env.wasm.wasmPaths = new URL("vendor/ort/", window.location.href).href;
      ort.env.wasm.numThreads = 1;

      const response = await fetch(manifestUrl, { cache: "force-cache" });
      if (!response.ok) throw new Error(`Cannot load model manifest (${response.status}).`);
      state.manifest = await response.json();
      validateManifest(state.manifest);
      state.modelUrl = modelUrl;

      try {
        state.session = await createSession(modelUrl, "webgpu");
        state.executionProvider = "webgpu";
      } catch (webGpuError) {
        console.info("WebGPU unavailable; ONNX Runtime is using WebAssembly.", webGpuError);
        state.session = await createSession(modelUrl, "wasm");
        state.executionProvider = "wasm";
      }
      return { executionProvider: state.executionProvider };
    })();

    try {
      return await state.initialization;
    } catch (error) {
      state.initialization = null;
      throw error;
    }
  }

  async function imageTensor(imageBytes) {
    const blob = new Blob([imageBytes]);
    const bitmap = await createImageBitmap(blob);
    try {
      const size = state.manifest.input_size;
      const canvas = new OffscreenCanvas(size, size);
      const context = canvas.getContext("2d", { willReadFrequently: true });
      const fill = state.manifest.letterbox_fill;
      context.fillStyle = `rgb(${fill[0]}, ${fill[1]}, ${fill[2]})`;
      context.fillRect(0, 0, size, size);

      const scale = Math.min(size / bitmap.width, size / bitmap.height);
      const width = bitmap.width * scale;
      const height = bitmap.height * scale;
      context.drawImage(bitmap, (size - width) / 2, (size - height) / 2, width, height);

      const rgba = context.getImageData(0, 0, size, size).data;
      const plane = size * size;
      const input = new Float32Array(3 * plane);
      const mean = state.manifest.mean;
      const std = state.manifest.std;
      for (let pixel = 0; pixel < plane; pixel += 1) {
        const source = pixel * 4;
        input[pixel] = (rgba[source] / 255 - mean[0]) / std[0];
        input[plane + pixel] = (rgba[source + 1] / 255 - mean[1]) / std[1];
        input[2 * plane + pixel] = (rgba[source + 2] / 255 - mean[2]) / std[2];
      }
      return new ort.Tensor("float32", input, [1, 3, size, size]);
    } finally {
      bitmap.close();
    }
  }

  async function runWithFallback(feeds) {
    try {
      return await state.session.run(feeds);
    } catch (error) {
      if (state.executionProvider !== "webgpu") throw error;
      console.info("WebGPU inference failed; retrying once with WebAssembly.", error);
      state.session = await createSession(state.modelUrl, "wasm");
      state.executionProvider = "wasm";
      return state.session.run(feeds);
    }
  }

  async function predict(imageBytes) {
    if (!state.session) {
      throw new Error("Call floodAi.initialize before prediction.");
    }
    const tensor = await imageTensor(imageBytes);
    const started = performance.now();
    const outputs = await runWithFallback({ [state.manifest.input_name]: tensor });
    const durationMs = performance.now() - started;
    const output = outputs[state.manifest.output_name];
    if (!output) throw new Error("The ONNX model did not return probabilities.");

    const probabilities = Array.from(output.data, Number);
    let bestIndex = 0;
    for (let index = 1; index < probabilities.length; index += 1) {
      if (probabilities[index] > probabilities[bestIndex]) bestIndex = index;
    }
    return {
      label: state.manifest.class_order[bestIndex],
      confidence: probabilities[bestIndex],
      probabilities,
      durationMs,
      executionProvider: state.executionProvider,
    };
  }

  window.floodAi = Object.freeze({ initialize, predict });
})();
