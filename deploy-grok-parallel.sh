#!/bin/bash
# ============================================================================
# Deploy Grok Agents in Parallel to Azure VMs
# Maximum parallelization for fastest completion
# ============================================================================

set -e

echo "🚀 Deploying Grok AI Agents in Parallel"
echo "=========================================="

# Configuration
VM1_IP="172.173.175.71"
VM2_IP="172.191.6.180"
VM3_IP="135.119.131.39"
VM_USER="azureuser"
GROK_API_KEY="${GROK_API_KEY:-xai-wOeEAYZslZCGGu4tudhzBdMIm4tiZ6Ya4W2cjE0Rgm1UbXnJJezOhaJwdpgTliMg56nCGZTbslp6zlML}"
GITHUB_PAT="${GITHUB_PAT:-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}"

echo ""
echo "📋 Phase Distribution:"
echo "  VM1 ($VM1_IP): Phases 3-5 (UX, Integrations, Analytics)"
echo "  VM2 ($VM2_IP): Phases 6-8 (Enterprise, Security, Scale)"
echo "  VM3 ($VM3_IP): Phases 9-11 (Mobile, Advanced AI, Deploy)"
echo ""

# Function to deploy to a single VM
deploy_vm() {
    local vm_ip="$1"
    local phases="$2"
    local vm_name="$3"

    echo "📦 Deploying to $vm_name ($vm_ip)..."

    # Create remote directory
    ssh -o StrictHostKeyChecking=no "${VM_USER}@${vm_ip}" "mkdir -p ~/meeting-minutes-work" 2>/dev/null || true

    # Copy agent script
    scp -o StrictHostKeyChecking=no grok-autonomous-agent.py "${VM_USER}@${vm_ip}:~/meeting-minutes-work/" 2>/dev/null

    # Set up and run agent
    ssh -o StrictHostKeyChecking=no "${VM_USER}@${vm_ip}" bash <<EOF
set -e

cd ~/meeting-minutes-work

# Install Python dependencies
pip3 install --user requests >/dev/null 2>&1 || true

# Make script executable
chmod +x grok-autonomous-agent.py

# Set environment
export GROK_API_KEY="$GROK_API_KEY"
export GITHUB_PAT="$GITHUB_PAT"

# Clone/update repository
if [ ! -d "meeting-minutes-app" ]; then
    git clone https://${GITHUB_PAT}@github.com/andrewmorton/meeting-minutes-app.git 2>&1 | grep -v "Password\|token" || true
    cd meeting-minutes-app
else
    cd meeting-minutes-app
    git pull 2>&1 | grep -v "Password\|token" || true
fi

# Configure git
git config user.name "Grok AI Agent"
git config user.email "grok-agent@meetingminutes.ai"

# Copy agent script here
cp ../grok-autonomous-agent.py .

# Run agent in background
nohup python3 grok-autonomous-agent.py '$phases' '$vm_name' > ~/grok-$vm_name.log 2>&1 &
echo \$! > ~/grok-$vm_name.pid

echo "✅ Agent started on $vm_name (PID: \$(cat ~/grok-$vm_name.pid))"
EOF

    echo "✅ Deployed to $vm_name"
}

# Deploy to all VMs in parallel
echo "🚀 Starting parallel deployment..."
deploy_vm "$VM1_IP" "[3,4,5]" "vm1" &
PID1=$!

deploy_vm "$VM2_IP" "[6,7,8]" "vm2" &
PID2=$!

deploy_vm "$VM3_IP" "[9,10,11]" "vm3" &
PID3=$!

# Wait for all deployments
echo "⏳ Waiting for all deployments to complete..."
wait $PID1 && echo "✅ VM1 deployment complete" || echo "❌ VM1 deployment failed"
wait $PID2 && echo "✅ VM2 deployment complete" || echo "❌ VM2 deployment failed"
wait $PID3 && echo "✅ VM3 deployment complete" || echo "❌ VM3 deployment failed"

echo ""
echo "=========================================="
echo "🎉 All Grok Agents Deployed and Running!"
echo "=========================================="
echo ""
echo "Monitor progress:"
echo "  VM1: ssh ${VM_USER}@${VM1_IP} 'tail -f ~/grok-vm1.log'"
echo "  VM2: ssh ${VM_USER}@${VM2_IP} 'tail -f ~/grok-vm2.log'"
echo "  VM3: ssh ${VM_USER}@${VM3_IP} 'tail -f ~/grok-vm3.log'"
echo ""
echo "Check status:"
echo "  VM1: ssh ${VM_USER}@${VM1_IP} 'ps -p \$(cat ~/grok-vm1.pid 2>/dev/null) 2>/dev/null && echo RUNNING || echo STOPPED'"
echo "  VM2: ssh ${VM_USER}@${VM2_IP} 'ps -p \$(cat ~/grok-vm2.pid 2>/dev/null) 2>/dev/null && echo RUNNING || echo STOPPED'"
echo "  VM3: ssh ${VM_USER}@${VM3_IP} 'ps -p \$(cat ~/grok-vm3.pid 2>/dev/null) 2>/dev/null && echo RUNNING || echo STOPPED'"
echo ""
echo "Expected completion: 2-4 hours"
echo ""
