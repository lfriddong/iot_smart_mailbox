# iot_smart_mailbox
iot anti-theft smart mailbox project

ESP8266
```bash
esptool.py erase_flash
```
```bash
esptool.py --baud 460800 write_flash --flash_size=detect 0 ESP8266_GENERIC-20230426-v1.20.0.bin
```
```bash
mpfshell -nc "open tty.usbserial-028618B4; mput main.py"
```


ESP32-CAM
```bash
esptool.py --port /dev/cu.usbserial-110 erase_flash
```

```bash
esptool.py --chip esp32 --port /dev/cu.usbserial-110 write_flash -z 0x1000 ESP32_GENERIC-20231005-v1.21.0.bin
```

```bash
mpfshell -nc "open tty.usbserial-110; mput main.py"
```
