import random
import time
import os
import math
from Multi_Thread_ModbusTCP.Control_Center_Server import ControlCenter
from Multi_Thread_ModbusTCP.ClientBlocks import BlockSlave
from Multi_Thread_ModbusTCP.ClientTrain import TrainSlave

# from TrainSimulation.Multi_Thread_ModbusTCP.Control_Center_Server import ControlCenter
# from TrainSimulation.Multi_Thread_ModbusTCP.ClientBlocks import BlockSlave
# from TrainSimulation.Multi_Thread_ModbusTCP.ClientTrain import TrainSlave

class Train:

    def __init__(self, rail_length, id: int):
        self.length = 150   # trenin uzunluğu
        self.position = 150 # treni baş kısmının konumu
        self.opt_speed = 30 # bir trenin hızlı gittiği zamanki sabit hızı
        self.speed = 0      # bir trenin  herhangi bir andaki hızı
        self.max_acc = 5    # max ivme
        self.drive_state = 0 # hedef sürme durumu
        self.rail_length = rail_length
        self.slave = None
        self._id = id # train id (train_0 vb)

    def start(self):
        self.slave = TrainSlave(host="localhost", port=5555, train_id=self._id)
        self.slave.Train_Stop = self.stop
        self.slave.Train_Slow = self.slow
        self.slave.Train_Continuation = self.begindrive
        self.slave.start()

    def drive(self):
        if self.speed + self.max_acc < self.drive_state:
            self.speed += self.max_acc
        elif self.speed < self.drive_state:
            self.speed = self.drive_state
        elif self.speed - self.max_acc > self.drive_state:
            self.speed -= self.max_acc
        elif self.speed > self.drive_state:
            self.speed = self.drive_state
        self.position = (self.position + self.speed) % self.rail_length

    def stop(self):
        self.drive_state = 0

    def slow(self):
        self.drive_state = self.opt_speed // 2

    def begindrive(self):
        self.drive_state = self.opt_speed



class GUI:

    chars = {
        "trainfront": "█",
        "train": "▓",
        "lefttop": "╔",
        "rightbottom": "╝",
        "leftbottom": "╚",
        "righttop": "╗",
        "vertical": "║",
        "horizontal": "═",
        "block": "◊",
        "ttop": "▀",
        "tbottom":"▄",
        "tleft":"▌",
        "tright":"▐",
    }

    def __init__(self):
        self.left = 0
        self.top = 0
        self.width = 100
        self.height = 30
        self.matris = None
        self.cursor = (0, 0)
        self.clear() #ekran açılınca ilk başta boşluk basılır

    def show(self):
        os.system("cls")# konsolu temizliyor.
        print("\n" * self.top, end="")#konsola yukardan satır boşluk bırakır
        for y in range(self.height):
            print(" " * self.left, end="")#konsola soldan boşluk bırakır
            for x in range(self.width):
                print(self.matris[y][x], end="")#matrisi yazdırır.
            print()

    def print(self, text:str, pos:tuple, length:int=None):#matrisin herhangi bir konumuna metin bastırır
        if length is None:
            length = len(text)
        x, y = self.cursor
        if pos is not None:
            x, y = pos
            self.cursor = x, y + 1
        for i in range(min(length, len(text))):
            self.matris[y][x] = text[i]
            x += 1
        for i in range(x, length):
            self.matris[y][x] = " "
            x += 1

    def clear(self):#matrise boşluk basılır
        self.matris = [[" " for x in range(self.width)] for y in range(self.height)]

    def lengthToPosition(self, length):#ray hattına göre verilen konumun matristeki konum değerini hesaplar
                                       #(yani konsola göre koordinatı ve rayın hangi kenarı olduğunu (x,y,kenarno)tuple olarak dönderir.)
        left, top, width, height, total_length = self.way_bounds
        length = int(length) % total_length
        dx = total_length / (2 * (width + height * 2))
        boxlength = round(length / dx)
        if boxlength <= width:
            return left + boxlength, top, 0
        elif boxlength <= width + height * 2:
            return left + width, top + math.ceil((boxlength - width) / 2), 1
        elif boxlength <= 2 * width + height * 2:
            return left + width - (boxlength - width - height * 2), top + height, 2
        else:
            return left, top + height - math.ceil((boxlength - 2 * width - height * 2) / 2), 3

    def way_print(self, left, top, width, height, total_length, blocks):#Ray hattı ve blokları döşüyor
        self.way_bounds = (left, top, width, height, total_length)
        # Top and Bottom line
        for x in range(left, left + width):
            self.matris[top][x] = GUI.chars["horizontal"]
            self.matris[top + height][x] = GUI.chars["horizontal"]
        # Left and Right line
        for y in range(top, top + height):
            self.matris[y][left] = GUI.chars["vertical"]
            self.matris[y][left + width] = GUI.chars["vertical"]
        # Corners
        self.matris[top][left] = GUI.chars["lefttop"]
        self.matris[top][left + width] = GUI.chars["righttop"]
        self.matris[top + height][left] = GUI.chars["leftbottom"]
        self.matris[top + height][left + width] = GUI.chars["rightbottom"]
        # Blocks
        for block, slave in blocks:
            if type(block) not in [int, float]:
                print(block)
                exit(0)
            coordinate = self.lengthToPosition(block)
            RENK = ["Y", "S", "K"]
            self.matris[coordinate[1]][coordinate[0]] = RENK[slave.isaretci_state]  # GUI.chars["block"]

    def train_print(self, trains):#Ekrana trenleri basar
        for train in trains:
            for l in range(train.position, train.position - train.length, -1):
                x, y, b = self.lengthToPosition(l)
                self.matris[y][x] = GUI.chars["train"]
            x, y, b = self.lengthToPosition(train.position)
            self.matris[y][x] = GUI.chars["trainfront"]


class TrainSimulation:#Gerçekte olabilecek şeylerin ortamını oluşturur.

    def __init__(self, length, blocks_count, trains_count):
        self.length = length
        self.blocks = []
        self.trains = []
        self.trains_count = trains_count
        self.clock = 0
        self.control_center = ControlCenter(host="localhost", port=5555)
        self.control_center.start()

        def add_blocks(count):
            dx = self.length / count # bir bloğun olması gereken boyu
            for i in range(count):
                blockslave = BlockSlave(host="localhost", port=5555, block_id=len(self.blocks)) #localhost:127.0.0.1
                self.blocks.append((i * dx, blockslave))#Oluşan bloğun konumunu ve block slave 'i ni tutar.
                blockslave.start()

        add_blocks(blocks_count)
        self.gui = GUI()
        self.gui.way_print(3, 1, 90, 28, self.length, self.blocks)
        self.gui.show()


    def crush_control(self):# çarpışmayı kontrol eder
        for t1 in range(len(self.trains) - 1):
            for t2 in range(t1 + 1, len(self.trains)):
                T1 = self.trains[t1]
                T2 = self.trains[t2]
                if T2.position < T1.position:
                    if T1.position - T1.length < T2.position:
                        return True
                if T1.position < T2.position:
                    if T2.position - T2.length < T1.position:
                        return True
        return False

    def RFControl(self):# bir trenin bir bloktan geçip geçmediğini kontrol ediyor(Tren bloğa girince aktif olur)
        for t in range(len(self.trains)):
            for b in range(len(self.blocks)):
                train = self.trains[t]
                block = self.blocks[b]
                if train.position >= block[0] and train.position - train.length <= block[0]:
                    block[1].RF(t)



    def start(self): # Simülasyonu an ve an çalıştırır.
        self.gui.clear()
        new_train_block = 2 # random.randint(2, len(self.blocks) // 3) ## yeni gelecek tren için kaç blok boş alan olacağını belirtir
        while True:
            self.clock += 1 # sümülasyonun zamanını sn cinsinden hesaplar time.sleep(.1) ile 10 kat hızlandırıldı
            self.gui.print(f"Time: {self.clock} sn", (0, 0), 20) # zamanı konsola bastırır
            # Tren yerleştirme
            if len(self.trains) < self.trains_count:
                IsEmpty = True
                for train in self.trains:# tüm trenlerin konumundan hangi blokta olduğuna bakılır
                    if train.position - train.length < self.blocks[new_train_block][0]:#ilk int(new_train_block) örn: burda 2 bloğun boşluk değilse
                        IsEmpty = False# boş değil için False döndürür.
                        break # geri kalan trenlere bakılmaz
                    elif train.position > self.blocks[-1][0]:#en son blok boş ise
                        IsEmpty = False# boş değil için False döndürür.
                        break # geri kalan trenlere bakılmaz
                if IsEmpty:# Eğer ilk int(new_train_block) adet blokta tren yoksa ve en son blok boş ise
                    # İlk bloğa tren yerleştir
                    T = Train(self.length, len(self.trains))
                    T.opt_speed = random.randint(20, 50)
                    T.begindrive()
                    # self.gui.print(f"train {len(self.trains)}: {T.opt_speed * 3.6} km/s", (6, 3 + len(self.trains)))
                    self.trains.append(T)
                    self.blocks[0][1].isaretci_state = 2
                    T.start()
                    new_train_block = 2 # bir sonraki gelecek tren için boş blok sayısı ayarlanır
                                        # random.randint(2, len(self.blocks) // 3)
            # Tren sürme
            for t in range(len(self.trains)):
                self.trains[t].drive() # hangi tren olduğunu bulduk
                #Tren hız vb bilgileri konsola bastırır.
                self.gui.print(f"train {t}: {self.trains[t].speed} m/s {self.trains[t].drive_state} {round(self.trains[t].drive_state / self.trains[t].opt_speed, 2)}", (6, 3 + t), 50)
            # Çarpışma kontrol
            if self.crush_control():
                self.stop()
                break

            self.RFControl()#her an RF Kontrolü yapılır
            #GUI

            self.gui.way_print(3, 1, 90, 28, self.length, self.blocks)# ray hattını matrise basar
            self.gui.train_print(self.trains)#trenleri matrise basar
            self.gui.show()#print ile matrisi ekrana basmak için show methodu çağrıldı
            time.sleep(.1)#0.1 saniyede bir while çalışır böylece simülasyon 10 kat hızlandırıldı

    def stop(self):
        self.gui.print("SİMULASYON DURDURULDU", (35, 14))

try:
    sim = TrainSimulation(length=5000, blocks_count=20, trains_count=20)#simulasyon nesnesi oluşturuldu
    sim.blocks[1] =200,sim.blocks[1][1] ##Bir bloğu isteğimiz bir yere taşır.
    sim.blocks[2] =400,sim.blocks[2][1] ##Bir bloğu isteğimiz bir yere taşır.
    sim.blocks[3] =600,sim.blocks[3][1] ##Bir bloğu isteğimiz bir yere taşır.
    sim.blocks[-1] =4600,sim.blocks[-1][1] ##Bir bloğu isteğimiz bir yere taşır.
    sim.start()
except Exception as e:
    print(e)
while True:
    time.sleep(10)
