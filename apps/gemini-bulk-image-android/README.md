# Gemini Bulk Image (Android)

Android app for bulk Gemini image generation: enter an API key, pick a model by task (image/coding/text), upload one shared base image plus many target images, and run serial or parallel generation with per-request tracking and download.

## Features

- Secure API key storage (EncryptedSharedPreferences)
- Fetch models from Gemini `listModels` and categorize by task
- Pick 1 base/source image + multiple target images
- Each request sends: prompt + base image + one unique target image
- Serial or parallel execution (1–8 concurrent when parallel)
- Per-request success/failure tracking with previews
- Save outputs to `Pictures/GeminiBulk`

## Build APK

```bash
export ANDROID_HOME="$HOME/android-sdk"
cd apps/gemini-bulk-image-android
./gradlew assembleDebug
```

APK output: `app/build/outputs/apk/debug/app-debug.apk`

## Usage

1. Enter your [Gemini API key](https://aistudio.google.com/apikey) and tap **Save API Key**.
2. Tap **Load Models** and select an image-capable model (e.g. `gemini-2.5-flash-image`).
3. Enter a prompt, select the base image and target images.
4. Choose serial or parallel mode, then **Start Bulk Generation**.
5. Download individual or all successful images.

## Recommended models

Use image-generation models (Nano Banana family), for example:

- `gemini-3.1-flash-image`
- `gemini-3-pro-image`
- `gemini-2.5-flash-image`
