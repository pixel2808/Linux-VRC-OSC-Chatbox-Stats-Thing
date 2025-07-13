#!/usr/bin/env python3
import time
import sys
import os
import psutil
import datetime
from pythonosc import udp_client
import dbus
import subprocess
import tkinter as tk
from tkinter import ttk
from threading import Thread
import queue

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller bundles """
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Setup OSC Client for VRChat (adjust IP and port if necessary)
osc_client = udp_client.SimpleUDPClient("127.0.0.1", 9000)  # VRChat's default OSC port

# Function to get the current Linux distribution without external packages
def get_linux_distro():
    try:
        with open("/etc/os-release") as f:
            lines = f.readlines()
            distro_name = ""
            distro_version = ""
            for line in lines:
                if line.startswith("NAME="):
                    distro_name = line.strip().split("=")[1].replace('"', '')
                elif line.startswith("VERSION="):
                    distro_version = line.strip().split("=")[1].replace('"', '')
            return f"🐧 {distro_name} {distro_version}"
    except FileNotFoundError:
        return "🐧 Unknown Linux Distro"

# Function to get the current playing media info using MPRIS
def get_media_info():
    try:
        bus = dbus.SessionBus()
        players = [name for name in bus.list_names() if name.startswith('org.mpris.MediaPlayer2.')]

        for player_name in players:
            try:
                player = bus.get_object(player_name, '/org/mpris/MediaPlayer2')
                metadata = player.Get('org.mpris.MediaPlayer2.Player', 'Metadata', dbus_interface='org.freedesktop.DBus.Properties')
                title = metadata.get('xesam:title', 'Unknown Title')[:25]
                artist = metadata.get('xesam:artist', ['Unknown Artist'])[0][:15]
                return f"🎵 {title} - {artist}"
            except dbus.DBusException:
                continue

        return "🎵 No media playing"
    except dbus.DBusException as e:
        print(f"DBus error: {e}")
        return "🎵 No media player detected"

# Function to get GPU usage (assuming NVIDIA GPU with nvidia-smi)
def get_gpu_usage():
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=utilization.gpu,memory.free,memory.total', '--format=csv,noheader,nounits'],
            capture_output=True, text=True
        )
        gpu_stats = result.stdout.strip().split(', ')

        if len(gpu_stats) != 3:
            return "🎮 Error retrieving GPU stats"

        gpu_usage = gpu_stats[0]
        gpu_memory_free = round(int(gpu_stats[1]) / 1024, 1)  # GB
        gpu_memory_total = round(int(gpu_stats[2]) / 1024, 1)  # GB
        gpu_memory_used = round(gpu_memory_total - gpu_memory_free, 1)

        return f"🎮 {gpu_usage}% | {gpu_memory_used}GB / {gpu_memory_total}GB"
    except Exception as e:
        print(f"Error getting GPU usage: {e}")
        return "🎮 No GPU or error retrieving GPU stats"

# AMD GPU Shit
def get_amdgpu_usage():
    try:
        # Run radeontop once to get GPU usage and sampled VRAM usage (in MB)
        result = subprocess.run(
            ['radeontop', '-d', '-', '-l', '1'],
            capture_output=True, text=True, timeout=3
        )
        output = result.stdout.strip()

        # Remove timestamp prefix before first colon
        if ':' in output:
            output = output.split(':', 1)[1].strip()

        parts = [p.strip() for p in output.split(',')]

        gpu_usage = None
        vram_mb_used = None

        for part in parts:
            tokens = part.split()
            if not tokens:
                continue
            key = tokens[0].lower()
            if key == 'gpu' and len(tokens) >= 2:
                gpu_usage = tokens[1].replace('%', '')
            elif key == 'vram' and len(tokens) >= 3:
                vram_mb_used = float(tokens[2].lower().replace('mb', ''))

        if gpu_usage is None or vram_mb_used is None:
            return "🎮 Error retrieving GPU stats"

        # Read real VRAM total in bytes and convert to GB
        with open('/sys/class/drm/card0/device/mem_info_vram_total', 'r') as f:
            vram_total_bytes = int(f.read().strip())
        vram_total_gb = round(vram_total_bytes / (1024**3), 2)

        # Convert sampled VRAM usage in MB to GB
        vram_used_gb = round(vram_mb_used / 1024, 2)

        return f"🎮 {gpu_usage}% | {vram_used_gb}GB / {vram_total_gb}GB"
    except Exception as e:
        print(f"Error getting AMD GPU usage: {e}")
        return "🎮 No GPU or error retrieving GPU stats"

# Function to get CPU and RAM usage, along with CPU GHz and max RAM
def get_system_usage():
    try:
        cpu = psutil.cpu_percent(interval=1)
        cpu_ghz = round(psutil.cpu_freq().current / 1000, 2)
        ram_gb = round(psutil.virtual_memory().used / (1024**3), 1)
        max_ram_gb = round(psutil.virtual_memory().total / (1024**3), 1)
        return cpu, cpu_ghz, ram_gb, max_ram_gb
    except Exception as e:
        print(f"Error getting system usage: {e}")
        return "Error", "Error", "Error", "Error"

# Function to get current time (with 24-hour or 12-hour format based on user choice)
def get_current_time(is_24hr=True):
    if is_24hr:
        return datetime.datetime.now().strftime("%H:%M:%S")
    else:
        return datetime.datetime.now().strftime("%I:%M:%S %p")  # 12-hour format

# GUI for toggles and chatbox
class SystemInfoUI(tk.Tk):
    def __init__(self):
        super().__init__()
        icon_path = resource_path("Icon.png")
        self.iconphoto(False, tk.PhotoImage(file=icon_path))
        self.title("VRC OSC Chatbox Stats")
        self.geometry("600x750")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.is_sending = False
        self.queue = queue.Queue()
        self.message_duration = 5  # Default duration in seconds
        self.is_24hr = tk.BooleanVar(value=True)  # Default to 24-hour format

        # Boolean variables for each checkbox
        self.cpu_var = tk.BooleanVar(value=True)
        self.ram_var = tk.BooleanVar(value=True)
        self.gpu_var = tk.BooleanVar(value=True)
        self.media_var = tk.BooleanVar(value=True)
        self.time_var = tk.BooleanVar(value=True)
        self.linux_var = tk.BooleanVar(value=True)
        self.amdgpu_var = tk.BooleanVar(value=False)

        # Set up UI components
        self.create_widgets()
        self.apply_modern_theme()

    def create_widgets(self):
        # Create checkboxes for each data point
        self.cpu_check = ttk.Checkbutton(self, text="Send CPU Info", variable=self.cpu_var, style="TCheckbutton")
        self.cpu_check.pack(pady=10)

        self.ram_check = ttk.Checkbutton(self, text="Send RAM Info", variable=self.ram_var, style="TCheckbutton")
        self.ram_check.pack(pady=10)

        self.gpu_check = ttk.Checkbutton(self, text="Send GPU Info", variable=self.gpu_var, style="TCheckbutton")
        self.gpu_check.pack(pady=10)

        self.amdgpu_check = ttk.Checkbutton(self, text="Send AMD GPU Info", variable=self.amdgpu_var, style="TCheckbutton")
        self.amdgpu_check.pack(pady=10)

        self.media_check = ttk.Checkbutton(self, text="Send Media Info", variable=self.media_var, style="TCheckbutton")
        self.media_check.pack(pady=10)

        self.time_check = ttk.Checkbutton(self, text="Send Time Info", variable=self.time_var, style="TCheckbutton")
        self.time_check.pack(pady=10)

        self.linux_check = ttk.Checkbutton(self, text="Send Linux Distro", variable=self.linux_var, style="TCheckbutton")
        self.linux_check.pack(pady=10)

        # Toggle for 12-hour or 24-hour time format
        self.time_format_check = ttk.Checkbutton(self, text="Use 24-Hour Format", variable=self.is_24hr, style="TCheckbutton")
        self.time_format_check.pack(pady=15)

        # Button to start/stop sending data
        self.start_button = ttk.Button(self, text="Start Sending", command=self.toggle_sending, style="TButton")
        self.start_button.pack(pady=20)

        # Status label showing the current state (Sending/Not Sending)
        self.status_label = ttk.Label(self, text="Status: Not Sending", foreground="red", style="TLabel")
        self.status_label.pack(pady=10)

        # Chatbox Section
        self.chat_label = ttk.Label(self, text="Enter a message:", style="TLabel")
        self.chat_label.pack(pady=15)

        self.chat_text = tk.Text(self, height=5, width=45, font=("Arial", 12))  # Increased font size for better readability
        self.chat_text.pack(pady=10)
        self.chat_text.bind("<Return>", self.send_chat_message)  # Bind Enter key to send message

        self.send_button = ttk.Button(self, text="Send Message", command=self.send_chat_message, style="TButton")
        self.send_button.pack(pady=10)

        # Duration input to control message display time in VRChat
        self.duration_label = ttk.Label(self, text="Message Display Duration (seconds):", style="TLabel")
        self.duration_label.pack(pady=15)

        # Fix: Use tk.Entry instead of ttk.Entry
        self.duration_entry = tk.Entry(self, font=("Arial", 12), fg="black", insertbackground="gray")
        self.duration_entry.insert(0, "5")  # Default to 5 seconds
        self.duration_entry.pack(pady=10)

    def toggle_sending(self):
        if self.is_sending:
            self.is_sending = False
            self.status_label.config(text="Status: Not Sending", foreground="red")
            self.start_button.config(text="Start Sending")
        else:
            self.is_sending = True
            self.status_label.config(text="Status: Sending", foreground="green")
            self.start_button.config(text="Stop Sending")
            # Start background thread to send system info
            Thread(target=self.send_data_to_vrchat, daemon=True).start()

    def send_data_to_vrchat(self):
        MAX_MESSAGE_LENGTH = 144  # Maximum message length for VRChat

        while self.is_sending:
            current_time = get_current_time(self.is_24hr.get()) if self.time_var.get() else ""
            media_info = get_media_info() if self.media_var.get() else ""
            cpu_usage, cpu_ghz, ram_gb, max_ram_gb = get_system_usage() if self.cpu_var.get() or self.ram_var.get() else ("", "", "", "")
            gpu_usage = get_gpu_usage() if self.gpu_var.get() else ""
            linux_distro = get_linux_distro() if self.linux_var.get() else ""
            amdgpu_usage = get_amdgpu_usage() if self.amdgpu_var.get() else ""

            message = ""
            if linux_distro:
                message += f"{linux_distro}\n"
            if self.time_var.get():
                message += f"⏰ {current_time}\n"
            if self.media_var.get():
                message += f"{media_info}\n"
            if self.cpu_var.get():
                message += f"💻 {cpu_usage}% @ {cpu_ghz}GHz\n"
            if self.ram_var.get():
                message += f"💾 {ram_gb}GB / {max_ram_gb}GB\n"
            if self.gpu_var.get():
                message += f"{gpu_usage}"
            if self.amdgpu_var.get():
                message += f"{amdgpu_usage}"

            # Truncate the message if it's too long
            if len(message) > MAX_MESSAGE_LENGTH:
                message = message[:MAX_MESSAGE_LENGTH]

            # Send the message to VRChat's chatbox
            try:
                osc_client.send_message("/chatbox/input", [message, True, False])
            except Exception as e:
                print(f"Error sending chat message: {e}")

            time.sleep(1.5)  # Adjust the interval between messages

    def send_chat_message(self, event=None):
        message = self.chat_text.get("1.0", "end-1c").strip()
        if message:
            duration = self.get_message_duration()
            try:
                osc_client.send_message("/chatbox/input", [message, True, False])
            except Exception as e:
                print(f"Error sending chat message: {e}")

            self.chat_text.delete("1.0", "end")
            time.sleep(duration)

    def get_message_duration(self):
        try:
            duration = int(self.duration_entry.get())
        except ValueError:
            duration = 5  # Default duration if the value is invalid
        return duration

    def apply_modern_theme(self):
        # Apply a modern theme with a dark background and clean design
        self.configure(bg="#2e3b4e")
        style = ttk.Style(self)
        style.configure("TCheckbutton", background="#2e3b4e", foreground="#ffffff", font=("Arial", 12))
        style.configure("TButton", background="#5f78a1", foreground="#ffffff", font=("Arial", 12))
        style.configure("TLabel", background="#2e3b4e", foreground="#ffffff", font=("Arial", 12))
        style.configure("TEntry", background="#3f4a61", foreground="#ffffff", font=("Arial", 12))

    def on_closing(self):
        self.is_sending = False
        self.destroy()

if __name__ == "__main__":
    app = SystemInfoUI()
    app.mainloop()
