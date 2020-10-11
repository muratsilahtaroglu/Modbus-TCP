# Tren Simülasyonu

## Genel Mimari

Simulasyon üzerinde yer alan varlıklar şunlardır.
- Kontrol Merkezi
- Tren
- Blok
    - İşaretçi
    - RF anteni

### Kontrol Merkezi

Kontrol merkezinin görevleri arasında şunlar yer alacak:
- Treni durdurma
- İşaretçileri kontrol etme

Req(from Slave to Control)/Res|Function Code|Data|Açıklama
---|---|---|---
Request| 0| 0: "Block", 1: "Train", 2: "Test"|Slavelerin kendini tanıtma kodu
Request|1|blok_id, tren_id|Tren gelme bilgisini kontrol merkezine bildirme.
Response|1|0:Yeşil, 1:Sarı, 2:Kırmızı|Trenin önündeki işaretçinin renk bilgisini gönder.
Response|2| |Treni durdur.
Response|3| |Tren hareket edebilir.


### Tren

- Kontrol merkezinden durma emri gelirse kendini durdurur.
- Kontrol merkezinden trene önündeki işaretçinin renk bilgisi gelir.
- Trenin yeni gireceği bloğun RF antenine kendi id'sini sinyal olarak gönderir.
Bu durum simülasyon tarafından gerçekleştirilir.
Bloğun RF anteni simülasyon tarafından tetiklenmiş olur.

Req/Res|Function Code|Data|Açıklama
---|---|---|---
Response|1|0:Yeşil, 1:Sarı, 2:Kırmızı|Trenin önündeki işaretçinin renk bilgisi.
Response|2| |Treni durdur.
Response|3| |Tren hareket edebilir.

### Blok

Blok; işaretçi, RF anteni ve bir haberleşme modülünü içeren slave'den oluşur.
- RF anteninden bir tren sinyali gelirse bunu kontrol merkezine bildirir.
- Kontrol merkezinden işaretçi ile ilgili 

Req/Res|Function Code|Data|Açıklama
---|---|---|---
Request|1|blok_id, tren_id|Tren gelme bilgisini kontrol merkezine bildirme.
Response|1|0:Yeşil, 1:Sarı, 2:Kırmızı|Kontrol merkezinden işaretçinin rengini değiştirme emri.

## Simülasyon için yapılacak yapılar

### Blok
```python
class BlockSlave:
    def __init__(self, block_id, server_address):
        pass
    
    def RF(self, train_id):
        """
        RF anteni bir treni farkederse bu metot çağırılacak.
        :param train_id: Fark edilen trenin id'si.
        :return: 
        """
        pass
    
```

### Train
```python
class TrainSlave:
    def __init__(self, train, server_address):
        pass
```

### Kontrol Merkezi

```python
class ControlCenter:
    def __init__(self, address):
        pass
```
