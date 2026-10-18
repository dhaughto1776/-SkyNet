# New Guy with all we need

# Import Libraries
import smbus2
from time import sleep
import math

# Library for Tilt Compensation
from math import atan2, pi
import struct, time

# Our GY-271 address is 0x0d

# Defining Register Addresses
C_REG_A = 0x09 # Address of Configuration register A
C_REG_B = 0x0a # Address of configuration register B
SR_period_REG = 0x0b # Address of SER/RESET register

MODE_STBY = 0x00 # standby mode
MODE_CONT = 0x01 # continous mode

ODR_10Hz = 0x00 # output data rate 10Hz
ODR_50Hz = 0x01 # output data rate 50Hz
ODR_100Hz = 0x10 # output data rate 100Hz
ODR_200Hz = 0x11 # output data rate 200Hz

SENS_2G = 0x00 # magnetic field sensitivity 2G
SENS_8G = 0x01 # magnetic field sensitivity 8G

OSR_512 = 0x00 # oversampling rate 512
OSR_256 = 0x01 # oversampling rate 256
OSR_128 = 0x10 # oversampling rate 128
OSR_64 = 0x11 # oversampling rate 64

X_axis_H = 0x00 # Address of X-axis MSB data register
Z_axis_H = 0x02 # Address of Z-axis MSB data register
Y_axis_H = 0x04 # Address of Y-axis MSB data register
TEMP_REG = 0x07 # Address of Temperature MSB data register

# declination angle of location where measurement going to be done
CURR_DECL = -1.5    # averaged from not NOAA website
pi = 3.14159265359  # define pi value


class GY271:
  ## Initialization and Read Data Functions (Using I2C)
    def __init__(self, address=0x0d, mode=MODE_CONT, odr=ODR_10Hz, sens=SENS_2G, osr=OSR_512, d=CURR_DECL):
        self.bus = smbus2.SMBus(1)
        self.device_address = address # magnetometer device i2c address
        self._declination = d
        self.data = [0, 0, 0]

        self.mag_x_offset = 0
        self.mag_y_offset = 0
        self.mag_z_offset = 0
        self.mag_x_scale = 1.0
        self.mag_y_scale = 1.0
        self.mag_z_scale = 1.0

        self.magnetometer_init(mode, odr, sens, osr)
        sleep(0.1)

    def soft_reset(self):
        self.bus.write_byte_data(self.device_address, C_REG_B, 0x80)

    def __set_mode(self, mode, odr, sens, osr):
        value = mode | odr  | sens | osr
        return value

    def magnetometer_init(self, mode, odr, sens, osr):
        self.soft_reset()
        sleep(0.01)
        self._mode = self.__set_mode(mode, odr, sens, osr)

        # Write to Configuration Register B: normal 0x00, soft_reset: 0x80
        self.bus.write_byte_data(self.device_address, C_REG_B, 0x00)

        # SET/RESET period set to 0x01 (recommendation from datasheet)
        self.bus.write_byte_data(self.device_address, SR_period_REG, 0x01)

        # write to Configuration Register A: mode
        self.bus.write_byte_data(self.device_address, C_REG_A, self._mode)

    def __read_raw_data(self, reg_address):
        # Read raw 16-bit value
        low_byte = self.bus.read_byte_data(self.device_address, reg_address)
        high_byte = self.bus.read_byte_data(self.device_address, reg_address + 1)

        # concatenate high_byte and low_byte into two_byte data
        value = (high_byte << 8) | low_byte

        if value > 32767:
            value = value - 65536

        return value

        # PLACEHOLDER FUNC TO BE REPLACED W ACTUAL MAGNETOMETER READING FUNCTION (which i presume we have somewhere...?)

    def read_magnetometer(self):
        """Read and return calibrated magnetometer data [x, y, z]"""
        data = self.bus.read_i2c_block_data(self.device_address, X_axis_H, 6)

        x = (data[1] << 8) | data[0]
        y = (data[3] << 8) | data[2]
        z = (data[5] << 8) | data[4]

        if x > 32767:
         x -= 65536
        if y > 32767:
         y -= 65536
        if z > 32767:
         z -= 65536

        # Apply calibration
        x = (x - self.mag_x_offset) * self.mag_x_scale
        y = (y - self.mag_y_offset) * self.mag_y_scale
        z = (z - self.mag_z_offset) * self.mag_z_scale

        x = -y
        y = -x
        z = z

        return [x, y, z]

    def _update_data(self):
      """ Update internal magnetometer data"""
      self.data = self.read_magnetometer()
      return True

    def set_calibration(self, x_offset, y_offset, z_offset, x_scale=1.0, y_scale=1.0, z_scale=1.0):
        """Set calibration values"""
        self.mag_x_offset = x_offset
        self.mag_y_offset = y_offset
        self.mag_z_offset = z_offset
        self.mag_x_scale = x_scale
        self.mag_y_scale = y_scale
        self.mag_z_scale = z_scale

    def normaliser(self, vector):
      v1, v2, v3 = vector
      length = (v1*v1 + v2*v2 + v3*v3)**(1/2)

      if length == 0:
            return [0, 0, 0]

      return [v1/length, v2/length, v3/length]

  ## Tilt Compensation
    def _quat_rotate_mag_readings(self, q):
        qw, qx, qy, qz = q
        mx, my, mz = self.normaliser(self.data)

        # Rotate magnetometer vector into world reference frame
        rx = (qw*qw + qx*qx - qy*qy - qz*qz)*mx + 2*(qx*qy - qw*qz)*my + 2*(qx*qz + qw*qy)*mz
        ry = 2*(qx*qy + qw*qz)*mx + (qw*qw - qx*qx + qy*qy - qz*qz)*my + 2*(qy*qz - qw*qx)*mz

        return rx, ry

    def _world_heading_vector(self, q):
        qw, qx, qy, qz = q
        local_heading = [-1, 0, 0]

        # Using quaternion rotation to find the world x/y heading vector
        wx = (qw*qw + qx*qx - qy*qy - qz*qz)*local_heading[0] + 2*(qx*qy - qw*qz)*local_heading[1] + 2*(qx*qz + qw*qy)*local_heading[2]
        wy = 2*(qx*qy + qw*qz)*local_heading[0] + (qw*qw - qx*qx + qy*qy - qz*qz)*local_heading[1] + 2*(qy*qz - qw*qx)*local_heading[2]

        return wx, wy

    def compass_3d(self, quat, declination=0):
        """
        Fully pitch and roll compensated compass, which is accurate at all orientations of the sensor. North is taken as the negative x-axis.

        Required parameter: Quaternion orientation of the sensor - formatted as a list [qw, qx, qy, qz]
        Optional parameter: Magnetic declination (input as degrees, e.g. 1.5), which is different in every location. Default value is 0. If declination is given, then the output heading will be a true heading, instead of magnetic.

        Outputs a compass heading rounded to the nearest degree.
        """

        flag = self._update_data()

        rx, ry = self._quat_rotate_mag_readings(quat) # Magnetic north direction vector - vector=[rx, ry, 0]

        wx, wy = self._world_heading_vector(quat) # Device forward direction vector - vector=[wx, wy, 0]
        dot_product = rx*wx + ry*wy # Dot product between the world heading vector and magnetic north direction vector
        cross_product_z = rx*wy - ry*wx # Cross product z component (x and y are 0)

        heading = (atan2(cross_product_z, dot_product) * (180/pi) - declination - 48)
        # Heading calc maths: cross product = |a|*|b|*sin(theta), dot product = |a|*|b|*cos(theta), so atan(crossproduct/dotproduct)=atan(sin(theta)/cos(theta))=atan(tan(theta))=theta

        # Ensuring heading goes from 0-360 degrees
        heading %= 360

        return int(heading+0.5) # Rounds to nearest degree
      
if __name__ == "__main__":
    print("GY-271 Magnetometer Test") 
    try:
        # Initialize magnetometer at I2C address 0x0d
        mag = GY271(address=0x0d)
        print("GY-271 initialized")
        print()
        
        # Test reading raw magnetometer data
        print("Reading magnetometer...")
        i = 0
        while True:
            mag_data = mag.read_magnetometer()
            x, y, z = mag_data
            print(f"Reading #{i+1}: X={x:.2f}, Y={y:.2f}, Z={z:.2f}")
            i += 0
            sleep(0.5)
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
          
