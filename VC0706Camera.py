import serial
import queue
from threading import Thread
from time import sleep

class VC0706Camera(Thread):
    def __init__(self, port:str, baudrate:int, packet_len:int=65536):
        Thread.__init__(self)
        self.ser = serial.Serial(port, baudrate, timeout=5)
        self.packet_len = packet_len
        self.jpeg_data = [None, None]
        self.jpeg_data_idx = 0
        self.new_data_available = False
        self._is_running = False
        self.callback_queue = queue.Queue()
        self._init_camera()

    def _cmd_rw(self, cmd:list, expected_resp:list, fail_msg:str, return_len:int = 0):
        self.ser.flushInput()
        cmd = bytes(cmd)
        expected_len = len(expected_resp)
        expected_resp = bytes(expected_resp)
        self.ser.write(cmd)
        resp = self.ser.read(expected_len)
        if resp != expected_resp:
            print('Received:')
            for i in resp:
                print(hex(i), end=' ')
            print('\nExpected:')            
            for i in expected_resp:
                print(hex(i), end=' ')
            print()
            raise Exception(fail_msg)
        return None if return_len <= 0 else self.ser.read(return_len)

    def _init_camera(self):
        # 初始化摄像头
        self._cmd_rw(
            [0x56, 0x00, 0x26, 0x00],
            [0x76, 0x00, 0x26, 0x00],
            'Failed to initialize camera'
        )
        sleep(2.5)
    
    def set_size(self, size:str):
        cmd = [0x56, 0x00, 0x31, 0x05, 0x04, 0x01, 0x00, 0x19]
        if size=='640x480':
            cmd.append(0x00)
        elif size=='320x240':
            cmd.append(0x11)
        elif size=='160x120':
            cmd.append(0x22)
        else:
            raise ValueError('Parameter is illegal')
        self._cmd_rw(
            cmd,
            [0x76, 0x00, 0x31, 0x00, 0x00],
            'Failed to set size'
        )
        self._init_camera()

    def set_compress_rate(self, rate:int):
        self._cmd_rw(
            [0x56, 0x00, 0x31, 0x05, 0x01, 0x01, 0x12, 0x04, rate],
            [0x76, 0x00, 0x53, 0x00, 0x00],
            'Failed to set compress rate'
        )

    def flush_data(self):
        self._cmd_rw(
            [0x56, 0x00, 0x36, 0x01, 0x03],
            [0x76, 0x00, 0x36, 0x00, 0x00],
            'Failed to flush data'
        )

    def capture_and_get_size(self):
        # 拍照并获取图片
        self._cmd_rw(
            [0x56, 0x00, 0x36, 0x01, 0x00],
            [0x76, 0x00, 0x36, 0x00, 0x00],
            'Failed to take picture'
        )
        # 查询图片大小
        size = self._cmd_rw(
            [0x56, 0x00, 0x34, 0x01, 0x00],
            [0x76, 0x00, 0x34, 0x00, 0x04],
            'Failed to query picture size',
            4
        )
        return (size[2] << 8) + size[3]
    
    def recv_data(self, recv_len:int):
        print(f'Ready to receive {recv_len} bytes')
        data = b''
        start_idx = 0
        while start_idx < recv_len:
            print(f'Receiving {start_idx} / {recv_len}')
            r_len = min(recv_len - start_idx, self.packet_len)
            packet_data = self._cmd_rw(
                [0x56, 0x00, 0x32, 0x0C, 0x00, 0x0A, 0x00, 0x00] + 
                [start_idx >> 8, start_idx & 0xFF, 0x00, 0x00] + 
                [r_len >> 8, r_len & 0xFF, 0x00, 0xFF],
                [0x76, 0x00, 0x32, 0x00, 0x00],
                f'Failed to read picture data @{start_idx}',
                r_len + 5
            )
            data += packet_data[:-5]
            start_idx += r_len
        self.jpeg_data[self.jpeg_data_idx] = data
        self.jpeg_data_idx = 1 - self.jpeg_data_idx
        self.new_data_available = True

    def get_jpeg_data(self):
        self.new_data_available = False
        return self.jpeg_data[1 - self.jpeg_data_idx]
    
    def has_new_data(self):
        return self.new_data_available

    def run(self):
        max_error_count = 3
        now_error_count = 0
        self._is_running = True
        while self._is_running:
            try:
                if now_error_count >= max_error_count:
                    self._init_camera()
                size = self.capture_and_get_size()
                self.recv_data(size)
                self.flush_data()
                now_error_count = 0
                while not self.callback_queue.empty():
                    func = self.callback_queue.get()
                    func()           
            except Exception as e:
                print(str(e))
                now_error_count += 1
                sleep(5)

    def add_callback(self, func):
        self.callback_queue.put(func)

    def stop(self):
        self._is_running = False
        self.close()

    def close(self):
        self.ser.close()
