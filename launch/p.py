import RPI.GPIO as GPIO
import serial
import time

PIN_SENSOR = 22  # пин датчика
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_SENSOR, GPIO.IN)

motor1 = Motor(forward=17, backward=27)
motor2 = Motor(forward=5, backward=6)

LOBOT_SERVO_FRAME_HEADER = 0x55
LOBOT_SERVO_MOVE_TIME_WRITE = 1


def get_low_byte(value):
    return value & 0xFF


def get_high_byte(value):
    return (value >> 8) & 0xFF


def byte_to_hw(high_byte, low_byte):
    return (high_byte << 8) | low_byte


def lobot_checksum(buf):
    temp = 0
    for i in range(2, buf[3] + 2):
        temp += buf[i]
    temp = ~temp & 0xFF
    return temp


def lobot_serial_servo_move(serial_port, servo_id, position, move_time):
    if position < 0:
        position = 0
    if position > 1000:
        position = 1000

    buf = bytearray(10)
    buf[0] = buf[1] = LOBOT_SERVO_FRAME_HEADER
    buf[2] = servo_id
    buf[3] = 7
    buf[4] = LOBOT_SERVO_MOVE_TIME_WRITE
    buf[5] = get_low_byte(position)
    buf[6] = get_high_byte(position)
    buf[7] = get_low_byte(move_time)
    buf[8] = get_high_byte(move_time)
    buf[9] = lobot_checksum(buf)

    serial_port.write(buf)


serial_port = serial.Serial(port="/dev/ttyS0", baudrate=115200, timeout=1)
time.sleep(1)

ID1 = 1
ID2 = 2
ID3 = 3
ID5 = 5

try:
    while True:
        if GPIO.input(PIN_SENSOR):
            motor1.stop()
            motor2.stop()

            lobot_serial_servo_move(serial_port, ID2, 350, 1000)
            lobot_serial_servo_move(serial_port, ID1, 500, 1000)
            # time.sleep(2)
            lobot_serial_servo_move(serial_port, ID2, 387, 1000)
            # time.sleep(2)
            lobot_serial_servo_move(serial_port, ID3, 500, 1000)
            # time.sleep(2)
            lobot_serial_servo_move(serial_port, ID5, 500, 1000)
            time.sleep(5)
            lobot_serial_servo_move(serial_port, ID1, 915, 1000)
            # lobot_serial_servo_move(serial_port, ID5, 70, 3000)
            # time.sleep(2)
            lobot_serial_servo_move(serial_port, ID2, 230, 1000)
            # time.sleep(3)
            lobot_serial_servo_move(serial_port, ID5, 120, 1000)
            lobot_serial_servo_move(serial_port, ID3, 870, 1000)
            # lobot_serial_servo_move(serial_port, ID5, 180, 3000)
            time.sleep(4)
            lobot_serial_servo_move(serial_port, ID5, 370, 700)
            # time.sleep(2)
            # lobot_serial_servo_move(serial_port, ID1, 500, 700)
            time.sleep(4)
            lobot_serial_servo_move(serial_port, ID2, 340, 1000)

            # lobot_serial_servo_move(serial_port, ID2, 387, 700)
            # time.sleep(2)
            # lobot_serial_servo_move(serial_port, ID3, 490, 700)
            # time.sleep(2)
            # lobot_serial_servo_move(serial_port, ID4, 493, 700)
            time.sleep(10)

        else:
            motor1.forward()
            motor2.forward()

except KeyboardInterrupt:
    print("Program is stopped")
    serial_port.close()
    GPIO.cleanup()