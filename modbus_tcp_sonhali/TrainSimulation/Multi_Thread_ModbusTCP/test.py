from Multi_Thread_ModbusTCP.modbuslibrary import ModbusClient, ModBusPaket, SlaveType
import time
#projenin kontrol merkezinden istediğimiz bir yerin testini yapar. Diğer Slavelerde test yapmak için K.M  aracılığıyla test yapılabilir.
client = ModbusClient()
client.connect(host="localhost", port=5555)
client.send(ModBusPaket.DefinePacket(0, SlaveType.Test))
time.sleep(1)
try:
    while True:
        packet = client.receive()
        if not packet:
            break
        print(packet.data.decode("utf-8"))

    client.close()
except Exception as e:
    print(str(e))
while True:
    time.sleep(10)
