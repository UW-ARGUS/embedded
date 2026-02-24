# Script to auto restart the embedded code
DEVICE_IP="192.168.194.151"

echo "sshing into the device" 

# ssh into the device and restart the argus service
ssh argus@"$DEVICE_IP" << 'EOF'
#   sudo systemctl reboot   # reboot the entire device

    # restart only the argus embedded service
    sudo systemctl restart autostart_argus.service
    sudo systemctl status autostart_argus.service
EOF

echo "Restarted argus embedded service on device $DEVICE_IP"