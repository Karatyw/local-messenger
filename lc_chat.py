import socket
import threading
import tkinter as tk
from tkinter import messagebox
import json

PORT = 5000

def send_json(sock, data):
    sock.sendall((json.dumps(data, ensure_ascii=False) + "\n").encode("utf-8"))

class Messenger:
    def __init__(self, root):
        self.root = root
        self.root.title("Мессенджер")
        self.root.geometry("900x650")
        self.root.minsize(760, 520)
        self.root.configure(bg="#0f172a")

        self.mode = None
        self.server_socket = None
        self.client_socket = None
        self.clients = {}
        self.next_client_id = 1
        self.lock = threading.Lock()
        self.my_id = None
        self.host_nick = "Хост"
        self.my_nick = ""

        self.build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_ui(self):
        self.header = tk.Frame(self.root, bg="#111827", height=72)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        self.title_label = tk.Label(
            self.header,
            text="Мессенджер",
            bg="#111827",
            fg="white",
            font=("Segoe UI", 18, "bold")
        )
        self.title_label.pack(side="left", padx=18)

        self.status_label = tk.Label(
            self.header,
            text="Ожидание",
            bg="#111827",
            fg="#94a3b8",
            font=("Segoe UI", 10)
        )
        self.status_label.pack(side="right", padx=18)

        self.top_panel = tk.Frame(self.root, bg="#0f172a")
        self.top_panel.pack(fill="x", padx=14, pady=12)

        self.nick_label = tk.Label(
            self.top_panel,
            text="Ник",
            bg="#0f172a",
            fg="#cbd5e1",
            font=("Segoe UI", 10)
        )
        self.nick_label.grid(row=0, column=0, sticky="w", padx=(0, 6))

        self.nick_entry = tk.Entry(
            self.top_panel,
            width=18,
            bg="#1e293b",
            fg="white",
            insertbackground="white",
            relief="flat",
            font=("Segoe UI", 10)
        )
        self.nick_entry.grid(row=0, column=1, padx=(0, 14), ipady=7)

        self.ip_label = tk.Label(
            self.top_panel,
            text="IP сервера",
            bg="#0f172a",
            fg="#cbd5e1",
            font=("Segoe UI", 10)
        )
        self.ip_label.grid(row=0, column=2, sticky="w", padx=(0, 6))

        self.ip_entry = tk.Entry(
            self.top_panel,
            width=20,
            bg="#1e293b",
            fg="white",
            insertbackground="white",
            relief="flat",
            font=("Segoe UI", 10)
        )
        self.ip_entry.grid(row=0, column=3, padx=(0, 14), ipady=7)

        self.server_button = tk.Button(
            self.top_panel,
            text="Запустить сервер",
            command=self.start_server,
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=16,
            pady=8,
            cursor="hand2"
        )
        self.server_button.grid(row=0, column=4, padx=(0, 10))

        self.client_button = tk.Button(
            self.top_panel,
            text="Подключиться",
            command=self.connect_to_server,
            bg="#10b981",
            fg="white",
            activebackground="#059669",
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=16,
            pady=8,
            cursor="hand2"
        )
        self.client_button.grid(row=0, column=5)

        self.chat_wrap = tk.Frame(self.root, bg="#0f172a")
        self.chat_wrap.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        self.canvas = tk.Canvas(
            self.chat_wrap,
            bg="#0b1220",
            highlightthickness=0,
            bd=0
        )
        self.scrollbar = tk.Scrollbar(self.chat_wrap, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.messages_frame = tk.Frame(self.canvas, bg="#0b1220")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.messages_frame, anchor="nw")

        self.messages_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        self.bottom_panel = tk.Frame(self.root, bg="#0f172a")
        self.bottom_panel.pack(fill="x", padx=14, pady=(0, 14))

        self.msg_entry = tk.Entry(
            self.bottom_panel,
            bg="#1e293b",
            fg="white",
            insertbackground="white",
            relief="flat",
            font=("Segoe UI", 11)
        )
        self.msg_entry.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 10))
        self.msg_entry.bind("<Return>", lambda event: self.send_message())

        self.send_button = tk.Button(
            self.bottom_panel,
            text="Отправить",
            command=self.send_message,
            bg="#f59e0b",
            fg="white",
            activebackground="#d97706",
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=18,
            pady=10,
            cursor="hand2"
        )
        self.send_button.pack(side="right")

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def scroll_to_bottom(self):
        self.root.after(20, lambda: self.canvas.yview_moveto(1.0))

    def set_status(self, text):
        self.root.after(0, lambda: self.status_label.config(text=text))

    def show_error(self, text):
        self.root.after(0, lambda: messagebox.showerror("Ошибка", text))

    def disable_mode_buttons(self):
        self.root.after(0, lambda: self.server_button.config(state="disabled"))
        self.root.after(0, lambda: self.client_button.config(state="disabled"))

    def enable_mode_buttons(self):
        self.root.after(0, lambda: self.server_button.config(state="normal"))
        self.root.after(0, lambda: self.client_button.config(state="normal"))

    def normalize_nick(self, nick):
        nick = str(nick).strip()
        nick = " ".join(nick.split())
        return nick[:24]

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def get_unique_nick(self, requested_nick, client_id):
        base = self.normalize_nick(requested_nick)
        if not base:
            base = f"Собеседник {client_id}"

        used = set()
        with self.lock:
            for cid, info in self.clients.items():
                if cid != client_id and info.get("nick"):
                    used.add(info["nick"])
        used.add(self.host_nick)

        if base not in used:
            return base

        n = 2
        while True:
            new_nick = f"{base} ({n})"
            if new_nick not in used:
                return new_nick
            n += 1

    def add_system_message(self, text):
        def work():
            row = tk.Frame(self.messages_frame, bg="#0b1220")
            row.pack(fill="x", pady=6, padx=10)

            label = tk.Label(
                row,
                text=text,
                bg="#0b1220",
                fg="#94a3b8",
                font=("Segoe UI", 9)
            )
            label.pack()
            self.scroll_to_bottom()
        self.root.after(0, work)

    def add_chat_message(self, sender, text, is_self=False):
        def work():
            row = tk.Frame(self.messages_frame, bg="#0b1220")
            row.pack(fill="x", pady=6, padx=10)

            bubble = tk.Frame(
                row,
                bg="#2563eb" if is_self else "#1e293b",
                padx=12,
                pady=8
            )

            if is_self:
                bubble.pack(anchor="e")
            else:
                bubble.pack(anchor="w")

            sender_label = tk.Label(
                bubble,
                text=sender,
                bg="#2563eb" if is_self else "#1e293b",
                fg="#dbeafe" if is_self else "#93c5fd",
                font=("Segoe UI", 9, "bold")
            )
            sender_label.pack(anchor="w")

            text_label = tk.Label(
                bubble,
                text=text,
                justify="left",
                wraplength=520,
                bg="#2563eb" if is_self else "#1e293b",
                fg="white",
                font=("Segoe UI", 11)
            )
            text_label.pack(anchor="w", pady=(2, 0))

            self.scroll_to_bottom()
        self.root.after(0, work)

    def start_server(self):
        if self.mode is not None:
            return

        try:
            self.host_nick = self.normalize_nick(self.nick_entry.get()) or "Хост"
            self.my_nick = self.host_nick

            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("", PORT))
            self.server_socket.listen(50)

            self.mode = "server"
            self.disable_mode_buttons()

            ip = self.get_local_ip()
            self.set_status(f"Сервер: {ip}:{PORT} | Ник: {self.host_nick}")
            self.add_system_message(f"Сервер запущен на {ip}:{PORT}")
            self.add_system_message(f"Твой ник: {self.host_nick}")

            threading.Thread(target=self.accept_clients, daemon=True).start()
        except Exception as e:
            self.server_socket = None
            self.mode = None
            self.show_error(str(e))

    def accept_clients(self):
        while True:
            try:
                conn, addr = self.server_socket.accept()
            except:
                break

            with self.lock:
                client_id = self.next_client_id
                self.next_client_id += 1
                self.clients[client_id] = {"sock": conn, "nick": None, "addr": addr[0]}

            threading.Thread(target=self.handle_client, args=(conn, client_id), daemon=True).start()

    def handle_client(self, conn, client_id):
        file = None
        assigned_nick = f"Собеседник {client_id}"

        try:
            file = conn.makefile("r", encoding="utf-8")

            first_line = file.readline()
            if not first_line:
                raise Exception()

            try:
                first_data = json.loads(first_line)
            except:
                first_data = {}

            requested_nick = ""
            if first_data.get("type") == "hello":
                requested_nick = first_data.get("nick", "")

            assigned_nick = self.get_unique_nick(requested_nick, client_id)

            with self.lock:
                if client_id in self.clients:
                    self.clients[client_id]["nick"] = assigned_nick

            send_json(conn, {
                "type": "welcome",
                "client_id": client_id,
                "nick": assigned_nick,
                "host_nick": self.host_nick
            })

            self.add_system_message(f"{assigned_nick} подключился")
            self.broadcast({"type": "info", "text": f"{assigned_nick} подключился"}, exclude_id=client_id)

            while True:
                line = file.readline()
                if not line:
                    break

                try:
                    data = json.loads(line)
                except:
                    continue

                if data.get("type") == "message":
                    text = str(data.get("text", "")).strip()
                    if not text:
                        continue

                    self.add_chat_message(assigned_nick, text, is_self=False)
                    self.broadcast({
                        "type": "message",
                        "sender": "client",
                        "client_id": client_id,
                        "nick": assigned_nick,
                        "text": text
                    }, exclude_id=client_id)
        except:
            pass

        try:
            if file:
                file.close()
        except:
            pass

        try:
            conn.close()
        except:
            pass

        removed = False
        with self.lock:
            if client_id in self.clients:
                del self.clients[client_id]
                removed = True

        if removed:
            self.add_system_message(f"{assigned_nick} отключился")
            self.broadcast({"type": "info", "text": f"{assigned_nick} отключился"})

    def connect_to_server(self):
        if self.mode is not None:
            return

        ip = self.ip_entry.get().strip()
        if not ip:
            self.show_error("Введи IP сервера")
            return

        try:
            self.my_nick = self.normalize_nick(self.nick_entry.get())

            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((ip, PORT))
            send_json(self.client_socket, {"type": "hello", "nick": self.my_nick})

            self.mode = "client"
            self.disable_mode_buttons()
            self.set_status(f"Подключено к {ip}:{PORT}")
            self.add_system_message(f"Подключение к {ip}:{PORT}")

            threading.Thread(target=self.receive_from_server, daemon=True).start()
        except Exception as e:
            self.client_socket = None
            self.mode = None
            self.show_error(str(e))

    def receive_from_server(self):
        file = None
        try:
            file = self.client_socket.makefile("r", encoding="utf-8")
            while True:
                line = file.readline()
                if not line:
                    break

                try:
                    data = json.loads(line)
                except:
                    continue

                msg_type = data.get("type")

                if msg_type == "welcome":
                    self.my_id = data.get("client_id")
                    self.my_nick = data.get("nick", "")
                    host_nick = data.get("host_nick", "Хост")
                    self.add_system_message(f"Ты в чате как: {self.my_nick}")
                    self.add_system_message(f"Ник сервера: {host_nick}")

                elif msg_type == "message":
                    sender = data.get("sender")
                    nick = data.get("nick", "")
                    text = str(data.get("text", "")).strip()

                    if not text:
                        continue

                    if sender == "host":
                        self.add_chat_message(nick, text, is_self=False)
                    elif sender == "client":
                        client_id = data.get("client_id")
                        if client_id != self.my_id:
                            self.add_chat_message(nick, text, is_self=False)

                elif msg_type == "info":
                    text = str(data.get("text", "")).strip()
                    if text:
                        self.add_system_message(text)
        except:
            pass

        try:
            if file:
                file.close()
        except:
            pass

        try:
            if self.client_socket:
                self.client_socket.close()
        except:
            pass

        self.client_socket = None
        self.mode = None
        self.my_id = None
        self.enable_mode_buttons()
        self.set_status("Отключено")
        self.add_system_message("Соединение закрыто")

    def broadcast(self, data, exclude_id=None):
        with self.lock:
            items = list(self.clients.items())

        for client_id, info in items:
            if exclude_id is not None and client_id == exclude_id:
                continue
            sock = info["sock"]
            try:
                send_json(sock, data)
            except:
                pass

    def send_message(self):
        text = self.msg_entry.get().strip()
        if not text:
            return

        if self.mode == "server":
            self.add_chat_message("Ты", text, is_self=True)
            self.broadcast({
                "type": "message",
                "sender": "host",
                "nick": self.host_nick,
                "text": text
            })
            self.msg_entry.delete(0, "end")

        elif self.mode == "client":
            try:
                send_json(self.client_socket, {"type": "message", "text": text})
                self.add_chat_message("Ты", text, is_self=True)
                self.msg_entry.delete(0, "end")
            except:
                self.add_system_message("Не удалось отправить сообщение")

        else:
            self.show_error("Сначала запусти сервер или подключись")

    def on_close(self):
        try:
            if self.server_socket:
                self.server_socket.close()
        except:
            pass

        try:
            if self.client_socket:
                self.client_socket.close()
        except:
            pass

        with self.lock:
            for info in self.clients.values():
                try:
                    info["sock"].close()
                except:
                    pass
            self.clients.clear()

        self.root.destroy()

root = tk.Tk()
app = Messenger(root)
root.mainloop()
