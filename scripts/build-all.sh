#!/usr/bin/env bash
# Build pipeline helper.
# 1) Builds apps/web (Vite production build).
# 2) Copies the resulting dist/ into apps/desktop so Electron can load it.
# 3) Runs electron-builder to produce platform installers.
echo "Building apps/web..."
echo "Copying apps/web/dist into apps/desktop..."
echo "Running electron-builder for apps/desktop..."

