#!/bin/bash
cd "$(dirname "$0")"
python3 scripts/dispatch-agent.py generate --submit
echo ""
read -p "Press Enter to close..."
