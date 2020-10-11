import socket
import enum
#Enum ile sözlük yapısındaki gibi bir yapı oluşturuldu.
class SlaveType(enum.Enum):
    Block = 0
    Train = 1
    Test = 2

class IsaretciColor(enum.Enum):
    Green=0
    Yellow=1
    Red=2

class ModBusPaket:
    def __init__(self,slave_id:int,function_code:int,data:bytes):
        self.Transaction_identifier = b'\x00\x01'# _Transaction_identifier ile başlıyorsa privite bir yapı olduğu ve değiştirlmemesi gerektiğini belirtir.
        self.Protocol_identifier = b'\x00\x00'#2 byte
        self.slave_id = slave_id #1byte
        self.function_code = function_code #1byte
        self.data = data

    def MessageLength(self):# MessageLength 2 byte kendi boyutunu ve gelecek olan datanın boyutunu belirtir. Bu data boyut bilgisi bufferdan gelecek olan sonraki dataları ayırmak için kullandıldı.
        return len(self.data) + 2

    @staticmethod   # @classmethod vb decorators ler class'a özellik katar. Mesela  @staticmethod sadece ModBusPaket.fromFrame ile çağrılabiliyor
                    # ve yeni bir nesne türetmeden kullanılabiliyor. Burda fromFrame kendisi nesne olamadan çağıralacak şekilde ayarlandı.
    def fromFrame(frame: bytes):
        """
        Byte dizisi halinde gelen paketi modbus paket nesnesi haline çevirir
        :param frame: Modbus-TCP-çerçevesi
        """
        assert frame[2:4] == b'\x00\x00', f"It is not Modbus Protocol Identifier{frame[2:4]} "
        packet = ModBusPaket(
            slave_id = frame[6],
            function_code = frame[7],
            data = frame[8:]
        )
        return packet

    def toFrame(self):
        frame = b''#byte dizisi oluşturuldu.
        frame += self.Transaction_identifier
        frame += self.Protocol_identifier
        frame += self.MessageLength().to_bytes(2, byteorder='big') # 2 byte lık bir byte dizisine dönüştürür.
        frame += self.slave_id.to_bytes(1, byteorder='big')
        frame += self.function_code.to_bytes(1, byteorder='big')
        frame += self.data
        return frame

    def __str__(self):
        return f"slave id: {self.slave_id}, func code: {self.function_code}, data: {self.data}"

    @staticmethod
    def DefinePacket(slave_id, slave_type: SlaveType):#Konrol Merkezine Slavelerin kendisini tanıtma (Train,Block) paketi üretir.
        return ModBusPaket(slave_id, 0, slave_type.value.to_bytes(1, "big", signed=False))


class ModbusClient:#istemci

    Buffer_Boyutu=1024         # gelecek olan paketin max uzunluğu, paketi 1024 bytelara böler öyle işlem yapar.
                               # Bu boyut değişebilir. Byte sayısı küçülünce yavaş çalışır.
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP paket  yapısı
        self.buffer = b''

    def connect(self,host,port):
        self.socket.connect((host, port))# belirtilen host ve port daki sunucuya bağlanır.

    def receive(self) -> ModBusPaket:#Soketten gelen ModBusPaketini dinler ve ModBusPaketi üretir
        while True:
            if len(self.buffer) < 6:# 6 byte>>Transaction(2byte)-Protocol(2byte) identidier ve message length(2byte) uzunluğu
                self.temp = self.socket.recv(ModbusClient.Buffer_Boyutu)
                if self.temp is None:
                    return None # paket boş gelirse methodu sonlandırır.
                self.buffer += self.temp
            else:
                t_id = self.buffer[0:2]
                p_id = self.buffer[2:4]
                m_len = int.from_bytes(self.buffer[4:6], "big", signed=False)
                if len(self.buffer) < m_len + 6:#m_len=len(slaveid)+len(functionid)+len(data)
                    self.temp = self.socket.recv(ModbusClient.Buffer_Boyutu)
                    if self.temp is None:
                        return None
                    self.buffer += self.temp
                    continue # iteraturü yani döngünün birkez çalışmasını kırar. Yani while'nın başına atar.
                s_id = int.from_bytes(self.buffer[6], "big", signed=False)
                fun_code = int.from_bytes(self.buffer[7], "big", signed=False)
                data = self.buffer[8:6 + m_len] #self.buffer[8:8 + len(data)] => len(data): m_len - 2 (s_id+fun_code)
                packet = ModBusPaket(s_id, fun_code, data)
                packet.Transaction_identifier = t_id
                packet.Protocol_identifier = p_id
                self.buffer = self.buffer[6 + m_len:]#bufferdan okuduğu paketi siler ve bir sonraki paketleri alır
                return packet
        return None


    def send(self,packet: ModBusPaket):
        assert type(packet) == ModBusPaket, f"packet is {type(packet)}"#assert false olursa yandaki hatayı basar
        self.socket.send(packet.toFrame())

    def close(self):
        self.socket.close()


class ModbusServer:#sunucu
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.Buffer_Boyutu = 1024 #1kbyte
        self.buffer = b''

    def bind(self, host, port):
        self.socket.bind((host, port))

    def listen(self, client_count=5):
        self.socket.listen(client_count)

    def receive(self, client: socket) -> ModBusPaket:
        while True:
            if len(self.buffer) < 6:
                self.temp = client.recv(ModbusClient.Buffer_Boyutu)
                if self.temp is None:
                    return None
                self.buffer += self.temp
            else:
                t_id = int.from_bytes(self.buffer[0:2], "big", signed=False)
                p_id = int.from_bytes(self.buffer[2:4], "big", signed=False)
                m_len = int.from_bytes(self.buffer[4:6], "big", signed=False)
                if len(self.buffer) < m_len + 6:
                    self.temp = client.recv(ModbusClient.Buffer_Boyutu)
                    if self.temp is None:
                        return None
                    self.buffer += self.temp
                    continue
                s_id = int.from_bytes(self.buffer[6:7], "big", signed=False)
                fun_code = int.from_bytes(self.buffer[7:8], "big", signed=False)
                data = self.buffer[8:8 + m_len]
                packet = ModBusPaket(s_id, fun_code, data)
                packet.Transaction_identifier = t_id
                packet.Protocol_identifier = p_id
                self.buffer = self.buffer[8 + m_len:]
                return packet
        return None


    def send(self,client: socket, packet: ModBusPaket):
        assert type(packet) == ModBusPaket, f"packet is {type(packet)}"#assert false olursa yandaki hatayı basar
        client.send(packet.toFrame())
