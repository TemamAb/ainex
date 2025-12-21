#!/usr/bin/env python3
"""
Create directories for the wallet connect system
"""

import os

# Create directories
directories = [
    'templates',
    'static',
    'static/css',
    'static/js'
]

for directory in directories:
    os.makedirs(directory, exist_ok=True)
    print(f"Created directory: {directory}")

print("All directories created successfully!")