#!/usr/bin/env bash
# ==============================================================================
# HoneyNet One-Click Startup Script
# ==============================================================================
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "========================================================"
echo "      🛡️  HONEYNET AI ADAPTIVE HONEYPOT LAUNCHER"
echo "========================================================"

# 1. Activate Python Environment
if [ -d ".venv" ]; then
    echo "[+] Activating Python virtual environment (.venv)..."
    source .venv/bin/activate
elif command -v python3 &> /dev/null; then
    echo "[!] .venv not found. Creating .venv..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    echo "[ERROR] Python 3 is required but not found."
    exit 1
fi

# 2. Check Ollama Health
echo "[+] Checking Local Ollama AI Status..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "  [✓] Ollama daemon is active."
    if curl -s http://localhost:11434/api/tags | grep -q "qwen2.5:7b"; then
        echo "  [✓] Model 'qwen2.5:7b' is ready."
    else
        echo "  [!] Note: Model 'qwen2.5:7b' not yet pulled. System will use heuristic classifier or you can run: 'ollama pull qwen2.5:7b'."
    fi
else
    echo "  [!] Ollama is not running on http://localhost:11434."
    echo "  [!] HoneyNet will automatically operate in zero-downtime Heuristic Classification mode."
    echo "  [!] (To enable full LLM: run 'ollama serve' in another terminal)."
fi

# 3. Seed HoneyFS Virtual Filesystem
echo "[+] Ensuring HoneyFS deception filesystem is seeded from safe templates..."
python3 -c "from backend.asset_manager import seed_honeyfs_from_templates; seed_honeyfs_from_templates()"

# 4. Cowrie Docker (Optional / If Docker Available)
if command -v docker &> /dev/null && docker info > /dev/null 2>&1; then
    echo "[+] Docker detected. Launching Cowrie honeypot container..."
    docker compose up -d
    echo "  [✓] Cowrie SSH listening on port 2222 (AuthRandom enabled)."
else
    echo "[!] Docker not detected or not running. Standalone honeypot simulator mode is active."
    echo "  [!] Use 'python3 honeypot_sim.py' to generate realistic attack telemetry."
fi

# 4. Launch Services
echo ""
echo "[+] Starting FastAPI backend on http://localhost:8000 ..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --log-level warning &
FASTAPI_PID=$!

sleep 1

echo "[+] Starting Streamlit Dashboard on http://localhost:8501 ..."
streamlit run dashboard/dashboard.py --server.port 8501 --server.headless true &
STREAMLIT_PID=$!

echo ""
echo "========================================================"
echo "  🚀 HoneyNet is Running!"
echo "  ----------------------------------------------------"
echo "  📊 Live Dashboard: http://localhost:8501"
echo "  🔌 API Backend:    http://localhost:8000 (Docs: /docs)"
echo "  🍯 Cowrie SSH:     ssh root@localhost -p 2222"
echo "  🎯 Attack Sim:     python3 honeypot_sim.py"
echo "========================================================"
echo "Press Ctrl+C to stop all HoneyNet services."

# Trap termination signals to clean up background processes
cleanup() {
    echo ""
    echo "[+] Stopping HoneyNet services..."
    kill $FASTAPI_PID 2>/dev/null || true
    kill $STREAMLIT_PID 2>/dev/null || true
    if command -v docker &> /dev/null; then
        docker compose down 2>/dev/null || true
    fi
    echo "[✓] Cleaned up all processes. Goodbye!"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Keep script running
wait
