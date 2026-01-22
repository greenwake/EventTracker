# 📅 Event Tracker Pro

**Event Tracker Pro**, kişisel alışkanlıklarınızı, görevlerinizi ve etkinliklerinizi takip etmenizi sağlayan; gelişmiş veri görselleştirme araçları ve çoklu kullanıcı desteği sunan profesyonel bir masaüstü uygulamasıdır.

Bu proje, verilerinizi güvenli bir şekilde saklar ve size GitHub tarzı yoğunluk haritaları, zaman çizelgeleri ve sıklık histogramları ile içgörüler sunar.

---

## 🌟 Temel Özellikler

### 🔐 Güvenlik ve Kullanıcı Yönetimi

-   **Çoklu Kullanıcı Desteği:** Her kullanıcının verisi ayrı JSON dosyalarında izole edilir.
-   **Banka Seviyesinde Şifreleme:** Parolalar asla açık metin olarak saklanmaz. **Salted SHA-256 + PBKDF2 (100.000 iterasyon)** algoritması ile korunur.
-   **Güvenli Giriş:** Zamanlama saldırılarına (Timing Attacks) karşı `hmac` tabanlı doğrulama kullanılır.

### 📊 Veri Görselleştirme ve Analiz

-   **GitHub Tarzı Isı Haritası (Heatmap):** Yılın hangi günlerinde ne kadar aktif olduğunuzu renk yoğunluğu ile gösterir.
-   **Zaman Çizelgesi (Timeline):** Etkinliklerinizi kronolojik bir çizgi üzerinde, haftalık yoğunluk renkleriyle sunar.
-   **Sıklık Histogramı:** Etkinlikler arasında kaç gün ara verdiğinizi analiz eder (Örn: En sık 2 günde bir yapıyorsunuz).
-   **Aylık Özet:** Hangi ayda ne kadar performans gösterdiğinizi bar grafiği ile sunar.
-   **İnteraktif Grafikler:** Grafikler statik değildir; barlara tıkladığınızda o veriye ait tarih detaylarını görebilirsiniz.

### 🛠️ Veri Yönetimi ve Araçlar

-   **Çoklu Etkinlik Takibi:** Spor, Kitap, Yazılım gibi sınırsız sayıda farklı kategori oluşturabilirsiniz.
-   **CRUD İşlemleri:** Hatalı girilen kayıtları liste üzerinden silebilir veya tarihini düzenleyebilirsiniz.
-   **Akıllı Göç (Migration):** Eski sürümden kalan `.txt` verilerini otomatik olarak algılar ve JSON formatına dönüştürür.
-   **Otomatik Güncelleme:** Uygulama açıldığında GitHub API üzerinden yeni sürüm olup olmadığını kontrol eder ve kullanıcıyı uyarır. 

---

## 🚀 Kurulum ve Çalıştırma

### 1. Gereksinimler

Bu projeyi kaynak kodundan çalıştırmak için bilgisayarınızda Python yüklü olmalıdır.

```bash
# Gerekli kütüphaneleri yükleyinpip install matplotlib tkcalendar requests
```

### 2. Çalıştırma

```bash
python EventTracker_v13_Update.py
```

### 3. EXE Olarak Paketleme (Windows)

Projeyi tek bir çalıştırılabilir dosya (.exe) haline getirmek için **PyInstaller** kullanılır:

```bash
# PyInstaller'ı yükleyinpip install pyinstaller# Paketleme komutupyinstaller --noconsole --onefile --hidden-import "babel.numbers" --icon="logo.ico" EventTracker_v13_Update.py
```

*Oluşan `.exe` dosyası `dist` klasöründe bulunacaktır.*

---

## 📂 Proje Yapısı

```
EventTracker/├── EventTracker.py       # Ana uygulama kodu├── users.json            # Kullanıcı adları ve hashlenmiş şifreler├── Data/                 # Kullanıcı verilerinin tutulduğu klasör│   ├── kullanici1.json│   └── kullanici2.json├── eventList.txt         # (Eski sürümlerden kalan yedek dosya)└── README.md             # Proje dokümantasyonu
```

---

## 🔄 Güncelleme Sistemi Nasıl Çalışır?

Uygulama, `UpdateManager` sınıfı aracılığıyla GitHub Releases API'sini kullanır.

1.  Uygulama içinde tanımlı `MEVCUT_SURUM` ile GitHub'daki `latest` sürüm etiketini (tag) karşılaştırır.
2.  Eğer yeni bir sürüm varsa, kullanıcıya bildirim gösterir.
3.  Kullanıcı onaylarsa varsayılan tarayıcıda indirme sayfasını açar.

---

## 🤝 Katkıda Bulunma

1.  Bu repoyu Fork'layın.
2.  Yeni bir özellik dalı (branch) oluşturun (`git checkout -b ozellik/YeniOzellik`).
3.  Değişikliklerinizi Commit'leyin (`git commit -m 'Yeni özellik eklendi'`).
4.  Branch'inizi Push'layın (`git push origin ozellik/YeniOzellik`).
5.  Bir Pull Request oluşturun.