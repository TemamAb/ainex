#!/bin/bash

echo "Ì¥Ñ Deploying V3 Dashboard..."
cd ~/Desktop/ainex

# Check if V3 dashboard file exists
if [ ! -f "app/page.v3.tsx" ]; then
    echo "‚ùå V3 dashboard file not found! Run the upgrade script first."
    exit 1
fi

# Backup current dashboard
if [ -f "app/page.tsx" ]; then
    cp app/page.tsx app/page.backup.$(date +%Y%m%d_%H%M%S).tsx
    echo "‚úÖ Current dashboard backed up"
fi

# Deploy V3 dashboard
mv app/page.v3.tsx app/page.tsx
echo "‚úÖ V3 Dashboard deployed successfully!"

# Run build to verify everything works
echo "Ì¥® Building project..."
if npm run build; then
    echo "‚úÖ Build successful! V3 Dashboard is ready."
    echo ""
    echo "Ìæâ DEPLOYMENT COMPLETE!"
    echo "======================="
    echo "Ìºê Start your development server with: npm run dev"
    echo ""
    echo "Ì≥ã Next Steps:"
    echo "1. Connect API endpoints to your AInex engine"
    echo "2. Test simulation mode with real blockchain data"
    echo "3. Configure admin settings for your strategy"
    echo "4. Monitor real-time performance in the dashboard"
    echo ""
    echo "‚ö†Ô∏è  Remember: No mock data allowed - only real blockchain connections!"
else
    echo "‚ùå Build failed! Restoring original dashboard..."
    mv app/page.tsx app/page.v3.tsx
    if [ -f app/page.backup.*.tsx ]; then
        mv app/page.backup.*.tsx app/page.tsx
    fi
    echo "Original dashboard restored. Check for errors above."
    exit 1
fi
