#!/bin/bash

echo "=== Fixing Next.js Dynamic Import Error ==="

# Find all files that might have the dynamic import error
echo "Searching for files with dynamic imports..."
FILES=$(find . -name "*.tsx" -o -name "*.ts" | xargs grep -l "dynamic.*import" 2>/dev/null)

if [ -z "$FILES" ]; then
  echo "No files with dynamic imports found. Let's check app directory..."
  FILES=$(find app/ -name "*.tsx" -o -name "*.ts" 2>/dev/null)
fi

echo "Files to check:"
echo "$FILES"
echo ""

# Check each file
for FILE in $FILES; do
  if [ -f "$FILE" ]; then
    echo "Checking $FILE..."
    
    # Look for the pattern that causes the error
    if grep -q "dynamic(() => import.*App" "$FILE"; then
      echo "Found problematic dynamic import in $FILE"
      
      # Create backup
      cp "$FILE" "${FILE}.backup.$(date +%s)"
      
      # Fix the file using multiple pattern approaches
      # Pattern 1: single quotes
      sed -i "s/dynamic(() => import('\.\.\/App'),/dynamic(() => import('..\/App').then(mod => mod.default || mod),/g" "$FILE"
      
      # Pattern 2: double quotes  
      sed -i 's/dynamic(() => import("\.\.\/App"),/dynamic(() => import("..\/App").then(mod => mod.default || mod),/g' "$FILE"
      
      # Pattern 3: with type annotations
      sed -i "s/dynamic(() => import('\.\.\/App') as Promise<any>,/dynamic(() => import('..\/App').then(mod => mod.default || mod),/g" "$FILE"
      
      echo "Applied fixes to $FILE"
      echo ""
      echo "=== Before fix ==="
      grep -n -B2 -A2 "dynamic.*import.*App" "${FILE}.backup.*" 2>/dev/null | head -10 || true
      echo ""
      echo "=== After fix ==="
      grep -n -B2 -A2 "dynamic.*import.*App" "$FILE" | head -10 || true
      echo ""
    fi
  fi
done

echo ""
echo "=== Checking App.tsx structure ==="
if [ -f "App.tsx" ]; then
  echo "Found App.tsx in root"
  head -20 App.tsx
elif [ -f "app/page.tsx" ]; then
  echo "Found app/page.tsx"
  head -20 app/page.tsx
fi

echo ""
echo "=== Testing Build ==="
npm run build

if [ $? -eq 0 ]; then
  echo "✅ Build successful!"
  
  # Find which files were modified
  MODIFIED_FILES=$(git status --porcelain | grep -E "\.(tsx|ts)$" | awk '{print $2}')
  
  if [ -n "$MODIFIED_FILES" ]; then
    echo "Committing changes..."
    git add $MODIFIED_FILES
    git commit -m "fix: correct dynamic import syntax for Next.js compatibility"
    git push origin main
    echo "✅ Changes pushed to GitHub!"
  else
    echo "No files modified. The fix might have already been applied."
    echo "Current git status:"
    git status --porcelain
  fi
else
  echo "❌ Build failed. Let's see the error..."
  npm run build 2>&1 | tail -20
  
  echo ""
  echo "=== Manual Fix Required ==="
  echo "Please check these common files for dynamic imports:"
  echo "1. app/page.tsx"
  echo "2. app/layout.tsx" 
  echo "3. Any file in app/ directory"
  echo "4. components/ directory"
  
  echo ""
  echo "Run this to find the exact line:"
  echo "grep -r 'dynamic(() => import.*App' . --include='*.tsx' --include='*.ts'"
fi
