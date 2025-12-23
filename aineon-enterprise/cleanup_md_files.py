#!/usr/bin/env python3
"""
AINEON MD FILES CLEANUP SCRIPT
Systematically remove excessive .md files while keeping core specifications
"""

import os
import glob
from pathlib import Path

def cleanup_md_files():
    """Remove excessive .md files, keep only critical ones"""
    
    # Get current directory
    current_dir = Path.cwd()
    
    # Core files to KEEP
    KEEP_FILES = {
        'AINEON_ENGINE_DNA.md',                    # Master specifications
        'AINEONAGENT_PROMPT.md',                   # Agent configuration  
        'CONTRIBUTING.md',                         # Contribution guide
        'SECURITY.md',                            # Security documentation
        'README.md',                              # Main documentation
        'AINEON_BLOCKCHAIN_ELITE_IMPLEMENTATION.md', # Elite blockchain
        'AINEON_BLOCKCHAIN_CONNECTED_IMPLEMENTATION.md', # Blockchain connected
        'AINEON_CERTIFIED_SIMULATION_REPORT.md',   # Simulation certification
    }
    
    # Files to evaluate (optional keep)
    EVALUATE_FILES = {
        'AINEON_BLOCKCHAIN_VALIDATION_FINAL_REPORT.md',
        'AINEON_FINAL_VALIDATION_SUMMARY.md',
    }
    
    # Get all .md files in root directory
    md_files = list(current_dir.glob('*.md'))
    
    print(f"🔍 Found {len(md_files)} .md files in root directory")
    print(f"📋 Planning to keep {len(KEEP_FILES)} core files")
    print(f"⚖️ Evaluating {len(EVALUATE_FILES)} optional files")
    
    removed_count = 0
    kept_count = 0
    
    for md_file in md_files:
        if md_file.name in KEEP_FILES:
            print(f"✅ KEEP: {md_file.name}")
            kept_count += 1
        elif md_file.name in EVALUATE_FILES:
            print(f"⚖️ EVALUATE: {md_file.name} (keeping for now)")
            kept_count += 1
        else:
            print(f"🗑️ REMOVE: {md_file.name}")
            try:
                md_file.unlink()
                removed_count += 1
                print(f"   ✅ Successfully removed {md_file.name}")
            except Exception as e:
                print(f"   ❌ Failed to remove {md_file.name}: {e}")
    
    print(f"\n📊 CLEANUP SUMMARY:")
    print(f"   ✅ Kept: {kept_count} files")
    print(f"   🗑️ Removed: {removed_count} files")
    print(f"   📁 Net change: {removed_count} fewer .md files")
    
    # List remaining files
    remaining_files = list(current_dir.glob('*.md'))
    print(f"\n📋 REMAINING .MD FILES ({len(remaining_files)}):")
    for file in sorted(remaining_files):
        print(f"   📄 {file.name}")

if __name__ == "__main__":
    print("🧹 AINEON MD FILES CLEANUP")
    print("=" * 50)
    cleanup_md_files()
    print("\n🎉 Cleanup completed!")