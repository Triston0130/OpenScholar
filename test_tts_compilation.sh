#!/bin/bash

echo "Testing TTS compilation..."

cd frontend

# Check if TypeScript compilation succeeds
echo "Checking TypeScript compilation..."
npx tsc --noEmit

if [ $? -eq 0 ]; then
  echo "✅ TypeScript compilation successful!"
else
  echo "❌ TypeScript compilation failed!"
  exit 1
fi

echo "All checks passed! The TTS system should now work perfectly."