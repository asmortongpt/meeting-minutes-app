#!/bin/bash
# ============================================================================
# Monitor Grok AI Agents on Azure VMs
# Real-time progress tracking for Phases 3-11
# ============================================================================

VM1_IP="172.173.175.71"
VM2_IP="172.191.6.180"
VM3_IP="135.119.131.39"
VM_USER="azureuser"
SSH_KEY="~/.ssh/id_rsa"

echo "🔍 Monitoring Grok AI Agents"
echo "=============================="
echo ""

while true; do
    clear
    echo "🤖 Grok AI Agents - Live Status"
    echo "$(date)"
    echo "================================"
    echo ""

    # VM1 Status
    echo "📊 VM1 (172.173.175.71) - Phases 3-5 (UX, Integrations)"
    echo "------------------------------------------------------"
    ssh -q -i "$SSH_KEY" "${VM_USER}@${VM1_IP}" '
        if [ -f ~/grok-agent.pid ]; then
            PID=$(cat ~/grok-agent.pid)
            if ps -p $PID > /dev/null 2>&1; then
                echo "Status: ✅ RUNNING (PID: $PID)"
                echo "Latest: $(tail -n 3 ~/grok-agent.log 2>/dev/null || echo "No logs yet")"
            else
                echo "Status: ⏹️  STOPPED"
            fi
        else
            echo "Status: ⏳ NOT STARTED"
        fi
    ' 2>/dev/null || echo "Status: ❌ CANNOT CONNECT"
    echo ""

    # VM2 Status
    echo "📊 VM2 (172.191.6.180) - Phases 6-8 (Enterprise, Security, Scale)"
    echo "------------------------------------------------------"
    ssh -q -i "$SSH_KEY" "${VM_USER}@${VM2_IP}" '
        if [ -f ~/grok-agent.pid ]; then
            PID=$(cat ~/grok-agent.pid)
            if ps -p $PID > /dev/null 2>&1; then
                echo "Status: ✅ RUNNING (PID: $PID)"
                echo "Latest: $(tail -n 3 ~/grok-agent.log 2>/dev/null || echo "No logs yet")"
            else
                echo "Status: ⏹️  STOPPED"
            fi
        else
            echo "Status: ⏳ NOT STARTED"
        fi
    ' 2>/dev/null || echo "Status: ❌ CANNOT CONNECT"
    echo ""

    # VM3 Status
    echo "📊 VM3 (135.119.131.39) - Phases 9-11 (Mobile, Advanced AI, Deploy)"
    echo "------------------------------------------------------"
    ssh -q -i "$SSH_KEY" "${VM_USER}@${VM3_IP}" '
        if [ -f ~/grok-agent.pid ]; then
            PID=$(cat ~/grok-agent.pid)
            if ps -p $PID > /dev/null 2>&1; then
                echo "Status: ✅ RUNNING (PID: $PID)"
                echo "Latest: $(tail -n 3 ~/grok-agent.log 2>/dev/null || echo "No logs yet")"
            else
                echo "Status: ⏹️  STOPPED"
            fi
        else
            echo "Status: ⏳ NOT STARTED"
        fi
    ' 2>/dev/null || echo "Status: ❌ CANNOT CONNECT"
    echo ""

    echo "================================"
    echo "Press Ctrl+C to exit"
    echo "Refreshing in 10 seconds..."

    sleep 10
done
