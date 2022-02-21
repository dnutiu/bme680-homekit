
# Introduction

Expose BME680 sensor readings to Apple Homekit.

## Installing

Ensure you are the `pi` user. Clone the repo in home and then install requirements. 

```bash
cd /home/pi && git clone git@github.com:dnutiu/bme680-homekit.git && cd bme680-homekit
sudo apt-get install libavahi-compat-libdnssd-dev
pip3 install -r requirements.txt
```

Run the program once to pair it with your ios. ex:

```bash
python3 main.py 
Setup payload: X-HM://0023K50QET2YB
Scan this code with your HomeKit app on your iOS device:

Or enter this code in your HomeKit app on your iOS device: 053-86-998

```

Copy the systemd service.

```bash
sudo cp bme680-homekit.service /etc/systemd/system
sudo systemctl status bme680-homekit
```

```
● bme680-homekit.service - Bme680 Homekit service
     Loaded: loaded (/etc/systemd/system/bme680-homekit.service; disabled; vendor preset: enabled)
     Active: inactive (dead)
```

Start the service
```bash
sudo systemctl start bme680-homekit
sudo systemctl status bme680-homekit
```

```
● bme680-homekit.service - Bme680 Homekit service
     Loaded: loaded (/etc/systemd/system/bme680-homekit.service; disabled; vendor preset: enabled)
     Active: active (running) since Mon 2022-02-21 20:10:30 GMT; 935ms ago
   Main PID: 1722 (python3)
      Tasks: 1 (limit: 780)
        CPU: 895ms
     CGroup: /system.slice/bme680-homekit.service
             └─1722 /usr/bin/python3 /home/pi/bme680-homekit/main.py

Feb 21 20:10:30 raspberrypi systemd[1]: Started Bme680 Homekit service.
```