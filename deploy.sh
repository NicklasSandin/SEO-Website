#!/bin/bash

FRONTEND_DIR="/home/nicklas/seo-service-website"
BACKEND_DIR="/home/nicklas/seo-backend"
BACKEND_STATIC_DIR="$BACKEND_DIR/src/static"
BACKEND_ENTRY="seo_routes.py"   # adjust if named differently

echo "🔨 Building frontend..."
cd "$FRONTEND_DIR" || exit 1
npm run build

echo "🧹 Cleaning old static files..."
rm -rf "$BACKEND_STATIC_DIR"/*

echo "📂 Copying new build to backend static..."
cp -r dist/* "$BACKEND_STATIC_DIR"/

echo "♻️ Restarting Flask backend..."
# kill existing process if running
pkill -f "$BACKEND_ENTRY"

# start backend with venv python
cd "$BACKEND_DIR" || exit 1
"$BACKEND_DIR/venv/bin/python" "$BACKEND_ENTRY" &

echo "✅ Frontend deployed and backend restarted"
