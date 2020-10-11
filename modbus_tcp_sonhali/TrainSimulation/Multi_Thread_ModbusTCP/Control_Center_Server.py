from Multi_Thread_ModbusTCP import modbuslibrary as modbus
# from TrainSimulation.Multi_Thread_ModbusTCP import modbuslibrary as modbus
from _thread import *
import threading
import time


class ControlCenter:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server = modbus.ModbusServer()
        self.print_lock = threading.Lock()
        self.slaves = {}
        self.isaretciler_state = []
        self.trains_position = {}
        self.test = None

    def start(self):
        start_new_thread(self._main_threaded, ())

    def print(self, mesaj):
        if self.test is not None:
            self.server.send(self.test, modbus.ModBusPaket(0, 1, mesaj.encode("utf-8")))

    def _client_threaded(self, client: modbus.socket.socket, addr):
        key = None
        slave_type = {
            0: "Block",
            1: "Train",
            2: "Test"
        }
        try:
            while True:

                # data received from client
                paket = self.server.receive(client)# istemciden paket okundu
                if not paket:# paket None ise paket olamyan istemcinin sunucu kulağı kapanır.
                    # lock released on exit
                    self.print_lock.release()
                    break

                if paket.function_code == 0:
                    key = slave_type[paket.data[0]] + "_" + str(paket.slave_id)
                    if paket.data[0] == modbus.SlaveType.Test.value:
                        self.test = client# test slavenin soketini self.test de tutuldu
                        self.print("Sunucuya bağlanıldı.")
                        self.print(f"connected slaves: {list(self.slaves.keys())}")
                    else:
                        self.print(f"CONNECT: {key} slave.")
                        self.slaves[key] = (addr, paket.slave_id, client)#train ve block (addr, paket.slave_id, client) leri kayıt edildi
                        if paket.data[0] == modbus.SlaveType.Block.value:#Başlangıçta bağlanan tüm blokların işareti yeşil sayılıyor.
                            self.isaretciler_state.append(modbus.IsaretciColor.Green.value)

                elif paket.function_code == 1:#RFsinyali geldiyse;
                    block_id, train_id = paket.data[0], paket.data[1]#hangi train ile hangi block'un karşılaştığını söyler.
                    #self.print(f"RF sinyali yakalandı block_{block_id}, train_{train_id}")
                    self.trains_position["Train_" + str(train_id)] = "Block_" + str(block_id)
                    # trene önündeki işaretçinin rengini veriyoruz.
                    isaretci_rengi = self.isaretciler_state[(block_id + 1) % len(self.isaretciler_state)]
                    packet = modbus.ModBusPaket(train_id, 1, bytes(bytearray([isaretci_rengi])))
                    self.server.send(self.slaves["Train_" + str(train_id)][2], packet)
                    # trenin arkasında kalan bloğu kırmızı yap
                    packet = modbus.ModBusPaket(block_id, 1, b'\x02')
                    self.server.send(self.slaves["Block_" + str(block_id)][2], packet)
                    self.isaretciler_state[block_id] = modbus.IsaretciColor.Red.value
                    # trenin iki arkasında kalan bloğu sarı yap
                    packet = modbus.ModBusPaket(block_id, 1, b'\x01')
                    self.server.send(self.slaves["Block_" + str((block_id-1) % len(self.isaretciler_state))][2], packet)
                    self.isaretciler_state[block_id - 1] = modbus.IsaretciColor.Yellow.value
                    # trenin üç arkasında kalan bloğu ayarla
                    if self.isaretciler_state[block_id - 2] != modbus.IsaretciColor.Red.value:#trenin üç arkasında kalan blok kırmızı değilse
                        #trenin üç arkasında kalan bloğu yeşil yak
                        packet = modbus.ModBusPaket(block_id, 1, b'\x00')
                        self.server.send(self.slaves["Block_" + str((block_id-2) % len(self.isaretciler_state))][2], packet)
                        self.isaretciler_state[block_id - 2] = modbus.IsaretciColor.Green.value
        except Exception as e:
            if key.startswith("Block_"):#eğer bir block bağlantısı koparsa;
                self.isaretciler_state[int(key[6:])]=2#işaretçiyi kırmızı yakar

            if self.slaves.keys().__contains__(key):#patlayan client slavelerin içindeyse
                del self.slaves[key]  #silme yapılır
            self.print(f"HATA: '{key}' sonlandırıldı: '{str(e)}'")
        client.close()
        self.print(f"UYARI: '{key}' sonlandırıldı.")

    def _main_threaded(self):

        self.server.bind(self.host, self.port)
        # print("socket binded to port", self.port)

        # put the socket into listening mode
        self.server.listen(5)
        # print("socket is listening")

        while True:
            # establish connection with client
            client, addr = self.server.socket.accept()
            # lock acquired by client
            self.print_lock.acquire(False)
            # print('Connected to :', addr[0], ':', addr[1])
            # Start a new thread and return its identifier
            start_new_thread(self._client_threaded, (client, addr))

        # server.close()
