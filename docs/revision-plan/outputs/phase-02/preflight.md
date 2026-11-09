# P04/P05 preflight

Exact seed1024 pruning assets ONNX/PTE hiện có trong app/assets/models; compression-audit.csv nối theo SHA256, không filename. Test256 cùng IDs. visual-env: NumPy2.5.3/Pillow12, không onnxruntime/torch/executorch; adb không có. Chưa có attached-device receipt hoặc APK hash; không giả định device online. P04 cần runner/clean parity và runtime/device trước inference. P05 cần raw E2E recovery trước rerun, không dùng DB chung. Không coi missing Python runtime là model absent.
