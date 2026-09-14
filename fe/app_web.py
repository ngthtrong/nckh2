"""Web App kiểm thử Mô hình PyTorch (.pth), ONNX (.onnx) và ExecuTorch (.pte)
So sánh song song kết quả dự đoán giữa mô hình PyTorch gốc (.pth), mô hình ONNX (.onnx) và mô hình ExecuTorch (.pte).

Chạy ứng dụng:
    .venv\\Scripts\\python.exe app_web.py
Truy cập:
    http://localhost:5000
"""

import io
import json
import time
from pathlib import Path

import torch
from torch import nn
from torchvision import models, transforms
import onnxruntime as ort
import numpy as np
from PIL import Image
from flask import Flask, request, jsonify, render_template_string

# Cấu hình đường dẫn
ROOT = Path(__file__).resolve().parent
CHECKPOINT_PTH = (
    ROOT
    / "model"
    / "models"
    / "mobilenetv3_large_relabel"
    / "flood_mobilenetv3_large_relabel_best.pth"
)
if not CHECKPOINT_PTH.exists():
    CHECKPOINT_PTH = ROOT / "app" / "model.pth"

CHECKPOINT_ONNX = ROOT / "app" / "assets" / "models" / "model.onnx"
CHECKPOINT_PTE = ROOT / "model" / "Edge Ai" / "flood_mobilenetv3_large.pte"

DEFAULT_CONFIG = (
    ROOT / "model" / "models" / "mobilenetv3_large_relabel" / "config_mobilenetv3_large.json"
)

# 1. Khởi tạo PyTorch
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

if DEFAULT_CONFIG.exists():
    config = json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    class_order = config.get("class_order", ["low", "medium", "high", "non_flood"])
    dropout = float(config.get("dropout", 0.35))
    image_size = int(config.get("image_size", 224))
else:
    class_order = ["low", "medium", "high", "non_flood"]
    dropout = 0.35
    image_size = 224


def build_model(num_classes: int, dropout: float) -> nn.Module:
    model = models.mobilenet_v3_large(weights=None)
    classifier = list(model.classifier.children())[:-1]
    in_features = model.classifier[-1].in_features
    model.classifier = nn.Sequential(
        *classifier,
        nn.Sequential(
            nn.Dropout(p=dropout),
            nn.Linear(in_features, num_classes),
        ),
    )
    return model


# Nạp PyTorch (.pth)
model_pt = build_model(len(class_order), dropout)
pth_loaded = False
if CHECKPOINT_PTH.exists():
    try:
        checkpoint = torch.load(CHECKPOINT_PTH, map_location="cpu", weights_only=False)
        state_dict = checkpoint
        if isinstance(checkpoint, dict):
            for k in ("model_state_dict", "state_dict", "model"):
                if k in checkpoint and isinstance(checkpoint[k], dict):
                    state_dict = checkpoint[k]
                    break
        state_dict = {k.removeprefix("module."): v for k, v in state_dict.items()}
        model_pt.load_state_dict(state_dict, strict=False)
        model_pt.to(device)
        model_pt.eval()
        pth_loaded = True
        print(f"✓ PyTorch (.pth) model loaded: {CHECKPOINT_PTH.name}")
    except Exception as e:
        print(f"✗ Error loading .pth model: {e}")

# Nạp ONNX (.onnx)
onnx_session = None
onnx_loaded = False
if CHECKPOINT_ONNX.exists():
    try:
        onnx_session = ort.InferenceSession(str(CHECKPOINT_ONNX))
        onnx_loaded = True
        print(f"✓ ONNX (.onnx) model loaded: {CHECKPOINT_ONNX.name}")
    except Exception as e:
        print(f"✗ Error loading .onnx model: {e}")

# Nạp ExecuTorch (.pte)
pte_module = None
pte_loaded = False
if CHECKPOINT_PTE.exists():
    try:
        from executorch.extension.pybindings.portable_lib import _load_for_executorch

        pte_module = _load_for_executorch(str(CHECKPOINT_PTE))
        pte_loaded = True
        print(f"✓ ExecuTorch (.pte) model loaded: {CHECKPOINT_PTE.name}")
    except Exception as e:
        print(f"✗ Error loading .pte model: {e}")

# Transform ảnh
transform = transforms.Compose([
    transforms.Resize((image_size, image_size)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

LABEL_TRANSLATIONS = {
    "low": "Ngập nhẹ (Low)",
    "medium": "Ngập trung bình (Medium)",
    "high": "Ngập sâu nguy hiểm (High)",
    "non_flood": "Không ngập nước (Safe)",
}

LABEL_COLORS = {
    "low": "bg-yellow-100 text-yellow-800 border-yellow-300",
    "medium": "bg-orange-100 text-orange-800 border-orange-300",
    "high": "bg-red-100 text-red-800 border-red-300",
    "non_flood": "bg-green-100 text-green-800 border-green-300",
}

# 2. Flask Web App
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>So Sánh Mô Hình AI: PyTorch (.pth) vs ONNX (.onnx) vs ExecuTorch (.pte)</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Work+Sans:wght@600;700;800;900&family=Nunito:wght@500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Nunito', sans-serif; background-color: #f7f7f7; }
        .font-heading { font-family: 'Work Sans', sans-serif; }
    </style>
</head>
<body class="min-h-screen pb-12">
    <!-- Header -->
    <header class="bg-[#C62828] text-white py-6 px-6 shadow-md mb-8">
        <div class="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
                <p class="text-white/70 text-xs font-bold uppercase tracking-widest">NCKH - Cứu Hộ Lũ Lụt</p>
                <h1 class="text-2xl sm:text-3xl font-heading font-black">So Sánh Mô Hình: .pth vs .onnx vs .pte</h1>
            </div>
            <div class="flex flex-wrap items-center gap-2">
                <span class="px-3 py-1.5 rounded-xl bg-white/20 text-xs font-extrabold flex items-center gap-1.5">
                    <span class="w-2.5 h-2.5 rounded-full {{ 'bg-green-400' if pth_loaded else 'bg-red-400' }}"></span>
                    PyTorch (.pth): {{ 'Ready' if pth_loaded else 'Missing' }}
                </span>
                <span class="px-3 py-1.5 rounded-xl bg-white/20 text-xs font-extrabold flex items-center gap-1.5">
                    <span class="w-2.5 h-2.5 rounded-full {{ 'bg-green-400' if onnx_loaded else 'bg-red-400' }}"></span>
                    ONNX (.onnx): {{ 'Ready' if onnx_loaded else 'Missing' }}
                </span>
                <span class="px-3 py-1.5 rounded-xl bg-white/20 text-xs font-extrabold flex items-center gap-1.5">
                    <span class="w-2.5 h-2.5 rounded-full {{ 'bg-green-400' if pte_loaded else 'bg-red-400' }}"></span>
                    ExecuTorch (.pte): {{ 'Ready' if pte_loaded else 'Missing' }}
                </span>
            </div>
        </div>
    </header>

    <!-- Main Container: 4 Columns -->
    <main class="max-w-7xl mx-auto px-4 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <!-- Panel 1: Upload Zone -->
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col justify-between">
            <div>
                <h2 class="text-gray-800 font-heading font-extrabold text-lg mb-4 flex items-center gap-2">
                    <svg class="w-5 h-5 text-[#C62828]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                    Tải Ảnh Hiện Trường
                </h2>

                <div id="dropZone" class="border-2 border-dashed border-gray-300 rounded-2xl p-6 text-center hover:border-[#C62828] hover:bg-red-50/30 transition-all cursor-pointer">
                    <input type="file" id="fileInput" accept="image/*" class="hidden">
                    <div id="previewContainer" class="hidden mb-4">
                        <img id="imagePreview" src="" alt="Preview" class="max-h-48 mx-auto rounded-xl object-contain shadow-md">
                    </div>
                    <div id="uploadPrompt">
                        <div class="w-12 h-12 rounded-full bg-red-50 text-[#C62828] flex items-center justify-center mx-auto mb-3">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                            </svg>
                        </div>
                        <p class="text-gray-700 font-bold text-sm">Kéo thả hoặc Bấm chọn ảnh</p>
                        <p class="text-gray-400 text-xs mt-1">.jpg, .png, .jpeg, .webp</p>
                    </div>
                </div>
            </div>

            <button id="btnPredict" disabled class="mt-6 w-full bg-[#C62828] text-white font-heading font-extrabold text-base py-4 rounded-2xl shadow-lg disabled:opacity-40 hover:bg-[#8E0000] active:scale-[0.98] transition-all flex items-center justify-center gap-2">
                <span id="btnText">Chạy So Sánh 3 Mô Hình</span>
                <div id="btnSpinner" class="hidden w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            </button>
        </div>

        <!-- Panel 2: Result PyTorch (.pth) -->
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col justify-between">
            <div>
                <h2 class="text-gray-800 font-heading font-extrabold text-base mb-4 flex items-center justify-between">
                    <span class="flex items-center gap-2">🔥 PyTorch Gốc (.pth)</span>
                    <span id="pthTime" class="text-xs font-bold text-gray-400"></span>
                </h2>

                <div id="pthEmpty" class="py-12 text-center text-gray-400 text-sm font-bold">Chưa có kết quả</div>

                <div id="pthContent" class="hidden space-y-4">
                    <div id="pthBestCard" class="p-3.5 rounded-2xl border flex items-center justify-between">
                        <div>
                            <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Dự đoán</p>
                            <p id="pthBestLabel" class="font-heading font-black text-base"></p>
                        </div>
                        <span id="pthBestConf" class="text-xl font-black font-heading text-gray-800"></span>
                    </div>

                    <div class="bg-gray-50 p-3 rounded-2xl border border-gray-100 space-y-2">
                        <p class="text-[11px] font-bold uppercase tracking-wider text-gray-500">Xác suất các lớp</p>
                        <div id="pthBars" class="space-y-2"></div>
                    </div>
                </div>
            </div>

            <div class="text-[11px] text-gray-400 bg-gray-50 p-2.5 rounded-xl border border-gray-100">
                <strong>Source:</strong> PyTorch Native Checkpoint
            </div>
        </div>

        <!-- Panel 3: Result ONNX (.onnx) -->
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col justify-between">
            <div>
                <h2 class="text-gray-800 font-heading font-extrabold text-base mb-4 flex items-center justify-between">
                    <span class="flex items-center gap-2">⚡ ONNX (.onnx)</span>
                    <span id="onnxTime" class="text-xs font-bold text-gray-400"></span>
                </h2>

                <div id="onnxEmpty" class="py-12 text-center text-gray-400 text-sm font-bold">Chưa có kết quả</div>

                <div id="onnxContent" class="hidden space-y-4">
                    <div id="onnxBestCard" class="p-3.5 rounded-2xl border flex items-center justify-between">
                        <div>
                            <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Dự đoán</p>
                            <p id="onnxBestLabel" class="font-heading font-black text-base"></p>
                        </div>
                        <span id="onnxBestConf" class="text-xl font-black font-heading text-gray-800"></span>
                    </div>

                    <div class="bg-gray-50 p-3 rounded-2xl border border-gray-100 space-y-2">
                        <p class="text-[11px] font-bold uppercase tracking-wider text-gray-500">Xác suất các lớp</p>
                        <div id="onnxBars" class="space-y-2"></div>
                    </div>
                </div>
            </div>

            <div class="text-[11px] text-gray-400 bg-gray-50 p-2.5 rounded-xl border border-gray-100">
                <strong>Source:</strong> ONNX Runtime Exported Model
            </div>
        </div>

        <!-- Panel 4: Result ExecuTorch (.pte) -->
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col justify-between">
            <div>
                <h2 class="text-gray-800 font-heading font-extrabold text-base mb-4 flex items-center justify-between">
                    <span class="flex items-center gap-2">📱 ExecuTorch (.pte)</span>
                    <span id="pteTime" class="text-xs font-bold text-gray-400"></span>
                </h2>

                <div id="pteEmpty" class="py-12 text-center text-gray-400 text-sm font-bold">Chưa có kết quả</div>

                <div id="pteContent" class="hidden space-y-4">
                    <div id="pteBestCard" class="p-3.5 rounded-2xl border flex items-center justify-between">
                        <div>
                            <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Dự đoán</p>
                            <p id="pteBestLabel" class="font-heading font-black text-base"></p>
                        </div>
                        <span id="pteBestConf" class="text-xl font-black font-heading text-gray-800"></span>
                    </div>

                    <div class="bg-gray-50 p-3 rounded-2xl border border-gray-100 space-y-2">
                        <p class="text-[11px] font-bold uppercase tracking-wider text-gray-500">Xác suất các lớp</p>
                        <div id="pteBars" class="space-y-2"></div>
                    </div>
                </div>
            </div>

            <div class="text-[11px] text-gray-400 bg-gray-50 p-2.5 rounded-xl border border-gray-100">
                <strong>Source:</strong> ExecuTorch Mobile Runtime (.pte)
            </div>
        </div>
    </main>

    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const imagePreview = document.getElementById('imagePreview');
        const previewContainer = document.getElementById('previewContainer');
        const uploadPrompt = document.getElementById('uploadPrompt');
        const btnPredict = document.getElementById('btnPredict');
        const btnText = document.getElementById('btnText');
        const btnSpinner = document.getElementById('btnSpinner');

        let selectedFile = null;

        dropZone.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) handleFile(e.target.files[0]);
        });

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('border-[#C62828]', 'bg-red-50/30');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('border-[#C62828]', 'bg-red-50/30');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('border-[#C62828]', 'bg-red-50/30');
            if (e.dataTransfer.files.length > 0) handleFile(e.dataTransfer.files[0]);
        });

        function handleFile(file) {
            if (!file.type.startsWith('image/')) return;
            selectedFile = file;
            const reader = new FileReader();
            reader.onload = (ev) => {
                imagePreview.src = ev.target.result;
                previewContainer.classList.remove('hidden');
                uploadPrompt.classList.add('hidden');
                btnPredict.disabled = false;
            };
            reader.readAsDataURL(file);
        }

        btnPredict.addEventListener('click', async () => {
            if (!selectedFile) return;

            btnPredict.disabled = true;
            btnText.textContent = 'Đang tính toán so sánh...';
            btnSpinner.classList.remove('hidden');

            const formData = new FormData();
            formData.append('file', selectedFile);

            try {
                const res = await fetch('/predict', {
                    method: 'POST',
                    body: formData,
                });
                const data = await res.json();

                if (data.error) {
                    alert('Lỗi: ' + data.error);
                    return;
                }

                // Render PyTorch
                if (data.pytorch) {
                    document.getElementById('pthEmpty').classList.add('hidden');
                    document.getElementById('pthContent').classList.remove('hidden');
                    document.getElementById('pthTime').textContent = data.pytorch.duration_ms + ' ms';
                    document.getElementById('pthBestLabel').textContent = data.pytorch.label_vi;
                    document.getElementById('pthBestConf').textContent = (data.pytorch.confidence * 100).toFixed(1) + '%';
                    document.getElementById('pthBestCard').className = 'p-3.5 rounded-2xl border flex items-center justify-between ' + data.pytorch.color_class;

                    renderBars('pthBars', data.pytorch.probabilities, data.translations);
                }

                // Render ONNX
                if (data.onnx) {
                    document.getElementById('onnxEmpty').classList.add('hidden');
                    document.getElementById('onnxContent').classList.remove('hidden');
                    document.getElementById('onnxTime').textContent = data.onnx.duration_ms + ' ms';
                    document.getElementById('onnxBestLabel').textContent = data.onnx.label_vi;
                    document.getElementById('onnxBestConf').textContent = (data.onnx.confidence * 100).toFixed(1) + '%';
                    document.getElementById('onnxBestCard').className = 'p-3.5 rounded-2xl border flex items-center justify-between ' + data.onnx.color_class;

                    renderBars('onnxBars', data.onnx.probabilities, data.translations);
                }

                // Render ExecuTorch (.pte)
                if (data.executorch) {
                    document.getElementById('pteEmpty').classList.add('hidden');
                    document.getElementById('pteContent').classList.remove('hidden');
                    document.getElementById('pteTime').textContent = data.executorch.duration_ms + ' ms';
                    document.getElementById('pteBestLabel').textContent = data.executorch.label_vi;
                    document.getElementById('pteBestConf').textContent = (data.executorch.confidence * 100).toFixed(1) + '%';
                    document.getElementById('pteBestCard').className = 'p-3.5 rounded-2xl border flex items-center justify-between ' + data.executorch.color_class;

                    renderBars('pteBars', data.executorch.probabilities, data.translations);
                }

            } catch (err) {
                alert('Lỗi server: ' + err);
            } finally {
                btnPredict.disabled = false;
                btnText.textContent = 'Chạy So Sánh 3 Mô Hình';
                btnSpinner.classList.add('hidden');
            }
        });

        function renderBars(containerId, probs, translations) {
            const container = document.getElementById(containerId);
            container.innerHTML = '';
            for (const [cls, prob] of Object.entries(probs)) {
                const pct = (prob * 100).toFixed(1);
                const viName = translations[cls] || cls;
                container.innerHTML += `
                    <div>
                        <div class="flex justify-between text-[11px] font-bold text-gray-700 mb-0.5">
                            <span>${viName}</span>
                            <span>${pct}%</span>
                        </div>
                        <div class="w-full bg-gray-200 h-2 rounded-full overflow-hidden">
                            <div class="bg-[#C62828] h-2 rounded-full transition-all duration-500" style="width: ${pct}%"></div>
                        </div>
                    </div>
                `;
            }
        }
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(
        HTML_TEMPLATE,
        pth_loaded=pth_loaded,
        onnx_loaded=onnx_loaded,
        pte_loaded=pte_loaded,
    )


@app.route("/predict", methods=["POST"])
def predict():
    if "file" not in request.files:
        return jsonify({"error": "Không tìm thấy file"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Chưa chọn file"}), 400

    try:
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        tensor = transform(image).unsqueeze(0)

        result_pth = None
        result_onnx = None
        result_pte = None

        # 1. Inference PyTorch (.pth)
        if pth_loaded:
            t0 = time.perf_counter()
            with torch.no_grad():
                out_pt = model_pt(tensor.to(device))
                probs_pt = torch.softmax(out_pt, dim=1)[0]
            t1 = time.perf_counter()

            probs_dict_pt = {class_order[i]: float(probs_pt[i].cpu().item()) for i in range(len(class_order))}
            best_idx_pt = int(torch.argmax(probs_pt).item())
            best_cls_pt = class_order[best_idx_pt]

            result_pth = {
                "predicted_class": best_cls_pt,
                "label_vi": LABEL_TRANSLATIONS.get(best_cls_pt, best_cls_pt),
                "confidence": round(float(probs_pt[best_idx_pt].item()), 4),
                "duration_ms": round((t1 - t0) * 1000, 1),
                "probabilities": probs_dict_pt,
                "color_class": LABEL_COLORS.get(best_cls_pt, "bg-gray-100"),
            }

        # 2. Inference ONNX (.onnx)
        if onnx_loaded and onnx_session is not None:
            t0 = time.perf_counter()
            input_name = onnx_session.get_inputs()[0].name
            onnx_out = onnx_session.run(None, {input_name: tensor.numpy()})[0][0]
            t1 = time.perf_counter()

            probs_dict_onnx = {class_order[i]: float(onnx_out[i]) for i in range(len(class_order))}
            best_idx_onnx = int(np.argmax(onnx_out))
            best_cls_onnx = class_order[best_idx_onnx]

            result_onnx = {
                "predicted_class": best_cls_onnx,
                "label_vi": LABEL_TRANSLATIONS.get(best_cls_onnx, best_cls_onnx),
                "confidence": round(float(onnx_out[best_idx_onnx]), 4),
                "duration_ms": round((t1 - t0) * 1000, 1),
                "probabilities": probs_dict_onnx,
                "color_class": LABEL_COLORS.get(best_cls_onnx, "bg-gray-100"),
            }

        # 3. Inference ExecuTorch (.pte)
        if pte_loaded and pte_module is not None:
            t0 = time.perf_counter()
            pte_out = pte_module.forward((tensor.cpu(),))[0].numpy()[0]
            t1 = time.perf_counter()

            probs_dict_pte = {class_order[i]: float(pte_out[i]) for i in range(len(class_order))}
            best_idx_pte = int(np.argmax(pte_out))
            best_cls_pte = class_order[best_idx_pte]

            result_pte = {
                "predicted_class": best_cls_pte,
                "label_vi": LABEL_TRANSLATIONS.get(best_cls_pte, best_cls_pte),
                "confidence": round(float(pte_out[best_idx_pte]), 4),
                "duration_ms": round((t1 - t0) * 1000, 1),
                "probabilities": probs_dict_pte,
                "color_class": LABEL_COLORS.get(best_cls_pte, "bg-gray-100"),
            }

        return jsonify({
            "pytorch": result_pth,
            "onnx": result_onnx,
            "executorch": result_pte,
            "translations": LABEL_TRANSLATIONS,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 Server Web So Sánh Mô Hình: PyTorch (.pth) vs ONNX (.onnx) vs ExecuTorch (.pte)")
    print(f"📌 Checkpoint .pth:        {CHECKPOINT_PTH.name} ({'Sẵn sàng' if pth_loaded else 'Chưa có'})")
    print(f"📌 Checkpoint .onnx:       {CHECKPOINT_ONNX.name} ({'Sẵn sàng' if onnx_loaded else 'Chưa có'})")
    print(f"📌 Checkpoint .pte:        {CHECKPOINT_PTE.name} ({'Sẵn sàng' if pte_loaded else 'Chưa có'})")
    print(f"📌 Trình tính toán PyTorch: {device}")
    print("🌐 Mở trình duyệt truy cập: http://localhost:5000")
    print("=" * 70 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
