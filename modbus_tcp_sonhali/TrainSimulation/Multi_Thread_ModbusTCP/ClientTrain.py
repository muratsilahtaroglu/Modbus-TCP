import Multi_Thread_ModbusTCP.modbuslibrary as modbus
# import TrainSimulation.Multi_Thread_ModbusTCP.modbuslibrary as modbus
from _thread import *
import threading
import time

class TrainSlave:

    def __init__(self, host, port, train_id: int):
        self.isaretci_state = 0  #0: yeşil 1:sarı 2:kırmızı
        self.slave_id = train_id
        self.host = host
        self.port = port
        self.client = modbus.ModbusClient()
        self.Train_Stop=None
        self.Train_Slow=None
        self.Train_Continuation=None

    def start(self):
        self.client.connect(self.host, self.port)
        packet = modbus.ModBusPaket.DefinePacket(slave_id=self.slave_id, slave_type=modbus.SlaveType.Train)
        start_new_thread(self._send, (packet, ))#multi thread ile beklemeden yeni bir paket gönderilir
        start_new_thread(self._main_threaded, ())#ayrı bir thread ile sunucu dinleniyor

    def _send(self, paket):
        try:
            # message received from server
            self.client.send(paket)
        except:
            self.client.close()

    def _main_threaded(self):
        time.sleep(1) # çakışma olmasın diye her ihtimale karşı yazıldı
        try:
            while True:
                packet: modbus.ModBusPaket = self.client.receive()
                if packet.function_code == 1:
                    self.isaretci_state = int.from_bytes(packet.data, "big", signed=False)

                    if self.Train_Stop is not None:
                        if self.isaretci_state == modbus.IsaretciColor.Red.value:
                            self.Train_Stop()
                        elif self.isaretci_state == modbus.IsaretciColor.Yellow.value:
                            self.Train_Slow()
                        elif self.isaretci_state == modbus.IsaretciColor.Green.value:
                            self.Train_Continuation()
        except:
            self.client.close()
