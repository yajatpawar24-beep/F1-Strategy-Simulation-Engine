#!/bin/bash
# Monitor training progress

LOG_FILE="/Users/yajatpawar/Desktop/F1 Strategy Simulation/training.log"

echo "=========================================="
echo "F1 STRATEGY ENGINE - TRAINING MONITOR"
echo "=========================================="
echo ""

# Check if training is running
if pgrep -f "train_pipeline.py" > /dev/null; then
    echo "✅ Training is RUNNING"
    echo ""
else
    echo "⚠️  Training is NOT running"
    echo ""
fi

# Show last 30 lines of log
echo "Last 30 lines from training log:"
echo "------------------------------------------"
tail -30 "$LOG_FILE"
echo ""
echo "------------------------------------------"
echo ""
echo "To watch live: tail -f training.log"
echo "To stop training: pkill -f train_pipeline.py"
