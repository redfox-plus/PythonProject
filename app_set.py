import sys
import threading
import time
import pyvisa
from PyQt5 import uic
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow
from queue import Queue
from threading import Thread
import os
import requests

from functools import wraps


def print_func_name(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"调用函数: {func.__name__}")
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 打印并避免异常冒泡到 Qt 事件循环导致崩溃
            print(f"{func.__name__} 捕获异常: {e}")
            # 如果第一个参数是 self 且有统一的错误显示控件，可在此更新 UI：
            try:
                if args and hasattr(args[0], "IdnShowAlineEdit"):
                    args[0].IdnShowAlineEdit.setText("Fail")
            except Exception:
                pass
    return wrapper





class Timer(QThread):

        tick = pyqtSignal()  # 定义一个信号

        def __init__(self, interval=1.0):
            super().__init__()
            self.interval = interval
            self.running = True

        def run(self):
            while self.running:
                self.tick.emit()  # 发信号
                time.sleep(self.interval)

        def stop(self):
            self.running = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()


        self.timer_thread = Timer(interval=1.0)
        self.timer_thread.tick.connect(self.on_tick)
        self.timer_thread.start()





        # 使用默认 VISA 后端
        self.rm = pyvisa.ResourceManager()
        self.screen_times = 0

        self.inst = None   # 分析仪 TCPIP
        self.instS = None  # 信号源 GPIB
        self.write_queue_A = Queue() #创建发送命令队列
        self.write_thread_A = Thread(target=self.write_thread_func_A, daemon=True)
        self.write_thread_A.start()

        self.write_queue_S = Queue() #创建发送命令队列
        self.write_thread_S = Thread(target=self.write_thread_func_S, daemon=True)
        self.write_thread_S.start()

        #===========================================
        # 窗口默认设置初始化
        #===========================================
        uic.loadUi("untitled.ui", self)

        self.AttSetdoubleSpinBox.setRange(-100, 100)
        self.MakerSetdoubleSpinBoxCustomiz.setRange(-100, 100)
        self.SouseceLEVELSetdoubleSpinBox.setRange(-100, 100)
        self.RbwSetdoubleSpinBox.setRange(0, 1000)
        self.VbwSetdoubleSpinBox.setRange(0, 1000)
        self.FREQSetdoubleSpinBoxCustomiz.setRange(-1000, 1000)
        self.FREQSetdoubleSpinBox.setRange(0,10000)

        self.AttSetdoubleSpinBox.setValue(-50)
        self.SpanSetdoubleSpinBox.setValue(10)
        self.MakerSetdoubleSpinBox.setValue(10)
        self.RbwSetdoubleSpinBox.setValue(910)
        self.VbwSetdoubleSpinBox.setValue(910)
        self.SouseceFREQSetdoubleSpinBox.setValue(20)
        self.FREQSetdoubleSpinBoxCustomiz.setValue(10)
        self.FREQSetdoubleSpinBox.setValue(100)
        self.FREQheadSetdoubleSpinBoxCustomiz.setValue(0)
        self.FREQtailSetdoubleSpinBoxCustomiz.setValue(20)

        self.Span_value = None
        self.Maker_value = 0.0
        self.FREQ_value = 0.0
        self.RFS_Switch = False
        self.RFRoll_DONE = 0
        self.linshi_index = 0
        self.linshi_list = [20,30,40,50,60,70,80,90,100]




        #===========================================
        # 按钮绑定区
        #===========================================
        self.AnalzarConnetButton.clicked.connect(self.AnalzarConnetButtonFunc)
        self.PeekButton.clicked.connect(self.PeekButtonFunc)
        self.AttButton.clicked.connect(self.AttButtonFunc)
        self.RbwButton.clicked.connect(self.RbwButtonFunc)
        self.VbwButton.clicked.connect(self.VbwButtonFunc)
        self.SpanButton.clicked.connect(self.SpanButtonFunc)
        self.SpanstepNeg100.clicked.connect(self.SpanstepNeg100Func)
        self.SpanstepNeg10.clicked.connect(self.SpanstepNeg10Func)
        self.SpanstepNeg1.clicked.connect(self.SpanstepNeg1Func)
        self.Spanstep1.clicked.connect(self.Spanstep1Func)
        self.Spanstep10.clicked.connect(self.Spanstep10Func)
        self.Spanstep100.clicked.connect(self.Spanstep100Func)
        self.MakerButton.clicked.connect(self.MakerButtonFunc)
        self.MakerstepNeg100.clicked.connect(self.MakerstepNeg100Func)
        self.MakerstepNeg10.clicked.connect(self.MakerstepNeg10Func)
        self.MakerstepNeg1.clicked.connect(self.MakerstepNeg1Func)
        self.Makerstep1.clicked.connect(self.Makerstep1Func)
        self.Makerstep10.clicked.connect(self.Makerstep10Func)
        self.Makerstep100.clicked.connect(self.Makerstep100Func)
        self.MakerstepCustomize.clicked.connect(self.MakerstepCustomizeFunc)
        self.MaxHoldButton.clicked.connect(self.MaxHoldButtonFunc)
        self.MixHoldButton.clicked.connect(self.MixHoldButtonFunc)
        self.AverageButton.clicked.connect(self.AverageButtonFunc)
        self.SousceConnetButton.clicked.connect(self.SousceConnetButtonFunc)
        self.SouseceFREQButton.clicked.connect(self.SouseceFREQButtonFunc)
        self.SouseceLEVELButton.clicked.connect(self.SouseceLEVELButtonFunc)
        self.SouseceFREQRollButton.clicked.connect(self.SouseceFREQRollButtonFunc)
        self.TraceClearButton.clicked.connect(self.TraceClearButtonFunc)
        self.FREQButton.clicked.connect(self.FREQButtonFunc)
        self.FREQStepNeg100.clicked.connect(self.FREQStepNeg100Func)
        self.FREQstepNeg10.clicked.connect(self.FREQstepNeg10Func)
        self.FREQstepNeg1.clicked.connect(self.FREQstepNeg1Func)
        self.FREQstep1.clicked.connect(self.FREQstep1Func)
        self.FREQstep10.clicked.connect(self.FREQstep10Func)
        self.FREQstep100.clicked.connect(self.FREQstep100Func)
        self.FREQstepCustomize.clicked.connect(self.FREQstepCustomizeFunc)
        self.RFAswicth.clicked.connect(self.RFAswicthFunc)
        self.FREQHDCustomize.clicked.connect(self.FREQHDCustomizeFunc)

        self.shangyige.clicked.connect(self.shangyigeFunc)
        self.xiayige.clicked.connect(self.xiayigeFunc)


    def on_tick(self):
        if self.SpanAoto.isChecked():
            self.SpanButtonFunc()
        if self.FREQAoto.isChecked():
            self.FREQButtonFunc()
        if self.MakerAoto.isChecked():
            self.MakerButtonFunc()
        if self.RbwAoto.isChecked():
            self.RbwButtonFunc()
        if self.VbwAoto.isChecked():
            self.VbwButtonFunc()
        if self.PeekAoto.isChecked():
            self.PeekButtonFunc()


    #===========================================
    # 按钮槽函数
    #===========================================

    # 分析仪 TCPIP 连接
    @print_func_name
    def AnalzarConnetButtonFunc(self,checked=False):
        print("AnalzarConnetButton clicked")

        resource_name = self.SousceAnalzarChoose.currentText()#"TCPIP0::169.254.25.47::hislip0::INSTR"
        try:
            self.inst = self.rm.open_resource(resource_name[-38:])
            self.inst.timeout = 5000
            idn = self.inst.query("*IDN?")
            print("仪器IDN:", idn)
            self.IdnShowAlineEdit.setText("Done")
        except Exception as e:
            self.IdnShowAlineEdit.setText("Fail")
            print(f"TCPIP Connect Error: {e}")

    # 捕获屏幕图像
    @print_func_name
    def PeekButtonFunc(self, checked=False):
        print("PeekButton clicked")
        try:
            if self.PeekToScreen.isChecked():
                # 确保保存文件的文件夹存在
                folder = "screen"
                os.makedirs(folder, exist_ok=True)

                # 构造文件名
                file_name = f"scope_screen_{self.screen_times}.png"
                file_path = os.path.join(folder, file_name)

                # 请求截图
                url = "http://169.254.25.47/Agilent.SA.WebInstrument/Screen.png"
                resp = requests.get(url, timeout=10)  # 可根据网速调整timeout
                if resp.status_code == 200:
                    with open(file_path, "wb") as f:
                        f.write(resp.content)
                    print(f"截屏成功: {file_path}")
                    self.screen_times += 1
                else:
                    print(f"截屏失败，状态码: {resp.status_code}")

            # Marker 最大值操作
            self.write_queue_A.put(":CALCulate:MARKer1:MAXimum")

        except Exception as e:
            print(f"PeekButton error: {e}")

    # Att/RBW/VBW/Span/Marker 控制函数
    @print_func_name
    def AttButtonFunc(self,checked=False):
        try:
            value = self.AttSetdoubleSpinBox.value()
            self.write_queue_A.put(f":DISPlay:WINDow:TRACe:Y:SCALe:RLEVel {value*1e6}")
        except Exception as e:
            print(f"AttButton error: {e}")

    @print_func_name
    def RbwButtonFunc(self,checked=False):
        try:
            value = self.RbwSetdoubleSpinBox.value()
            self.write_queue_A.put(f":BANDwidth:RESolution {value*1e3}")
        except Exception as e:
            print(f"RbwButton error: {e}")

    @print_func_name
    def VbwButtonFunc(self,checked=False):
        try:
            self.Span_value = self.VbwSetdoubleSpinBox.value()
            self.write_queue_A.put(f":BANDwidth:VIDeo {self.Span_value*1e3}")
        except Exception as e:
            print(f"VbwButton error: {e}")

    @print_func_name
    def SpanButtonFunc(self,checked=False):
        try:
            self.Span_value = self.SpanSetdoubleSpinBox.value()
            self.write_queue_A.put(f":FREQuency:SPAN {self.Span_value*1e6}")
        except Exception as e:
            print(f"SpanButton error: {e}")

    @print_func_name
    def SpanstepNeg100Func(self,checked=False): self._change_span(-100)

    @print_func_name
    def SpanstepNeg10Func(self,checked=False): self._change_span(-10)

    @print_func_name
    def SpanstepNeg1Func(self,checked=False): self._change_span(-1)

    @print_func_name
    def Spanstep1Func(self,checked=False): self._change_span(1)

    @print_func_name
    def Spanstep10Func(self,checked=False): self._change_span(10)

    @print_func_name
    def Spanstep100Func(self,checked=False): self._change_span(100)

    @print_func_name
    def _change_span(self, delta,checked=False):
        try:
            if self.Span_value is None:
                self.Span_value = self.SpanSetdoubleSpinBox.value()
            self.Span_value += delta
            self.SpanSetdoubleSpinBox.setValue(self.Span_value)
            self.write_queue_A.put(f":FREQuency:SPAN {self.Span_value*1e6}")
        except Exception as e:
            print(f"Span step error: {e}")

    # Marker 控制
    @print_func_name
    def MakerButtonFunc(self,checked=False):
        self._set_marker(self.MakerSetdoubleSpinBox.value())




    @print_func_name
    def MakerstepNeg100Func(self,checked=False): self._step_marker(-100)

    @print_func_name
    def MakerstepNeg10Func(self,checked=False): self._step_marker(-10)
    def MakerstepNeg1Func(self,checked=False): self._step_marker(-1)

    @print_func_name
    def Makerstep1Func(self,checked=False): self._step_marker(1)

    @print_func_name
    def Makerstep10Func(self,checked=False): self._step_marker(10)

    @print_func_name
    def Makerstep100Func(self,checked=False): self._step_marker(100)

    @print_func_name
    def MakerstepCustomizeFunc(self,checked=False): self._step_marker(self.MakerSetdoubleSpinBoxCustomiz.value())

    @print_func_name
    def _set_marker(self, value):
        try:
            self.Maker_value = value
            self.MakerSetdoubleSpinBox.setValue(self.Maker_value)
            maker = self.MakerChooser.currentText()
            self.write_queue_A.put(f":CALCulate:MARKer{maker[-1]}:STATe ON")
            self.write_queue_A.put(f":CALCulate:MARKer{maker[-1]}:X {self.Maker_value*1e6}")
            print(f":CALCulate:MARKer1:X {self.Maker_value*1e6}")

            if self.FREQfollowMaker.isChecked():
                self.write_queue_A.put(":CALCulate:MARKer1:STATe ON")
                self.write_queue_A.put(f":FREQuency:CENTer {self.Maker_value * 1e6}")
                self.FREQSetdoubleSpinBox.setValue(self.Maker_value)

        #修改备注：这里的设置和改变的逻辑不一致，表现为maker按钮和快捷按钮的表现不同步


        except Exception as e:
            print(f"Marker set error: {e}")

    @print_func_name
    def _step_marker(self, delta,checked=False):
        try:
            self.Maker_value += delta
            self.MakerSetdoubleSpinBox.setValue(self.Maker_value)
            self.write_queue_A.put(f":CALCulate:MARKer1:X {self.Maker_value*1e6}")
            if self.FREQfollowMaker.isChecked():

                self.write_queue_A.put(f":FREQuency:CENTer {self.Maker_value * 1e6}")
                self.FREQSetdoubleSpinBox.setValue(self.Maker_value)
        except Exception as e:
            print(f"Marker step error: {e}")

    # Trace 控制
    @print_func_name
    def MaxHoldButtonFunc(self,checked=False):
        try: self.write_queue_A.put(":TRACe1:MODE MAXHold")
        except Exception as e: print(f"MaxHoldButton error: {e}")

    @print_func_name
    def MixHoldButtonFunc(self,checked=False):
        try: self.write_queue_A.put(":TRACe1:MODE MINHold")#
        except Exception as e: print(f"MixHoldButton error: {e}")

    @print_func_name
    def AverageButtonFunc(self,checked=False):
        try:
            # self.write_queue_A.put(":ACQuire:AVERage:COUNt 16")
            self.write_queue_A.put(":SENSe1:AVERage:STATe ON")
            self.write_queue_A.put(":SENSe1:AVERage:MODE SWEEP")
            self.write_queue_A.put(":SENSe1:AVERage:COUNt 16")
            print("使用平均功能")



        except Exception as e: print(f"AverageButton error: {e}")
#################################################################################
    @print_func_name
    def TraceClearButtonFunc(self,checked=False):
        try:
            self.write_queue_A.put(":TRACe1:MODE WRITe")
            self.write_queue_A.put(":TRACe1:CLEar")
        except Exception as e:
            print(f"TraceClearButton error: {e}")

    # Source GPIB 连接与控制
    @print_func_name
    def SousceConnetButtonFunc(self,checked=False):
        try:
            # 列出所有可用资源
            self.instS = self.rm.open_resource("GPIB0::28::INSTR")
            self.instS.timeout = 10000
            idn = self.instS.query("*IDN?")
            self.IdnShowGlineEdit.setText("Done")


            print(f"{idn}")

        except Exception as e:


            print("Exception type:", type(e))
            print("Exception args:", e.args)

            self.IdnShowGlineEdit.setText("连接失败")

    @print_func_name
    def RFAswicthFunc(self):
            try:
                if self.RFS_Switch :

                    self.write_queue_S.put(f"OUTPut OFF")
                    self.RFAswicth.setText("信号关")
                    self.RFS_Switch = False

                else:
                    self.write_queue_S.put(f"OUTPut ON")
                    self.RFAswicth.setText("信号开")
                    self.RFS_Switch = True

            except Exception as e:
                print(f"SouseceFREQButton error: {e}")



    @print_func_name
    def SouseceFREQButtonFunc(self,checked=False):
        try:
            value = self.SouseceFREQSetdoubleSpinBox.value()
            self.write_queue_S.put(f"FREQ {value*1e6}HZ")
        except Exception as e:
            print(f"SouseceFREQButton error: {e}")

    @print_func_name
    def SouseceLEVELButtonFunc(self,checked=False):
        try:
            value = self.SouseceLEVELSetdoubleSpinBox.value()
            self.write_queue_S.put(f":SOUR:POW:LEV:IMM:AMPL {value}DBM")
        except Exception as e:
            print(f"SouseceLEVELButton error: {e}")







    @print_func_name
    def SouseceFREQRollButtonFunc(self,checked=False):
        try:
            start = self.SouseceFREQRollStartSetdoubleSpinBox.value()
            finish = self.SouseceFREQRollFinSetdoubleSpinBox.value()
            step = self.SouseceFREQRollStepSetdoubleSpinBox.value()
            if start < finish:
                for i in range(int(start * 1e3), int(finish * 1e3), int(step)):
                        self.write_queue_S.put(f"FREQ {i * 1e3}HZ")
                        time.sleep(0.01)
            elif start > finish:
                for i in range(int(start), int(finish), -int(step)):
                        self.write_queue_S.put(f"FREQ {i * 1e6}HZ")
                        time.sleep(0.01)
            self.RFRoll_DONE = 1



        except Exception as e:
            print(f"SouseceFREQRollButton error: {e}")
########################################################################################

    @print_func_name
    def FREQButtonFunc(self,checked=False):
        value = self.FREQSetdoubleSpinBox.value()
        self.write_queue_A.put(f":FREQuency:CENTer {value * 1e6}")

    @print_func_name
    def FREQStepNeg100Func(self,checked=False):
        self._FREQ_change(-100)

    @print_func_name
    def FREQstepNeg10Func(self,checked=False):
        self._FREQ_change(-10)

    @print_func_name
    def FREQstepNeg1Func(self,checked=False):
        self._FREQ_change(-1)

    @print_func_name
    def FREQstep1Func(self,checked=False):
        self._FREQ_change(1)

    @print_func_name
    def FREQstep10Func(self,checked=False):
        self._FREQ_change(10)

    @print_func_name
    def FREQstep100Func(self,checked=False):
        self._FREQ_change(100)

    @print_func_name
    def FREQstepCustomizeFunc(self,checked=False):
        value = self.FREQSetdoubleSpinBoxCustomiz.value()
        self._FREQ_change(value)

    @print_func_name
    def FREQHDCustomizeFunc(self,checked=False):
        value_head = self.FREQheadSetdoubleSpinBoxCustomiz.value()
        value_tail = self.FREQtailSetdoubleSpinBoxCustomiz.value()
        self._FREQ_change((value_tail-value_head)/2)
        self.FREQSetdoubleSpinBox.setValue((value_tail-value_head)/2)

    @print_func_name
    def _FREQ_change(self,delta):
        try:
            if self.FREQ_value is None:
                self.FREQ_value = self.FREQSetdoubleSpinBox.value()
            self.FREQ_value += delta
            self.FREQSetdoubleSpinBox.setValue(self.FREQ_value)
            self.FREQheadSetdoubleSpinBoxCustomiz.setValue(self.FREQ_value-self.SpanSetdoubleSpinBox.value())
            self.FREQtailSetdoubleSpinBoxCustomiz.setValue(self.FREQ_value+self.SpanSetdoubleSpinBox.value())
            self.write_queue_A.put(f":FREQuency:CENTer {self.FREQ_value*1e6}")

        except Exception as e:
            print(f"Span step error: {e}")


    @print_func_name
    def write_thread_func_A(self,checked=False):
        while True:
            cmd = self.write_queue_A.get()
            if cmd is None:
                break
            try:
                if self.inst is not None:
                    self.inst.write(cmd)
                else:
                    print(f"write_thread_A: inst 未初始化，命令被忽略: {cmd}")
            except Exception as e:
                print(f"write_thread_A 异常: {e}")

    @print_func_name
    def write_thread_func_S(self,checked=False):
        while True:
            cmd = self.write_queue_S.get()
            if cmd is None:
                break
            try:
                if self.instS is not None:
                    self.instS.write(cmd)
                else:
                    print(f"write_thread_S: inst 未初始化，命令被忽略: {cmd}")
            except Exception as e:
                print(f"write_thread_A 异常: {e}")

    #临时区域
    def shangyigeFunc(self):
        self.linshi_index -= 1
        self.label_14.setText(f"{self.linshi_list[(self.linshi_index % len(self.linshi_list))]}Mhz")
        self._set_marker(self.linshi_list[(self.linshi_index % len(self.linshi_list))])
        self.write_queue_A.put(f":FREQuency:CENTer {(self.linshi_index % len(self.linshi_list)) * 1e6}")

    def xiayigeFunc(self):
        self.linshi_index += 1
        self.label_14.setText(f"{self.linshi_list[(self.linshi_index % len(self.linshi_list))]}Mhz")
        self._set_marker(self.linshi_list[(self.linshi_index % len(self.linshi_list))])
        self.write_queue_A.put(f":FREQuency:CENTer {self.linshi_list[(self.linshi_index % len(self.linshi_list))] * 1e6}")


#===========================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
