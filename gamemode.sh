#!/bin/bash

# PROJECT FREEDOM: UNIFIED GAMING ENGINE
# Usage: 
#   1. ./gamemode.sh              (Optimizes PC & Launches Lutris)
#   2. ./gamemode.sh trainer.exe  (Launches a trainer securely)

# --- CONFIGURATION ---
DEFAULT_SWAPPINESS=60
GAMING_SWAPPINESS=100
STATE_DIR="$HOME/.config/gamemode"
mkdir -p "$STATE_DIR"


# 1. Capture the default swappiness to return to it later
ORIGINAL_SWAP=$(cat /proc/sys/vm/swappiness)

# 2. Define the Restoration logic
restore_system() {
    echo ""
    echo "[!] Closing session: Restoring system defaults..."
    
    
    echo 1 | sudo tee /proc/sys/kernel/yama/ptrace_scope > /dev/null
    
    
    sudo sysctl vm.swappiness=$ORIGINAL_SWAP > /dev/null
    
    echo "[*] System baseline restored. Goodbye."
    exit
}

trap restore_system EXIT SIGINT SIGTERM


# ==============================================================================
# MODE 1: TRAINER LAUNCHER (Logic from your provided script)
# ==============================================================================
run_trainer_mode() {
    TRAINER_CMD="$1"
    shift
    
    echo "[*] TRAINER MODE ACTIVATED: $TRAINER_CMD"
    
    # Determine Wine Prefix (Flatpak detection)
    det_wineprefix() {
        # Check if user manually set it
        if [ -n "${WINEPREFIX-}" ] && [ -d "${WINEPREFIX}" ]; then
            echo "$WINEPREFIX"; return
        fi
        # Check OG Wine
        if [ -d "$HOME/.wine" ]; then
            echo "$HOME/.wine"; return
        fi
        # Check Flatpak Lutris Default 
        if [ -d "$HOME/.var/app/net.lutris.Lutris/data/wine" ]; then
            echo "$HOME/.var/app/net.lutris.Lutris/data/wine"; return
        fi
        echo ""
    }

    WINEPREFIX_TO_USE="$(det_wineprefix)"
    
    if [ -n "$WINEPREFIX_TO_USE" ]; then
        echo "    -> Using WINEPREFIX: $WINEPREFIX_TO_USE"
        export WINEPREFIX="$WINEPREFIX_TO_USE"
    else
        echo "    [!] WARN: No WINEPREFIX detected. Trainer might not find the game."
    fi

    #read current security state
    ORIG_PTRACE="$(cat /proc/sys/kernel/yama/ptrace_scope 2>/dev/null || echo 1)"
    
    # if shields are UP (1), ask for sudo to lower them. 
    # if shields are DOWN (0) because Game Mode is running,skip sudo.
    if [ "$ORIG_PTRACE" -ne 0 ]; then
        echo "    -> Shields are UP. Requesting permission to inject..."
        sudo -v
        echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope >/dev/null
    else
        echo "    -> Shields are already DOWN (Game Mode Active). Proceeding..."
    fi

    #launch trainer
    echo "    -> Injecting Trainer..."

    #use nohup/setsid to detach it so it doesn't die if script closes
    setsid wine "$TRAINER_CMD" >/dev/null 2>&1 &
    TPID=$!
    echo "    -> Trainer PID: $TPID"
    
    # wait for trainer to close
    wait "$TPID" 2>/dev/null || true
    
    # restore Security State, if changed
    # if it was 0 when we started, we leave it at 0, dont wanna break the game
    echo "    -> Trainer exited. Restoring security state to: $ORIG_PTRACE"
    echo "${ORIG_PTRACE}" | sudo tee /proc/sys/kernel/yama/ptrace_scope >/dev/null
    
    exit 0
}

# check if the script was run with an argument
if [ -n "${1-}" ]; then
    run_trainer_mode "$@"
fi

# ==============================================================================
# MODE 2: GAME MODE ORCHESTRATOR (System Optimization)
# ==============================================================================

echo "========================================"
echo "    ENTERING HIGH-PERFORMANCE MODE"
echo "========================================"

# verify running as regular user
if [ "$EUID" -eq 0 ]; then
   echo "[!] ERROR: Do NOT run this script as root!"
   exit 1
fi

# ask for sudo once
sudo -v

# 1. Memory Optimization
echo "[*] Setting Swappiness to $GAMING_SWAPPINESS (Force ZRAM)..."
sudo sysctl vm.swappiness=$GAMING_SWAPPINESS > /dev/null

echo "[*] Dropping File Caches (Clearing RAM)..."
sudo sync
echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null

# 2. SECURITY BYPASS (Global)
echo "[*] Lowering PTrace Scope (Allowing Memory Injection)..."
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope > /dev/null

# 3. Thermal Check
CURRENT_TEMP=$(cat /sys/class/thermal/thermal_zone0/temp)
CURRENT_TEMP_C=$((CURRENT_TEMP / 1000))

if [ "$CURRENT_TEMP_C" -gt 80 ]; then
    echo "    [!] WARNING: CPU is ${CURRENT_TEMP_C}°C. Hot!"
else
    echo "    -> Thermals Nominal (${CURRENT_TEMP_C}°C)."
fi

# 4. GPU OPTIMIZATION
echo "[*] Overclocking Mesa Driver (Iris + Performance)..."
export vblank_mode=0
export MESA_LOADER_DRIVER_OVERRIDE=iris
export INTEL_DEBUG=norbc
export MESA_GL_VERSION_OVERRIDE=4.6
export MESA_GLSL_VERSION_OVERRIDE=460

# 5. LAUNCH LUTRIS
echo ""
echo "Launching Lutris..."

if flatpak list | grep -q "net.lutris.Lutris"; then
    echo "    -> Detected Flatpak version."
    flatpak run net.lutris.Lutris
else
    echo "    -> Detected Native version."
    lutris
fi

# -- Cleanup Phase --
echo ""
echo "========================================"
echo "    RESTORING DESKTOP MODE"
echo "========================================"

echo "[*] Restoring Security..."
echo 1 | sudo tee /proc/sys/kernel/yama/ptrace_scope > /dev/null

echo "[*] Restoring Memory (Swappiness $DEFAULT_SWAPPINESS)..."
sudo sysctl vm.swappiness=$DEFAULT_SWAPPINESS > /dev/null

echo "    -> System Normal."
echo "========================================"
sleep 3
