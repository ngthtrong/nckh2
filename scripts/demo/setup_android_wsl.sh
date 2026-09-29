#!/usr/bin/env bash
# Cài Android SDK (command-line, không cần Android Studio / sudo) trên Linux hoặc WSL2 để build APK.
#
#   scripts/demo/setup_android_wsl.sh               # SDK để build APK: platform-tools, platform, build-tools, NDK
#   scripts/demo/setup_android_wsl.sh --emulator    # thêm emulator + system image x86_64 + AVD "rescue_api36"
#
# Mặc định cài vào ~/Android/Sdk (đổi bằng ANDROID_SDK_ROOT). Emulator trên WSL2 cần /dev/kvm và
# user thuộc nhóm kvm:  sudo usermod -aG kvm $USER  rồi  wsl --shutdown  (chạy từ Windows).
set -euo pipefail

SDK="${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}"
CMDLINE_ZIP="commandlinetools-linux-16111833_latest.zip"
NDK="ndk;28.2.13676358"          # = flutter.ndkVersion của Flutter 3.47
PLATFORM="platforms;android-37.0"  # = compileSdk 37 trong fe/app/android/app/build.gradle.kts
BUILD_TOOLS="build-tools;36.0.0"
EMULATOR=0
[[ "${1:-}" == "--emulator" ]] && EMULATOR=1

mkdir -p "$SDK/cmdline-tools"
if [[ ! -x "$SDK/cmdline-tools/latest/bin/sdkmanager" ]]; then
  echo ">> Tải Android command-line tools ..."
  tmp="$(mktemp -d)"
  curl -fL --retry 5 -o "$tmp/cmdline.zip" "https://dl.google.com/android/repository/$CMDLINE_ZIP"
  unzip -q "$tmp/cmdline.zip" -d "$tmp"
  rm -rf "$SDK/cmdline-tools/latest"
  mv "$tmp/cmdline-tools" "$SDK/cmdline-tools/latest"
  rm -rf "$tmp"
fi
SDKMANAGER="$SDK/cmdline-tools/latest/bin/sdkmanager"

echo ">> Chấp nhận license ..."
yes | "$SDKMANAGER" --sdk_root="$SDK" --licenses >/dev/null || true

PACKAGES=("platform-tools" "$PLATFORM" "$BUILD_TOOLS" "$NDK")
if [[ $EMULATOR -eq 1 ]]; then
  PACKAGES+=("emulator" "system-images;android-36;google_apis;x86_64")
fi
echo ">> Cài: ${PACKAGES[*]} (vài GB, lâu khi mạng chậm) ..."
"$SDKMANAGER" --sdk_root="$SDK" "${PACKAGES[@]}"

if [[ $EMULATOR -eq 1 ]]; then
  echo no | "$SDK/cmdline-tools/latest/bin/avdmanager" create avd --force -n rescue_api36 \
    -k "system-images;android-36;google_apis;x86_64" -d pixel_6 >/dev/null
  echo ">> Đã tạo AVD rescue_api36. Chạy: $SDK/emulator/emulator -avd rescue_api36 -no-snapshot"
fi

if command -v flutter >/dev/null; then
  flutter config --android-sdk "$SDK" >/dev/null
  yes | flutter doctor --android-licenses >/dev/null 2>&1 || true
fi

cat <<MSG
>> Xong. Thêm vào ~/.bashrc:
   export ANDROID_SDK_ROOT="$SDK"
   export PATH="\$ANDROID_SDK_ROOT/platform-tools:\$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:\$PATH"
>> Build APK:  cd fe/app && flutter build apk --debug --dart-define=SERVER_URL=http://<IP-LAN>:8000
MSG
