# Install the systemd service
cp ./systemd/bme680-homekit.service /etc/systemd/system
systemctl daemon-reload
systemctl start bme680-homekit
systemctl enable bme680-homekit

