from Multi_Thread_ModbusTCP import modbuslibrary as modbus
# from TrainSimulation.Multi_Thread_ModbusTCP import modbuslibrary as modbus
from _thread import *
import threading
import time

class BlockSlave:

    def __init__(self, host, port, block_id):
        self.isaretci_state = 0  #0: yeşil 1:sarı 2:kırmızı
        self.slave_id = block_id
        self.host = host
        self.port = port
        self.client = modbus.ModbusClient()
        self.isaretci_changed=None

    def RF(self, train_id):
        packet = modbus.ModBusPaket(slave_id=self.slave_id, function_code=1, data=bytes([self.slave_id, train_id]))
        start_new_thread(self._send, (packet, ))

    def start(self):
        self.client.connect(self.host, self.port)
        packet=modbus.ModBusPaket.DefinePacket(slave_id=self.slave_id, slave_type=modbus.SlaveType.Block)
        start_new_thread(self._send, (packet, ))
        start_new_thread(self._main_threaded, ())

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
                    if self.isaretci_changed is not None:#değişen isaretci_state'in slave_id ve isaretci_state'ne ulaşabilmek için oluşturuldu.
                                                         #fakat biz henüz ihtiyaç olmadığı için kullanmadık
                        self.isaretci_changed(self.slave_id, self.isaretci_state)
        except:
            self.isaretci_state=2
            self.client.close()

#block = BlockSlave("192.168.1.104", 1111, 1) #localhost da yapabilirsin 127.0.0.1
