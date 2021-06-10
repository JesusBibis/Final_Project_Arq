import time
import requests
import math
import random
import serial
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import subprocess

import smbus			#import SMBus module of I2C
from time import sleep          #import


TOKEN = "BBFF-nBvuz7N7aUNmmw6jVqt2OJZOa6zY5O"  # Put your TOKEN here
DEVICE_LABEL = "Raspi"  # Put your device label here 
VARIABLE_LABEL_1 = "temperature"  # Put your first variable label here
VARIABLE_LABEL_2 = "humidity"  # Put your second variable label here
VARIABLE_LABEL_3 = "position"  # Put your second variable label here
s= serial.Serial('/dev/ttyACM0', 9600)
s.flush()
# Raspberry Pi pin configuration:
RST = None     # on the PiOLED this pin isnt used
# Note the following are only used with SPI:
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0


# Beaglebone Black pin configuration:
# RST = 'P9_12'-s
# Note the following are only used with SPI:
# DC = 'P9_15'
# SPI_PORT = 1
# SPI_DEVICE = 0

# 128x64 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)

# Initialize library.
disp.begin()
    
# Clear display.
disp.clear()
disp.display()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0,0,width,height), outline=0, fill=0)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Load default font.
font = ImageFont.load_default()


PWR_MGMT_1   = 0x6B
SMPLRT_DIV   = 0x19
CONFIG       = 0x1A
GYRO_CONFIG  = 0x1B
INT_ENABLE   = 0x38
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F
GYRO_XOUT_H  = 0x43
GYRO_YOUT_H  = 0x45
GYRO_ZOUT_H  = 0x47


def MPU_Init():
	#write to sample rate register
	bus.write_byte_data(Device_Address, SMPLRT_DIV, 7)
	
	#Write to power management register
	bus.write_byte_data(Device_Address, PWR_MGMT_1, 1)
	
	#Write to Configuration register
	bus.write_byte_data(Device_Address, CONFIG, 0)
	
	#Write to Gyro configuration register
	bus.write_byte_data(Device_Address, GYRO_CONFIG, 24)
	
	#Write to interrupt enable register
	bus.write_byte_data(Device_Address, INT_ENABLE, 1)
 
def read_raw_data(addr):
	#Accelero and Gyro value are 16-bit
    high = bus.read_byte_data(Device_Address, addr)
    low = bus.read_byte_data(Device_Address, addr+1)
    
    #concatenate higher and lower value
    value = ((high << 8) | low)
        
    #to get signed value from mpu6050
    if(value > 32768):
        value = value - 65536
    return value
        
bus = smbus.SMBus(1) 	# or bus = smbus.SMBus(0) for older version boards
Device_Address = 0x68   # MPU6050 device address

MPU_Init()


def build_payload(variable):
    
    print(3)
    if variable == 1:
     comando = 'T'
     s.write('T')
     print(6)
     variable_1 = VARIABLE_LABEL_1
     print(7)
     msg1= float(s.readline())
     print('T')
     print(msg1)
     refresh_display(variable, msg1)
     payload = {variable_1: msg1}
    elif variable == 2:
     variable_2 = VARIABLE_LABEL_2
     comando = 'H'
     s.write(comando)
     msg2 = float(s.readline())
     print('H')
     print(msg2)
     refresh_display(variable, msg2)
     payload = {variable_2: msg2}
    else:
     variable_3 = VARIABLE_LABEL_3
     acc_z = read_raw_data(ACCEL_ZOUT_H)
     Az = round(acc_z/16384.00, 4)
     print('Az')
     print(Az)
     refresh_display(variable, Az)
     payload = {variable_3: Az}
    return payload


def post_request(payload):
    # Creates the headers for the HTTP requests
    url = "http://industrial.api.ubidots.com"
    url = "{}/api/v1.6/devices/{}".format(url, DEVICE_LABEL)
    headers = {"X-Auth-Token": TOKEN, "Content-Type": "application/json"}
        
    # Makes the HTTP requests
    status = 400
    attempts = 0
    while status >= 400 and attempts <= 5:
        req = requests.post(url=url, headers=headers, json=payload)
        status = req.status_code
        attempts += 1
        time.sleep(1)

    # Processes results
    print(req.status_code, req.json())
    if status >= 400:
        print("[ERROR] Could not send data after 5 attempts, please check \
            your token credentials and internet connection")
        return False

    print("[INFO] request made properly, your device is updated")
    return True

def refresh_display(var, mensaje):
	# Draw a black filled box to clear the image. 
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    
    if var == 1:
     draw.text((x, top),      "Temperatura ",  font=font, fill=255)
     draw.text((x, top+8),    str(mensaje), font=font, fill=255)
     draw.text((x, top+16),   "Humedad ",  font=font, fill=255)
     draw.text((x, top+24),   "0", font=font, fill=255)
     draw.text((x, top+32),   "Accel Z ",  font=font, fill=255)
     draw.text((x, top+40),   "0", font=font, fill=255)
     # Display image.
     disp.image(image)
     disp.display()
     time.sleep(.1)
    elif var == 2:
     draw.text((x, top),      "Temperatura ",  font=font, fill=255)
     draw.text((x, top+8),    "0", font=font, fill=255)
     draw.text((x, top+16),   "Humedad ",  font=font, fill=255)
     draw.text((x, top+24),   str(mensaje), font=font, fill=255)
     draw.text((x, top+32),   "Accel Z ",  font=font, fill=255)
     draw.text((x, top+40),   "0", font=font, fill=255)
     # Display image.
     disp.image(image)
     disp.display()
     time.sleep(.1)
    else:
     draw.text((x, top),      "Temperatura ",  font=font, fill=255)
     draw.text((x, top+8),    "0", font=font, fill=255)
     draw.text((x, top+16),   "Humedad ",  font=font, fill=255)
     draw.text((x, top+24),   "0", font=font, fill=255)
     draw.text((x, top+32),   "Accel Z ",  font=font, fill=255)
     draw.text((x, top+40),   str(mensaje), font=font, fill=255)
     # Display image.
     disp.image(image)
     disp.display()
     time.sleep(.1)
     
     




def main():
    print(2)
    comando = 'T'
    s.write('T')
    msg1= float(s.readline())
    print('T')
    print(msg1)

    
    payload = build_payload(1)
    print("[INFO] Attemping to send "+str(VARIABLE_LABEL_1))
    post_request(payload)
    print("[INFO] finished")
    payload = build_payload(2)
    print("[INFO] Attemping to send "+str(VARIABLE_LABEL_2))
    post_request(payload)
    print("[INFO] finished")
    payload = build_payload(3)
    print("[INFO] Attemping to send "+str(VARIABLE_LABEL_3))
    post_request(payload)
    print("[INFO] finished")
    




if __name__ == '__main__':
    while (True):
        print(1)
        main()
        time.sleep(1)
