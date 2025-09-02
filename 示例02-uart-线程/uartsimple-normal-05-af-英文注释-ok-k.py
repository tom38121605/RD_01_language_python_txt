import serial
import time
import serial.tools.list_ports
import threading
import re


text = "aa,bb;123"
pattern = r"[;, ]"
result = re.split(pattern, text)
print("splited:", result)

ports=serial.tools.list_ports.comports()
for port, desc, hwid in sorted(ports):
    # print(f"{port}: {desc} ({hwid})")
    print(f"{port}: {desc} ")

def receive_and_send_data(ser):
    try:
        while True:

            if ser.in_waiting > 0:

                received_data = ser.read(ser.in_waiting)
                print(f"received data: {received_data}")

                ser.write(received_data)

    except serial.SerialException as e:
        print(f"uart receive err: {e}")
    except KeyboardInterrupt:
        print("The uart rx thread is interrupted by the user")


try:

    ser = serial.Serial('COM17', 1000000, timeout=1)
    print(f"Successfully connected: {ser.name}")

    receive_thread = threading.Thread(target=receive_and_send_data, args=(ser,))
    receive_thread.daemon = True
    receive_thread.start()

    while True:
        pass

except serial.SerialException as e:
    print(f"uart connect err: {e}")
except KeyboardInterrupt:
    print("The program was interrupted by the user。")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("uart connection closed")
