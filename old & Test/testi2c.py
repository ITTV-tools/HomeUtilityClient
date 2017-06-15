import smbus
import time
 
#bus = smbus.SMBus(0) # Rev 1 Pi
bus = smbus.SMBus(1) # Rev 2 Pi
 
DEVICE = 0x20 # Device Adresse (A0-A2)
IODIRA = 0x00 # Pin Register fuer die Richtung
IODIRB = 0x01 # Pin Register fuer die Richtung
OLATA = 0x14 # Register fuer Ausgabe (GPA)
OLATB = 0x15 # Register fuer Ausgabe (GPB)
GPIOA = 0x12 # Register fuer Eingabe (GPA)
GPIOB = 0x13 # Register fuer Eingabe (GPB)

# Definiere GPA Pin 7 als Output (10000000 = 0x80)
# Binaer: 0 bedeutet Output, 1 bedeutet Input
bus.write_byte_data(DEVICE,IODIRA,0x7F)
bus.write_byte_data(DEVICE,IODIRB,0x00)
 
# Definiere alle GPB Pins als Output (00000000 = 0x00)
#bus.write_byte_data(DEVICE,IODIRB,0x00)
 
# Setze alle 7 Output bits auf 0
bus.write_byte_data(DEVICE,OLATA,0x00)
bus.write_byte_data(DEVICE,OLATB,0x00)

 

