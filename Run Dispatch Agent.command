#!/bin/bash
cd "$(dirname "$0")"
python3 scripts/dispatch-agent.py interactive
echo ""
read -p "Press Enter to close..."
