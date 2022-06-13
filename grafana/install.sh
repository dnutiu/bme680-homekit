wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
apt-get update
apt-get install -y grafana

cp grafana.ini /etc/grafana/grafana.ini
systemctl daemon-reload
systemctl enable grafana-server
systemctl start grafana-server