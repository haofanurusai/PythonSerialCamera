import tkinter as tk
import serial.tools.list_ports

class SerialPortSelector:
    def __init__(self, parent):
        self.parent = parent
        self.selected_port = None
        self.selected_baudrate = None

        # 创建窗口组件
        self.label = tk.Label(self.parent, text='Please select COM port:')
        self.listbox = tk.Listbox(self.parent)
        self.baudrate_label = tk.Label(self.parent, text='Baud rate：')
        self.baudrate_var = tk.StringVar(value='38400')
        self.baudrate_menu = tk.OptionMenu(self.parent, self.baudrate_var, '1200', '4800', '9600', '19200', '38400', '57600', '115200')
        self.button = tk.Button(self.parent, text='OK', command=self._on_button_click)

        # 布局窗口组件
        self.label.pack()
        self.listbox.pack()
        self.baudrate_label.pack()
        self.baudrate_menu.pack()
        self.button.pack()

        # 列出所有可用串口
        self._list_serial_ports()

    def _list_serial_ports(self):
        # 获取所有可用串口
        ports = serial.tools.list_ports.comports()
        ports = [port.device for port in ports]
        
        # 在列表框中显示可用串口
        for port in ports:
            self.listbox.insert(tk.END, str(port))

    def _on_button_click(self):
        # 获取用户选择的串口和波特率
        selection = self.listbox.curselection()
        if len(selection) == 0:
            self.selected_port = None
        else:
            self.selected_port = str(self.listbox.get(selection[0]))
        self.selected_baudrate = int(self.baudrate_var.get())
        self.parent.destroy()

if __name__=='__main__':
    # 示例用法
    root = tk.Tk()
    selector = SerialPortSelector(root)
    root.mainloop()

    # 用户选择的串口和波特率
    selected_port = selector.selected_port
    selected_baudrate = int(selector.selected_baudrate)
    print('Selected port:', selected_port)
    print('Selected baudrate:', selected_baudrate)
