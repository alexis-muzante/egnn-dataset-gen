#!/bin/bash

# OMNeT++ Configuration Environment Variable Generator
# This script calculates and exports variables for the configuration file
set -a          # auto-export everything that is sourced
. ./simulation.conf   # (dot-space) source the file
set +a          # stop the auto-export

# Input parameters (modify these values as needed)
numRX=${numRX:-5}        # Number of RX hosts
numTX=${numTX:-5}        # Number of TX hosts  
numRXTX=${numRXTX:-3}    # Number of RXTX hosts
numRelay=${numRelay:-2}  # Number of relay hosts
repeat=${repeat:-1}      # Number of repetitions

# Calculate derived variables for 1-to-1 TCP connections
# Each RX host needs: 1 Batman app + apps to receive from each TX and RXTX
numListen=$((numTX + numRXTX))

# Each TX host needs: 1 Batman app + apps to connect to each RX and RXTX  
numConn=$((numRX + numRXTX))

# Each RXTX host needs: 1 Batman app + apps to receive (like RX) + apps to send (like TX)
numConnRXTX=$((numTX + numRXTX + numRX + numRXTX))

# Pre-calculate all arithmetic values for envsubst
numAppsRX=$((1 + numListen))
numAppsTX=$((1 + numConn))
numAppsRXTX=$((1 + numConnRXTX))

# Calculate app ranges for different host types
txToRxEnd=$((numTX))
rxTxToRxStart=$((numTX + 1))
rxTxToRxEnd=$((numTX + numRXTX))


txToRxEnd2=$((numRX))
txToRxTxStart=$((numRX + 1))
txToRxTxEnd=$((numRX + numRXTX))

rxtxServerTxEnd=$((numTX))
rxtxServerRxtxStart=$((numTX + 1))
rxtxServerRxtxEnd=$((numTX + numRXTX))

rxtxClientRxStart=$((numTX + numRXTX + 1))
rxtxClientRxEnd=$((numTX + numRXTX + numRX))
rxtxClientRxtxStart=$((numTX + numRXTX + numRX + 1))
rxtxClientRxtxEnd=$((numTX + numRXTX + numRX + numRXTX))

# Export all variables for envsubst
export numRX numTX numRXTX numRelay repeat 
export numListen numConn numConnRXTX
export numAppsRX numAppsTX numAppsRXTX
export txToRxEnd rxTxToRxStart rxTxToRxEnd
export txToRxEnd2 txToRxTxStart txToRxTxEnd
export rxtxServerTxEnd rxtxServerRxtxStart rxtxServerRxtxEnd
export rxtxClientRxStart rxtxClientRxEnd rxtxClientRxtxStart rxtxClientRxtxEnd

# Display calculated values
echo "=== OMNeT++ Configuration Variables ==="
echo "Input Parameters:"
echo "  numRX = $numRX"
echo "  numTX = $numTX" 
echo "  numRXTX = $numRXTX"
echo "  numRelay = $numRelay"
echo "  repeat = $repeat"
echo ""
echo "Calculated Variables:"
echo "  numListen = $numListen (apps for RX hosts: $numTX TX + $numRXTX RXTX)"
echo "  numConn = $numConn (apps for TX hosts: $numRX RX + $numRXTX RXTX)"
echo "  numConnRXTX = $numConnRXTX (apps for RXTX hosts: receive from $numTX TX + $numRXTX RXTX, send to $numRX RX + $numRXTX RXTX)"
echo ""

# Function to generate the substituted configuration file
generate_config() {
    local input_file="${1:-config.ini}"
    local output_file="${2:-config_generated.ini}"
    
    if [ ! -f "$input_file" ]; then
        echo "Error: Input file '$input_file' not found!"
        return 1
    fi
    
    echo "Generating configuration file..."
    echo "Input: $input_file"
    echo "Output: $output_file"
    
    # Use envsubst to substitute variables
    envsubst < "$input_file" > "$output_file"
    
    echo "Configuration file generated successfully!"
    echo ""
    echo "Key substitutions made:"
    echo "  \${numListen} -> $numListen"
    echo "  \${numConn} -> $numConn" 
    echo "  \${numConnRXTX} -> $numConnRXTX"
    echo "  \${numRX} -> $numRX"
    echo "  \${numTX} -> $numTX"
    echo "  \${numRXTX} -> $numRXTX"
    echo "  \${numRelay} -> $numRelay"
    echo "  \${repeat} -> $repeat"
}

# If script is run directly (not sourced), provide usage information
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Usage examples:"
    echo "1. Source this script to export variables:"
    echo "   source $0"
    echo ""
    echo "2. Generate config file:"
    echo "   source $0"
    echo "   generate_config input.ini output.ini"
    echo ""
    echo "3. Set custom values and generate:"
    echo "   numRX=10 numTX=8 numRXTX=5 source $0"
    echo "   generate_config config_template.ini config_final.ini"
    echo ""
    echo "4. One-liner to generate with custom values:"
    echo "   numRX=10 numTX=8 numRXTX=5 bash -c 'source $0 && generate_config input.ini output.ini'"
fi