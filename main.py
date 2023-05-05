import time
import tkinter as tk
from io import BytesIO
from PIL import Image, ImageTk
from threading import Thread
from SerialPortSelector import SerialPortSelector
from VC0706Camera import VC0706Camera

cam = None
img_tk = None
label = None

display_flag = True
save_flag = True

def show_jpeg():
    global label
    label.config(image=img_tk)
    label.image = img_tk
    label.after(100, show_jpeg)

def display_image():
    global cam
    global img_tk
    global display_flag
    global save_flag
    while display_flag:
        if cam.has_new_data():
            jpeg_data = cam.get_jpeg_data()
            if save_flag:
                with open(f'./img/{int(time.time()*1000)}.jpg','wb') as f:
                    f.write(jpeg_data)
            img = Image.open(BytesIO(jpeg_data))
            img_tk = ImageTk.PhotoImage(img.resize((1280, 960)))
        else:
            time.sleep(0.1)

def terminate():
    global cam
    global display_flag
    display_flag = False
    cam.stop()

def set640x480():
    global cam
    cam.add_callback(lambda: cam.set_size('640x480'))

def set320x240():
    global cam
    cam.add_callback(lambda: cam.set_size('320x240'))

def set160x120():
    global cam
    cam.add_callback(lambda: cam.set_size('160x120'))

if __name__=='__main__':
    root = tk.Tk()
    selector = SerialPortSelector(root)
    root.mainloop()

    cam = VC0706Camera(port=selector.selected_port, baudrate=int(selector.selected_baudrate), packet_len=984)
    cam.start()
    Thread(target=display_image).start()

    try:
        root = tk.Tk()
        img = Image.open('./bg.png')
        img_tk = ImageTk.PhotoImage(img)
        label = tk.Label(root)
        label.pack()
        button1 = tk.Button(root, text='SetResolution640x480', command=set640x480)
        button1.pack()
        button2 = tk.Button(root, text='SetResolution320x240', command=set320x240)
        button2.pack()
        button3 = tk.Button(root, text='SetResolution160x120', command=set160x120)
        button3.pack()
        show_jpeg()
        root.mainloop()
    except KeyboardInterrupt:
        terminate()
