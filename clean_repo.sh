#!/bin/bash
set -e

echo "🚀 Cleaning repo before pushing to GitHub..."

# 1. Remove unwanted large dirs from Git cache (not from disk)
git rm -r --cached node_modules 2>/dev/null || true
git rm -r --cached dist 2>/dev/null || true
git rm -r --cached build 2>/dev/null || true
git rm -r --cached venv 2>/dev/null || true
git rm -r --cached seo-backend/venv 2>/dev/null || true
git rm --cached seo-backend.zip 2>/dev/null || true

# 2. Update .gitignore so they never get committed again
cat <<EOL >> .gitignore

# Ignore heavy stuff
node_modules/
dist/
build/
venv/
seo-backend/venv/
*.log
*.sqlite3
seo-backend.zip
EOL

# 3. Add Git LFS for binary files (images, pdfs, zips, etc.)
git lfs install
git lfs track "*.pdf" "*.png" "*.jpg" "*.jpeg" "*.zip"
git add .gitattributes

# 4. Stage all changes
git add .gitignore
git add .

# 5. Commit cleanup
git commit -m "Repo cleanup: remove venv/node_modules, add .gitignore, enable LFS" || echo "✅ Nothing new to commit"

# 6. Force push to GitHub
git push origin main --force

echo "🎉 Repo cleaned and pushed successfully!"
