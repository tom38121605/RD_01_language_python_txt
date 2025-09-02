import time
import threading
import serial  # 导入模块
import serial.tools.list_ports
import re

class my_serial_class():
    serial_obj = None
    serial_port = 'COM1'
    serial_baud = 115200
    time_out = 5
    port_list = []  # 端口列表
    serial_open_flag = 0  # 串口打开标志

    def __init__(self):
        pass

    # 获取串口列表
    def get_serial_port_list(self):
        port_list_msg = list(serial.tools.list_ports.comports())  # 获取串口列表

        if len(port_list_msg) == 0:
            print('无可用串口')
        else:
            print('打印串口列表')
            cnt = 0
            for x in port_list_msg:
                print('{:2d}:   '.format(cnt) + str(x))
                cnt += 1
                # 取括号里的值
                temp_list = re.findall(r'[(](.*?)[)]', str(x))
                # print(type(temp_list))
                # print('temp = ', temp_list)
                self.port_list.append(temp_list[0])
            # print(self.port_list)

    # 打开端口
    def open_serial_port_list(self, port='COM1', baud=115200, timex=5):

        self.get_serial_port_list()  # 获取串口列表

        #  如果没有串口返回
        if len(self.port_list) == 0:
            print('Error: 没有可用串口！')
            return 0

        print('串口端口')
        print(self.port_list)
        print(port)

        if port in self.port_list:
            try:
                # 端口，GNU / Linux上的/ dev / ttyUSB0 等 或 Windows上的 COM3 等
                self.serial_port = port
                # 波特率，标准值之一：50,75,110,134,150,200,300,600,1200,1800,2400,4800,9600,19200,38400,57600,115200
                self.serial_baud = baud
                # 超时设置,None：永远等待操作，0为立即返回请求结果，其他值为等待超时时间(单位为秒）
                self.time_out = timex
                # 打开串口，并得到串口对象
                self.serial_obj = serial.Serial(self.serial_port, self.serial_baud, timeout=self.time_out)
                self.serial_open_flag = 1  # 打开串口标志
                # 写数据
                # result = self.serial_obj.write("123456".encode("gbk"))
                # print("写总字节数:", result)
            except Exception as e:
                print("Error: 串口打开失败，", e)
                return 0
        else:
            print('Error: 端口输入错误，请重新输入！')
            return 0

        return 1

    # 关闭串口
    def close_serial_port(self):
        self.serial_open_flag = 0  # 打开串口标志 关闭
        self.serial_obj.close()  # 关闭串口

    # 串口接收线程
    def serial_receive_thread(self):
        print('serial_port_receives_thread(); Create succeed!')

        while True:
            # 判断串口是否打开
            if self.serial_open_flag != 0:
                try:
                    time.sleep(0.001)

                    # 判断有没有数据
                    if self.serial_obj.in_waiting:
                        # str_a = serial_obj.read(serial_obj.in_waiting).decode("gbk")

                        # ========================== 字符串接收显示  ==============================
                        # 字符串接收 decode 的作用是吧bytes转成字符串
                        # rx_msg = self.serial_obj.read(self.serial_obj.in_waiting).decode("UTF-8")
                        # print(rx_msg)

                        # ========================== 字节接收显示  ==============================
                        # 字节几首显示
                        rx_msg = self.serial_obj.read(self.serial_obj.in_waiting)  # decode 的作用是吧bytes转成字符串
                        rx_msg_list = list(rx_msg)
                        for x in rx_msg_list:
                            print('0x{:02X} '.format(x))


                except Exception as e:
                    print('Error: 接收错误', e)
                    time.sleep(2)
            else:
                time.sleep(0.1)

    # 创建接收线程
    def receives_thread_create(self):
        try:
            recv_thread = threading.Thread(target=self.serial_receive_thread)
            recv_thread.start()
            time.sleep(0.01)
        except Exception as e:
            print('Error: 串口创建接收线程失败！', e)

    # 串口发送字符串
    def send_string(self, srt_data):
        try:
            if self.serial_obj.is_open:
                send_len = self.serial_obj.write(srt_data.encode("utf-8"))
                return send_len
            else:
                print('串口不存在或者关闭！')
        except Exception as e:
            print('Error: serial send_string() send fail; ', e)

    # 串口发送一个二进制
    def send_one_hex(self, hex_data):
        try:
            if self.serial_obj.is_open:

                x = hex_data.to_bytes(1, byteorder='little', signed=False)
                # x = chr(hex_data).encode("utf-8")
                send_len = self.serial_obj.write(x)
                return send_len
            else:
                print('串口不存在或者关闭！')
        except Exception as e:
            print('Error: serial send_one_hex() send fail; ', e)

    # 串口发送二进制列表
    def send_hex_list(self, hex_list):
        try:
            if self.serial_obj.is_open:
                x = bytes(hex_list)
                # print(x)
                send_len = self.serial_obj.write(x)
                return send_len
            else:
                print('串口不存在或者关闭！')
        except Exception as e:
            print('Error: serial send_one_hex() send fail; ', e)

    # 列表转 列表格式字符串
    def list_to_hex_string(shlf, list_data):
        list_str = '[ '
        for x in list_data:
            list_str += '0x{:02X},'.format(x)
        list_str += ' ]'
        return list_str


# 串口接收线程
def serial_port_receives_thread(serial_obj):
    print('serial_port_receives_thread(); Create succeed!')

    while True:
        try:
            # 判断有没有数据
            if serial_obj.in_waiting:
                # str_a = serial_obj.read(serial_obj.in_waiting).decode("gbk")
                # 接收的数据转换成字符串显示
                str_a = serial_obj.read(serial_obj.in_waiting).decode("UTF-8")  # decode 的作用是吧bytes转成字符串
                print(str_a)

        except Exception as e:
            print('Error:串口未打开或读取错误！')
            time.sleep(2)


if __name__ == "__main__":
    my_serial_obj = my_serial_class()  # 创建串口对象

    # 打开串口
    my_serial_obj.open_serial_port_list(port='COM17', baud=1000000)  # 配置端口 波特率
    my_serial_obj.receives_thread_create()  # 创建接收线程

    cnt = 0
    while True:
        my_serial_obj.send_string("cnt = " + cnt.__str__() + '\r\n')  # 发送字符串
        # serial_port_obj.send_one_hex(255)                                     # 发送一个字节
        # serial_port_obj.send_hex_list([0x11, 0xaa, 0xff])                     # 发送一个字节列表
        cnt += 1
        time.sleep(1)
        print('cnt = ', cnt)
