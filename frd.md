# Gereksinim Yönetimi Sistemi (RMS) Teknik Şartnamesi

## 1. Giriş ve Amaç
Bu doküman, karmaşık projelerde teknik şartnamelerin dijitalleştirilmesi, disiplinler arası (mekanik, yazılım, elektronik vb.) koordinasyonun sağlanması ve tam izlenebilirlik (traceability) sunulması amacıyla geliştirilecek yazılımın gereksinimlerini tanımlar.

---

## 2. Veri Girişi ve Gereksinim Tanımlama

### 2.1. Akıllı İçe Aktarma (Import)
* **Şartname Ayrıştırma:** Sistem; PDF ve Word formatındaki teknik şartnameleri içe aktarabilmelidir.
* **Otomatik Maddeleştirme:** Metin içerisindeki maddeler (Örn: Madde 3.2.1) otomatik olarak ayrıştırılarak her biri bağımsız birer "Gereksinim" (Requirement) olarak kaydedilmelidir.
* **Standart Entegrasyonu:** Projeye dahil edilen dış standartlar (ISO, MIL-STD vb.) sistem kütüphanesine eklenmeli ve bu standartların maddeleri de gereksinim olarak çağrılabilmelidir.

### 2.2. Gereksinim Öznitelikleri ve Organizasyon
* **Benzersiz Numaralandırma:** Her gereksinim, sistem tarafından üretilen benzersiz (unique) bir ID (Örn: REQ-001, SYS-102) ile takip edilmelidir.
* **Tip Belirleme (Açıklama Modu):** Bazı maddelerin sadece bilgilendirme amaçlı (başlık veya açıklama) olduğunu belirtmek için bir **"Açıklama" (Checkbox)** alanı bulunmalıdır.
* **Disiplin Ayrımı:** Gereksinimler, aşağıdaki disiplinlere göre kategorize edilebilmelidir (Pulldown Menu):
    - Sistem
    - Mekanik
    - Yazılım
    - Elektronik
    - Otomasyon
    - Optik
    - Diğer (Özelleştirilebilir)
* **Türetilmiş İsterler:** Mevcut bir gereksinimden yeni alt isterler (derived requirements) oluşturulabilmeli ve bunlar hiyerarşik olarak ana gereksinime bağlanmalıdır.

### 2.3. Düzenleme ve Görselleştirme
* **Zengin Metin Editörü:** Gereksinim detaylarında tablo, görsel, şema ve matematiksel formül desteği bulunmalıdır.
* **Hiyerarşik Yapı:** Gereksinimler; **Epic > Feature > User Story** veya **Sistem > Alt Sistem > Bileşen** kırılımında görüntülenebilmelidir.
* **Şablon Desteği:** "Bir [rol] olarak, [amaç] istiyorum..." gibi standart formatlar için hazır taslaklar sunulmalıdır.

---

## 3. Versiyon Kontrolü ve İş Akışı

### 3.1. Tarihçe ve Geri Dönüş
* **Versiyon Kontrolü:** Bir gereksinim üzerindeki her değişiklik (kim, ne zaman, neyi değiştirdi?) kayıt altına alınmalıdır.
* **Baseline Oluşturma:** Projenin belirli aşamalarında gereksinimlerin "anlık görüntüsü" (Snapshot) alınarak dondurulabilmelidir.

### 3.2. Onay Mekanizması
* **İş Akışı (Workflow):** Gereksinimler; `Taslak`, `İncelemede`, `Onaylandı`, `Reddedildi` gibi statülere sahip olmalıdır.
* **İşbirliği:** Madde bazlı yorum yapma ve @etiketleme (mention) özelliği ile ilgili mühendise bildirim gitmelidir.
* **E-İmza:** Kritik sektör gereksinimleri için resmi onay ve elektronik imza süreci işletilmelidir.

---

## 4. İzlenebilirlik ve Analiz (Traceability)

### 4.1. İzlenebilirlik Matrisi (RTM)
* **Uçtan Uca Takip:** Gereksinimlerin; tasarım dökümanları, alt sistemler ve test senaryoları ile olan ilişkisi bir tablo (matris) üzerinden izlenebilmelidir.



[Image of Requirements Traceability Matrix]


### 4.2. Etki Analizi (Impact Analysis)
* Bir gereksinim güncellendiğinde, bu maddeye bağlı olan tüm alt gereksinimler ve testler otomatik olarak "Şüpheli" (Suspect) olarak işaretlenmeli ve analiz edilmesi istenmelidir.

---

## 5. Önceliklendirme ve Planlama

### 5.1. Puanlama Modelleri
* Sistem; **MoSCoW** (Must, Should, Could, Won't), **RICE** veya **WSJF** gibi metotlarla otomatik öncelik puanı hesaplayabilmelidir.

### 5.2. Görsel Planlama
* **Yol Haritası (Roadmap):** Gereksinimlerin zaman çizelgesi (Gantt) üzerinde dağılımı.
* **Kapasite Yönetimi:** Gereksinimlerin iş yükü puanlarına göre disiplinlere ve ekiplere atanması.

---

## 6. Teknik Gereksinimler
* **Entegrasyon:** Jira, Azure DevOps veya Enterprise Architect ile çift yönlü senkronizasyon.
* **Dışa Aktarım:** Gereksinimlerin PDF/Word formatında resmî doküman olarak çıktı alınabilmesi.