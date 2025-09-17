# Paste the script and save (Ctrl+O, Enter, Ctrl+X)
#!/bin/bash
# clean_repo.sh
# Clean Flask + React repo for GitHub push

# Set repo root
REPO_ROOT=$(pwd)

echo "Cleaning repo in $REPO_ROOT ..."

# 1️⃣ Create .gitignore
cat <<EOL > .gitignore
# Node / React
node_modules/
dist/
build/
.env
*.log

# Python / Flask
__pycache__/
*.pyc
instance/
*.sqlite3

# OS / IDE
.DS_Store
.vscode/
.idea/
EOL

echo ".gitignore created."

# 2️⃣ Remove ignored files from Git cache
git rm -r --cached node_modules 2>/dev/null
git rm -r --cached dist 2>/dev/null
git rm -r --cached build 2>/dev/null
git rm -r --cached *.log 2>/dev/null
git rm -r --cached *.sqlite3 2>/dev/null

echo "Removed cached ignored files."

# 3️⃣ Optional: Install and configure Git LFS for large files
if ! command -v git-lfs &> /dev/null
then
    echo "Installing Git LFS..."
    sudo apt update && sudo apt install -y git-lfs
fi

git lfs install

# Track common large files
git lfs track "*.pdf"
git lfs track "*.zip"
git lfs track "*.png"

git add .gitattributes
echo "Git LFS configured for PDF, ZIP, PNG files."

# 4️⃣ Add all changes and commit
git add .
git commit -m "Clean repo: remove build artifacts, logs, cache; setup .gitignore and Git LFS"

echo "Repo cleaned and committed."

# 5️⃣ Instructions for push
echo "✅ Repo is ready. Push with:"
echo "git push origin main"


