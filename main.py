import socket
from threading import Thread
import tkinter
import re
import random
from Crypto.Cipher import Salsa20

MY_IP = "127.0.0.1" # Address for hosting


window = tkinter.Tk()
window.geometry("400x400")
window.title("Chat.py")


def on_close(event=None):  # Called when closed
    print("closing.")
    window.destroy()
    exit()


# Call on_close() when closed
window.protocol("WM_DELETE_WINDOW", on_close)

port = tkinter.StringVar()
port.set("port")
address = tkinter.StringVar()
address.set("address")


def chat(do_host, port, address=""):
    for child in window.winfo_children():
        child.destroy()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


    msg_box = tkinter.Frame(window)
    msg_scrollbar = tkinter.Scrollbar(msg_box)
    msg_list = tkinter.Listbox(msg_box, yscrollcommand=msg_scrollbar.set)
    msg_scrollbar.config(command=msg_list.yview)
    msg_value = tkinter.StringVar()
    msg_value.set("")
    msg_input_field = tkinter.Entry(window, textvariable=msg_value)

    conn = None
    send = None

    def disconnect():
        try:
            conn.send("*Disconnect*".encode())
        except:
            s.send("*Disconnect*".encode())
        s.close()
        try:
            conn.close()
        except:
            pass
        menu()

    def recv_builder(c):
        def recv():
            do_recv = True
            c.settimeout(15)
            while do_recv:
                data = None
                try:
                    data = c.recv(1024)
                except:
                    pass
                if data:
                    if data == "*Disconnect*":
                        do_recv = False
                        disconnect()
                    else:
                        msg_list.insert(tkinter.END, f"Received: {K.decrypt(data)}")
                        print("Received:", data)
            return
        return recv

    def send_builder(c):
        def send(event=None):
            data = msg_value.get()
            if data:
                msg_list.insert(tkinter.END, f"Sent: {data}")
                c.send(K.encrypt(data))
                msg_value.set("")
        return send


    def generate_prime_number():
        """
        Generate a random prime number between 1000 and 10000.
        """
        prime = random.randint(1000, 10000)
        while not is_prime(prime):
            prime = random.randint(1000, 10000)
        return prime


    def is_prime(n):
        """
        Check if a number is prime.
        """
        if n <= 1:
            return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False
        return True
    
    
    def generate_G(P):
        return random.randint(2, P)


    class DHKE:
        def __init__(self,G,P):
            self.G_param = G
            self.P_param = P

        def generate_privatekey(self):
            self.priv_key = random.randint(2, self.P_param - 1)

        def generate_publickey(self):
            self.pub_key = pow(self.G_param, self.priv_key) % self.P_param

        def exchange_key(self,  other_public):
            self.share_key = pow(other_public, self.priv_key) % self.P_param

        def decrypt(self, msg):
            msg_nonce = msg[:8]
            msg_text = msg[8:]
            cipher = Salsa20.new(str(self.share_key).rjust(32).encode(), nonce=msg_nonce)
            return cipher.decrypt(msg_text).decode()


        def encrypt(self, msg):
            cipher = Salsa20.new(str(self.share_key).rjust(32).encode())
            return cipher.nonce + cipher.encrypt(msg.encode())

    if do_host:
        s.bind((MY_IP, port))
        text_wait = tkinter.Label(window, text="Waiting for connection")
        text_wait.place(relx=.5, rely=.5, anchor="center", width=150, height=100)
        window.update()
        s.listen(1)
        conn, addr = s.accept()
        text_wait.destroy()
        msg_list.insert(tkinter.END, f"Connected: {addr[0]}")

        P = generate_prime_number()
        conn.send(str(P).encode())
        G = int(conn.recv(1024).decode())
        msg_list.insert(tkinter.END, f"p = {P}, g = {G}")
        K = DHKE(G, P)
        K.generate_privatekey()
        msg_list.insert(tkinter.END, "Generated private key")
        K.generate_publickey()
        msg_list.insert(tkinter.END, f"Generated public key {K.pub_key}")
        other_public = int(conn.recv(1024).decode())
        conn.send(str(K.pub_key).encode())
        msg_list.insert(tkinter.END, f"Received public key {other_public}")
        K.exchange_key(other_public)
        msg_list.insert(tkinter.END, f"Generated shared key {K.share_key}")

        # Create thread for receiving
        recv_thread = Thread(target=recv_builder(conn), daemon=True)

        send = send_builder(conn)
    else:
        s.connect((address, port))
        msg_list.insert(tkinter.END, f"Connected to: {address}:{port}")

        P = int(s.recv(1024).decode())
        G = generate_G(P)
        s.send(str(G).encode())
        msg_list.insert(tkinter.END, f"p = {P}, g = {G}")
        K = DHKE(G, P)
        K.generate_privatekey()
        msg_list.insert(tkinter.END, "Generated private key")
        K.generate_publickey()
        msg_list.insert(tkinter.END, f"Generated public key {K.pub_key}")
        s.send(str(K.pub_key).encode())
        other_public = int(s.recv(1024).decode())
        msg_list.insert(tkinter.END, f"Received public key {other_public}")
        K.exchange_key(other_public)
        msg_list.insert(tkinter.END, f"Generated shared key {K.share_key}")

        # Create thread for receiving
        recv_thread = Thread(target=recv_builder(s), daemon=True)

        send = send_builder(s)


    recv_thread.start()
    msg_input_field.bind("<Return>", send)
    msg_input_button = tkinter.Button(window, command=send, text=">")
    disconnect_button = tkinter.Button(window, command=disconnect, text="Disconnect")
    msg_box.place(relwidth=1, relheight=.9)
    msg_scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
    msg_list.place(relwidth=.9, relheight=1)
    disconnect_button.place(rely=.95, relwidth=0.1, anchor="w", height=25)
    msg_input_field.place(rely=.95, relx=.1, relwidth=.8, anchor="w", height=25)
    msg_input_button.place(rely=.95, relx=.9, relwidth=0.1, anchor="w", height=25)


def chat_connect():
    pattern = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )
    port_val = port.get()
    address_val = address.get()
    if port_val.isnumeric() and int(port_val) > 0 and int(port_val) < 65535\
            and pattern.match(address_val):
        # port.set("")
        chat(False, int(port_val), address_val)


def chat_host():
    port_val = port.get()
    if port_val.isnumeric() and int(port_val) > 0 and int(port_val) < 65535:
        print(f"Hosting on port: {port_val}")
        # port.set("")
        chat(True, int(port_val))


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
    button_host = tkinter.Button(
        buttons_box, text="Connect", command=chat_connect)
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
window.mainloop()
