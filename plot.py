import sys
import threading
import time
import json
from platform import release

from PyQt5.QtCore import QThread, pyqtSignal
from typing import Any
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow
from pynput.mouse import Controller,Listener,Button


class CatchMove:

    def __init__(self):
        self.mouse = Controller()
        self.event: list[Any] = []
        self.start_time = None
        self.listener: Listener | None = None

    def start(self):
        if self.listener and self.listener.running:
            return  # 已经在监听
        self.start_time = time.time()
        self.listener = Listener(
            on_move=self.on_move,
            on_click=self.on_click,
            on_scroll=self.on_scroll,
        )
        self.listener.start()

    def stop(self):
        if self.listener:
            self.listener.stop()
            self.listener = None

    def on_move(self, x, y):
        self.event.append(("move", x, y, time.time()))

    def on_click(self, x, y, button, pressed):
        if pressed:
            self.event.append(("pressed", x, y, str(button), time.time()))
        else:
            self.event.append(("released", x, y, str(button), time.time()))

    def on_scroll(self, x, y, dx, dy):
        self.event.append(("scroll", x, y, dx, dy, time.time()))

    def save_event_to_json(self, filename="mouse_event.json"):
        json_list = []
        for e in self.event:
            if e[0] == "move":
                json_list.append({"type": "move",
                                  "x": e[1], "y": e[2],
                                  "time": e[3]})
            elif e[0] == "pressed":
                json_list.append({"type": "pressed",
                                  "x": e[1],
                                  "y": e[2],
                                  "button": e[3],
                                  "time": e[4]})
            elif e[0] == "released":
                json_list.append({"type": "released",
                                  "x": e[1],
                                  "y": e[2],
                                  "button": e[3],
                                  "time": e[4]})
            elif e[0] == "scroll":
                json_list.append({"type": "scroll",
                                  "x": e[1],
                                  "y": e[2],
                                  "dx": e[3],
                                  "dy": e[4],
                                  "time": e[5]})
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(json_list, f, indent=4, ensure_ascii=False)
        print(f"保存 {len(json_list)} 个事件到 {filename}")

class MousePlayer(QThread):
    finished = pyqtSignal()
    def __init__(self,filename="mouse_event.json"):
        super().__init__()


        self.mouse = Controller()
        self.filename = filename
        self.event = []



    def play(self):
        buffer = None
        now = None
        times = 0
        first_time = None
        last_time = None
        times_x_pox_r = 0
        times_y_pox_r = 0

        if not self.event:
            print("None file")
            return


        for e in self.event:
            if e["type"] == "move":
                if buffer is None:
                    buffer = e
                    first_time = e["time"]
                now = e
                times += 1

            elif e["type"] == "clicked":

                if now:

                    last_time = now["time"]

                    times_x_pox = (now["x"] - buffer["x"]) / times

                    times_y_pox = (now["y"] - buffer["y"]) / times

                    for i in range(times):
                        times_x_pox_r += times_x_pox

                        times_y_pox_r += times_y_pox

                        self.mouse.position = (

                            int(buffer["x"] + times_x_pox_r),

                            int(buffer["y"] + times_y_pox_r)


                        )

                        delay = (last_time - first_time) / times

                        time.sleep(delay)


                buffer = 0

    def mouse_json_to_weighted_json(self):#采样原始鼠标数据并处理成一秒50个动作帧的格式并另存，为可能的操作可视化调整做简化预处理（后续可能在图形化的设置中让操作员确认并局部修改自己的逻辑）
        with open(self.filename, "r", encoding="utf-8") as f:
            self.event = json.load(f)
        print(f"加载{len(self.event)}事件")




















class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("text.ui", self)

        self.is_listening = False
        self.catch = CatchMove()

        # 绑定按钮
        self.player.clicked.connect(self.playerFunc)
        self.recode.clicked.connect(self.recodeFunc)

    def recodeFunc(self):
        if not self.is_listening:
            self.catch.start()
            self.lineEdit.setText("正在监听")
            print("正在监听")
            self.is_listening = True
        else:
            self.catch.stop()
            self.catch.save_event_to_json("mouse_event.json")
            self.lineEdit.setText("监听结束")
            self.is_listening = False

    def playerFunc(self):
        player = MousePlayer(filename="mouse_event.json")

        threading.Thread(target=player.play).start()









if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
