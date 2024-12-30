import pymem
import struct
import ctypes
from ctypes import wintypes
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
import string
import tkinter as tk
from tkinter import ttk


class Vec3:
    """Class representing a 3D vector."""
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z


class Matrix4x4:
    """Class representing a 4x4 matrix."""
    def __init__(self, data=None):
        self.data = data if data is not None else [0] * 16


def read_memory(pm, address, data_type, size=None):
    try:
        if data_type == "int":
            return pm.read_int(address)
        elif data_type == "float":
            return pm.read_float(address)
        elif data_type == "string" and size:
            return pm.read_string(address, size)
        elif data_type == "vec3":
            data = pm.read_bytes(address, 12)  # 3 floats (12 bytes)
            return Vec3(*struct.unpack("fff", data))
        elif data_type == "matrix":
            data = pm.read_bytes(address, 64)  # 16 floats (64 bytes)
            return Matrix4x4(struct.unpack("16f", data))
        else:
            raise ValueError(f"Unsupported data type: {data_type}")
    except Exception as e:
        print(f"Error reading memory: {e}")
        return None


def clean_entity_name(name, max_length=32):
    if not name:
        return ""
    name = name.lstrip("CLONE ").rstrip("0123456789")
    cleaned_name = ""
    for i in range(min(len(name), max_length)):
        char = name[i]
        if char == '\x00' or char not in string.printable:
            break
        cleaned_name += char
    
    cleaned_name = cleaned_name.strip()

    # Ignore names that contain any of the following
    excluded_names = [
        "door",
        "active_chimney_smoke",
        "light_com_lantern",
        "x_de_sn_gate",
        "sound_boat_creak",
        "hargencollision - extra",
    ]

    # Check if any of the excluded names are in the cleaned name (case-insensitive)
    if any(excluded_name in cleaned_name.lower() for excluded_name in excluded_names):
        return None  # Return None to indicate this entity should be ignored

    # Ignore names starting with "active_sign_"
    if cleaned_name.lower().startswith("active_sign_"):
        return None  # Return None to indicate this entity should be ignored
        
    # Ignore names starting with "active_sign_"
    if cleaned_name.lower().startswith("furn_sign_inn_"):
        return None  # Return None to indicate this entity should be ignored

    return cleaned_name






def world_to_screen(position, matrix, display_width=1400, display_height=1050):
    try:
        x = (matrix.data[0] * position.x + matrix.data[1] * position.y + matrix.data[2] * position.z + matrix.data[3])
        y = (matrix.data[4] * position.x + matrix.data[5] * position.y + matrix.data[6] * position.z + matrix.data[7])
        z = (matrix.data[8] * position.x + matrix.data[9] * position.y + matrix.data[10] * position.z + matrix.data[11])
        w = (matrix.data[12] * position.x + matrix.data[13] * position.y + matrix.data[14] * position.z + matrix.data[15])

        if w < 0.001:
            return None

        inv_w = 1.0 / w
        screen_x = x * inv_w
        screen_y = y * inv_w

        screen_x = (screen_x + 1.0) * 0.5 * display_width
        screen_y = (1.0 - screen_y) * 0.5 * display_height

        return QtCore.QPointF(screen_x, screen_y)

    except Exception as e:
        print(f"Error converting world to screen: {e}")
        return None


def get_client_area(window_title):
    hwnd = ctypes.windll.user32.FindWindowW(None, window_title)
    if not hwnd:
        raise ValueError(f"Window with title '{window_title}' not found.")
    rect = wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))

    client_rect = wintypes.RECT()
    ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(client_rect))

    border_x = (rect.right - rect.left) - client_rect.right
    border_y = (rect.bottom - rect.top) - client_rect.bottom

    client_left = rect.left + (border_x // 2)
    client_top = rect.top + border_y - ctypes.windll.user32.GetSystemMetrics(4)  # Title bar height
    client_width = client_rect.right
    client_height = client_rect.bottom

    return client_left, client_top, client_width, client_height


class Overlay(QtWidgets.QWidget):
    def __init__(self, game_window, pm, base_address, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game_window = game_window
        self.pm = pm
        self.base_address = base_address
        self.entities = []
        self.view_matrix = Matrix4x4()
        self.show_entity_names = True
        self.show_npc_names = True  # New flag for NPC names
        self.show_health_bars = True
        self.show_health_values = True

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(game_window.left, game_window.top, game_window.width, game_window.height)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1)

        self.paint_timer = QtCore.QTimer(self)
        self.paint_timer.timeout.connect(self.update_overlay)
        self.paint_timer.start(5)

    def update_data(self):
        try:
            entity_list = read_memory(self.pm, self.base_address + 0x3C67DC, "int")
            entity_list = read_memory(self.pm, entity_list + 0x32C, "int")
            final_entity_list_ptr = read_memory(self.pm, entity_list + 0x14, "int")
            entity_count = read_memory(self.pm, final_entity_list_ptr + 0x98, "int")
            entity_list = read_memory(self.pm, final_entity_list_ptr + 0x94, "int")

            dw_view_matrix = read_memory(self.pm, self.base_address + 0x3C67DC, "int")
            dw_view_matrix = read_memory(self.pm, dw_view_matrix + 0x134, "int")
            self.view_matrix = read_memory(self.pm, dw_view_matrix + 0x90, "matrix")

            self.entities = []
            for i in range(entity_count):
                entity = read_memory(self.pm, entity_list + i * 0x4, "int")
                if not entity:
                    continue

                name_ptr = read_memory(self.pm, entity + 0x8, "int")
                raw_name = read_memory(self.pm, name_ptr, "string", size=32)
                name = clean_entity_name(raw_name)

                if name is None:  # Skip entity if name is None (i.e., contains "door")
                    continue

                position = read_memory(self.pm, entity + 0x64, "vec3")
                health_ptr = read_memory(self.pm, entity + 0x84, "int")
                health = read_memory(self.pm, health_ptr + 0x2BC, "float") if health_ptr else None

                self.entities.append({"name": name, "position": position, "health": health})

        except Exception as e:
            print(f"Error updating data: {e}")


    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        for entity in self.entities:
            screen_pos = world_to_screen(entity["position"], self.view_matrix, self.width(), self.height())
            if screen_pos:
                head_offset = QtCore.QPointF(0, -30)
                head_position = screen_pos + head_offset

                if self.show_entity_names and entity["health"] is None:  # Entity (no health)
                    painter.setPen(QtGui.QColor(255, 255, 255, 255))
                    painter.drawText(head_position + QtCore.QPointF(10, -15), entity["name"])

                if self.show_npc_names and entity["health"] is not None:  # NPC (has health)
                    painter.setPen(QtGui.QColor(255, 255, 255, 255))
                    painter.drawText(head_position + QtCore.QPointF(10, -15), entity["name"])

                if self.show_health_bars and entity["health"] is not None:
                    health_bar_width = 50
                    health_bar_height = 5
                    health_percentage = entity["health"] / 100
                    health_bar_fill_width = int(health_percentage * health_bar_width)

                    health_bar_x = int(screen_pos.x() - health_bar_width / 2)
                    health_bar_y = int(screen_pos.y() + 10)
                    painter.setPen(QtGui.QColor(0, 0, 0, 255))
                    painter.setBrush(QtGui.QColor(0, 0, 0, 255))
                    painter.drawRect(health_bar_x, health_bar_y, health_bar_width, health_bar_height)

                    painter.setBrush(QtGui.QColor(0, 255, 0, 255))
                    painter.drawRect(health_bar_x, health_bar_y, health_bar_fill_width, health_bar_height)

                if self.show_health_values and entity["health"] is not None:
                    painter.setPen(QtGui.QColor(255, 255, 255, 255))
                    painter.drawText(head_position + QtCore.QPointF(10, 0), f"HP: {entity['health']:.1f}")

        painter.end()

    def update_overlay(self):
        self.repaint()

    def toggle_entity_names(self):
        self.show_entity_names = not self.show_entity_names

    def toggle_npc_names(self):  # New method to toggle NPC names
        self.show_npc_names = not self.show_npc_names

    def toggle_health_bars(self):
        self.show_health_bars = not self.show_health_bars

    def toggle_health_values(self):
        self.show_health_values = not self.show_health_values


def show_gui(overlay):
    def toggle_entity_names():
        overlay.toggle_entity_names()

    def toggle_npc_names():  # Add toggle for NPC names
        overlay.toggle_npc_names()

    def toggle_health_bars():
        overlay.toggle_health_bars()

    def toggle_health_values():
        overlay.toggle_health_values()

    root = tk.Tk()
    root.title("ESP Features")

    ttk.Checkbutton(root, text="Show Entity Names", command=toggle_entity_names).pack()
    ttk.Checkbutton(root, text="Show NPC Names", command=toggle_npc_names).pack()  # New checkbox for NPC names
    ttk.Checkbutton(root, text="Show Health Bars", command=toggle_health_bars).pack()
    ttk.Checkbutton(root, text="Show Health Values", command=toggle_health_values).pack()

    root.mainloop()



def main():
    try:
        process_name = "Morrowind.exe"
        pm = pymem.Pymem(process_name)
        base_address = pymem.process.module_from_name(pm.process_handle, process_name).lpBaseOfDll

        game_window_title = "Morrowind"
        client_left, client_top, client_width, client_height = get_client_area(game_window_title)

        app = QtWidgets.QApplication([])

        from collections import namedtuple
        GameWindow = namedtuple("GameWindow", ["left", "top", "width", "height"])
        game_window = GameWindow(client_left, client_top, client_width, client_height)

        overlay = Overlay(game_window, pm, base_address)
        overlay.show()

        # Start the Tkinter GUI in a separate thread
        import threading
        threading.Thread(target=show_gui, args=(overlay,), daemon=True).start()

        app.exec_()

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()


