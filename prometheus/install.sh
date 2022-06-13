wget https://github.com/prometheus/prometheus/releases/download/v2.36.1/prometheus-2.36.1.linux-armv6.tar.gz
tar -xzvf prometheus-2.36.1.linux-armv6.tar.gz
rm prometheus-2.36.1.linux-armv6.tar.gz

cp prometheus.service /etc/systemd/system
systemctl daemon-reload
systemctl start prometheus
systemctl enable prometheus

