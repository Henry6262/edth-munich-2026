# SCOUT — Hardware Checklist for EDTH Munich

## Critical (Must Have)

- [ ] PiCrawler robot (assembled, calibrated)
- [ ] Raspberry Pi 5
- [ ] Official Pi 5 27W USB-C power supply
- [ ] Sony IMX500 AI Camera
- [ ] Standard Pi Camera Module (wide angle)
- [ ] USB robot-eyes / arm camera
- [x] microSD card with Pi OS — flashed + SSH + WiFi ✅
- [x] SD card reader/adapter ✅
- [ ] Laptop (for Flask server + browser dashboards)
- [ ] Phone (for operator app)
- [ ] Pre-recorded 3D pitch video on laptop (backup)

- [ ] Colored electrical tape (patrol path)
- [ ] Cardboard boxes (3 sectors)
- [ ] Black cardboard drone cutout + stick
- [ ] Power bank (20,000mAh with PD)

## Connectivity (Buy at Venue if Missing)

- [ ] SD card reader
- [ ] Ethernet cable
- [ ] micro HDMI cable
- [ ] USB keyboard

## Spares

- [ ] Servos (SunFounder extras)
- [ ] USB-C cables
- [ ] Ribbon cables for cameras
- [ ] Tape refills

## Demo Props

- [ ] RED card (ENEMY)
- [ ] BLUE card (CIVILIAN)
- [ ] YELLOW card (HOSTAGE / FRIENDLY)
- [ ] Small Bluetooth speaker (optional, for alert sounds)

## Setup Notes

1. Power Pi 5 with official PSU, not laptop.
2. Connect cameras:
   - Standard Pi Cam → CSI 0
   - AI Camera → CSI 1
   - USB camera → USB 3.0
3. Connect robot arm/dongle to USB.
4. Configure WiFi at venue or use Ethernet.
5. On the laptop:
   - `python src/video/generate_village.py` to build `static/village.ply`
   - `python src/c2/server.py` to start Flask
   - Open `/admin` and `/3d` in separate browser tabs
   - Open `/operator` on the phone
6. Test robot walking before demo.
7. Take test photos for change detection calibration.
