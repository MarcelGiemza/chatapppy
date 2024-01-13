import socket
import sys
from threading import Thread
import tkinter
import re


socket.SO_REUSEADDR

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

do_recv = True  # When False the receiving thread will close


window = tkinter.Tk()
window.geometry("400x400")
window.title("Chat.py")


def on_close(event=None):  # Called when closed
    print("closing.")
    window.destroy()
    exit()


# Call on_close() when closed; TODO: test on Windows and MacOS VM
window.protocol("WM_DELETE_WINDOW", on_close)

port = tkinter.StringVar()
port.set("")
address = tkinter.StringVar()
address.set("")

def chat(do_connect, port, address="localhost"):
    for child in window.winfo_children():
        child.destroy()

    msg_box = tkinter.Frame(window)
    msg_scrollbar = tkinter.Scrollbar(msg_box)
    msg_list = tkinter.Listbox(msg_box, yscrollcommand=msg_scrollbar.set)
    msg_scrollbar.config(command=msg_list.yview)
    msg_value = tkinter.StringVar()
    msg_value.set("")
    msg_input_field = tkinter.Entry(window, textvariable=msg_value)

    def recv_builder(c):
        def recv():
            while do_recv:
                data = c.recv(1024).decode()
                if not data:
                    sys.exit(0)
                msg_list.insert(tkinter.END, f"Received: {data}")
                print("Received:", data)
            return
        return recv

    def send_builder(c):
        def send(event=None):
            data = msg_value.get()
            if data:
                msg_list.insert(tkinter.END, f"Sent: {data}")
                c.send(data.encode())
                msg_value.set("")
        return send

    send = None

    if do_connect:
        s.connect((address, port))
        msg_list.insert(tkinter.END, f"Connected to: {address}:{port}")

        # Create thread for receiving
        recv_thread = Thread(target=recv_builder(s), daemon=True)

        send = send_builder(s)

    else:
        s.bind((address, port))
        s.listen(1)
        conn, addr = s.accept()
        msg_list.insert(tkinter.END, f"Connected: {addr[0]}")

        # Create thread for receiving
        recv_thread = Thread(target=recv_builder(conn), daemon=True)

        send = send_builder(conn)

    recv_thread.start()
    msg_input_field.bind("<Return>", send)
    msg_input_button = tkinter.Button(window, command=send, text=">")
    msg_box.place(relwidth=1, relheight=.9)
    msg_scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
    msg_list.place(relwidth=.9, relheight=1)
    msg_input_field.place(rely=.95, relwidth=.9, anchor="w", height=25)
    msg_input_button.place(
        rely=.95, relx=.9, relwidth=0.1, anchor="w", height=25)


def chat_connect():
    pattern = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )
    port_val = port.get()
    address_val = address.get()
    if port_val.isnumeric() and int(port_val) > 0 and int(port_val) < 65535\
            and pattern.match(address_val):
        port.set("")
        chat(True, int(port_val), address_val)


def chat_host():
    port_val = port.get()
    if port_val.isnumeric() and int(port_val) > 0 and int(port_val) < 65535:
        print(f"Hosting on port: {port_val}")
        port.set("")
        chat(False, int(port_val))


def host():
    for child in window.winfo_children():
        child.destroy()

    box = tkinter.Frame(window)

    input_port = tkinter.Entry(box, textvariable=port)
    
    buttons_box = tkinter.Frame(box)
    button_back = tkinter.Button(buttons_box, text="Back", command=menu)
    button_host = tkinter.Button(
        buttons_box, text="Host", command=chat_host
        )
    input_port.place(relheight=.3, relwidth=1)
    box.place(width=150, height=100, anchor="center", relx=.5, rely=.5)
    buttons_box.place(relheight=.3, relwidth=1, anchor="sw", rely=1)
    button_back.place(relwidth=.4, relheight=1)
    button_host.place(relwidth=.4, relheight=1, anchor="ne", relx=1)


def connect():
    for child in window.winfo_children():
        child.destroy()

    box = tkinter.Frame(window)

    input_port = tkinter.Entry(box, textvariable=port)
    input_address = tkinter.Entry(box, textvariable=address)
    
    buttons_box = tkinter.Frame(box)
    button_back = tkinter.Button(buttons_box, text="Back", command=menu)
    button_host = tkinter.Button(buttons_box, text="Connect", command=chat_connect)
    input_port.place(relheight=.3, relwidth=1, anchor="w", rely=.5)
    input_address.place(relwidth=1, relheight=.3)
    box.place(width=150, height=100, anchor="center", relx=.5, rely=.5)
    buttons_box.place(relheight=.3, relwidth=1, anchor="sw", rely=1)
    button_back.place(relwidth=.4, relheight=1)
    button_host.place(relwidth=.4, relheight=1, anchor="ne", relx=1)


def menu():
    for child in window.winfo_children():
        child.destroy()

    buttons_box = tkinter.Frame(window)
    button_host = tkinter.Button(buttons_box, text="Host", command=host)
    button_connect = tkinter.Button(
        buttons_box, text="Connect", command=connect)
    buttons_box.place(height=100, width=150, anchor="center", relx=.5, rely=.5)
    button_host.place(relwidth=1, relheight=.4)
    button_connect.place(relwidth=1, relheight=.4, anchor="sw", rely=1)


menu()
tkinter.mainloop()
