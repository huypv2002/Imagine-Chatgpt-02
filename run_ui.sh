#!/bin/bash

# Script để chạy Text-to-Image Generator UI

echo "🎨 Text-to-Image Generator UI"
echo "=============================="
echo ""

# Check if PySide6 is installed
if ! python -c "import PySide6" 2>/dev/null; then
    echo "⚠️  PySide6 chưa được cài đặt!"
    echo ""
    echo "Đang cài đặt dependencies..."
    
    # Try uv first
    if command -v uv &> /dev/null; then
        echo "Sử dụng uv..."
        uv sync
    else
        echo "Sử dụng pip..."
        pip install pyside6
    fi
    
    echo ""
fi

# Run the UI
echo "🚀 Đang khởi động UI..."
echo ""
python image_generator_ui.py
