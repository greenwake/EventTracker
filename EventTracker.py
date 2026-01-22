import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle, Patch
import matplotlib.dates as mdates
import os
import json
import hashlib # Şifreleme
import hmac # Güvenli Karşılaştırma
from collections import defaultdict, Counter
import locale
import webbrowser # Link açmak için
import requests   # API sorgusu için
import threading  # Arayüz donmasın diye

# tkcalendar kontrolü
try:
    from tkcalendar import DateEntry
except ImportError:
    messagebox.showerror("Eksik Kütüphane", "Lütfen 'tkcalendar' kütüphanesini yükleyin.\nKomut: pip install tkcalendar")
    exit()

# Dil ayarı
try:
    locale.setlocale(locale.LC_ALL, 'tr_TR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Turkish')
    except:
        pass 

# --- AYARLAR ---
DATA_KLASORU = "Data"
USERS_DOSYASI = "users.json"
ESKI_TXT_DOSYA_ADI = "eventList.txt"


MEVCUT_SURUM = "v1.0.1"
GITHUB_KULLANICI = "greenwake" 
GITHUB_REPO = "EventTracker"       

if not os.path.exists(DATA_KLASORU):
    os.makedirs(DATA_KLASORU)

class UpdateManager:
    @staticmethod
    def kontrol_et(manuel=False):
        """
        GitHub API'sini kontrol eder.
        manuel=True ise kullanıcı butona basmıştır (Her durumda bilgi ver).
        manuel=False ise otomatik başlangıçtır (Sadece güncelleme varsa rahatsız et).
        """
        def thread_hedefi():
            try:
                # GitHub API URL'si
                url = f"https://api.github.com/repos/{GITHUB_KULLANICI}/{GITHUB_REPO}/releases/latest"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    son_surum = data['tag_name'] # Örn: v1.1.0
                    indirme_linki = data['html_url'] # Release sayfası

                    if son_surum != MEVCUT_SURUM:
                        # Ana thread'de mesaj kutusu göster
                        msg = f"Yeni bir güncelleme mevcut!\n\nMevcut Sürüm: {MEVCUT_SURUM}\nYeni Sürüm: {son_surum}\n\nİndirme sayfasına gitmek ister misiniz?"
                        cevap = messagebox.askyesno("Güncelleme Mevcut", msg)
                        if cevap:
                            webbrowser.open(indirme_linki)
                    else:
                        if manuel:
                            messagebox.showinfo("Durum", f"Uygulamanız güncel.\nSürüm: {MEVCUT_SURUM}")
                else:
                    if manuel:
                        messagebox.showerror("Hata", "Güncelleme bilgisi alınamadı.\nRepo bulunamadı veya gizli.")
            except Exception as e:
                if manuel:
                    messagebox.showerror("Bağlantı Hatası", f"İnternet bağlantısı kurulamadı.\n{e}")

        threading.Thread(target=thread_hedefi, daemon=True).start()

# --- GÜVENLİ KULLANICI YÖNETİCİSİ 
class UserManager:
    def __init__(self):
        self.users = {}
        self.load_users()

    def load_users(self):
        if os.path.exists(USERS_DOSYASI):
            with open(USERS_DOSYASI, "r", encoding="utf-8") as f:
                try:
                    self.users = json.load(f)
                except json.JSONDecodeError:
                    self.users = {}

    def save_users(self):
        with open(USERS_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(self.users, f, indent=4)

    def hash_password(self, password, salt=None):
        if salt is None:
            salt = os.urandom(16)
        else:
            salt = bytes.fromhex(salt)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return f"{salt.hex()}:{pwd_hash.hex()}"

    def register(self, username, password):
        if username in self.users:
            return False, "Bu kullanıcı adı zaten alınmış."
        if not username or not password:
            return False, "Kullanıcı adı ve şifre boş olamaz."
        self.users[username] = self.hash_password(password)
        self.save_users()
        return True, "Kayıt başarılı."

    def login(self, username, password):
        if username not in self.users:
            return False
        stored_data = self.users[username]
        try:
            salt_hex, stored_hash_hex = stored_data.split(':')
            new_hash_data = self.hash_password(password, salt_hex)
            _, new_hash_hex = new_hash_data.split(':')
            if hmac.compare_digest(stored_hash_hex, new_hash_hex):
                return True
        except ValueError:
            return False 
        return False

# --- GİRİŞ EKRANI ---
class LoginWindow:
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.user_manager = UserManager()
        
        self.frame = tk.Frame(root, bg="#eceff1")
        self.frame.place(relwidth=1, relheight=1)

        box = tk.Frame(self.frame, bg="white", padx=40, pady=40, relief=tk.RAISED, borderwidth=1)
        box.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(box, text="Event Tracker", font=("Arial", 20, "bold"), bg="white", fg="#455a64").pack(pady=(0, 5))

        tk.Label(box, text=f"Sürüm: {MEVCUT_SURUM}", font=("Arial", 9), bg="white", fg="gray").pack(pady=(0, 20))

        tk.Label(box, text="Kullanıcı Adı:", bg="white", font=("Arial", 10)).pack(anchor="w")
        self.entry_user = tk.Entry(box, width=30, font=("Arial", 11))
        self.entry_user.pack(pady=(0, 10))

        tk.Label(box, text="Şifre:", bg="white", font=("Arial", 10)).pack(anchor="w")
        self.entry_pass = tk.Entry(box, width=30, show="*", font=("Arial", 11))
        self.entry_pass.pack(pady=(0, 20))
        self.entry_pass.bind('<Return>', lambda event: self.login())

        btn_frame = tk.Frame(box, bg="white")
        btn_frame.pack(fill=tk.X)

        tk.Button(btn_frame, text="Giriş Yap", command=self.login, bg="#4CAF50", fg="white", width=12, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Kayıt Ol", command=self.register, bg="#2196F3", fg="white", width=12, font=("Arial", 10, "bold")).pack(side=tk.RIGHT, padx=5)

    def login(self):
        u = self.entry_user.get().strip()
        p = self.entry_pass.get().strip()
        if self.user_manager.login(u, p):
            self.frame.destroy()
            self.on_login_success(u)
        else:
            messagebox.showerror("Hata", "Kullanıcı adı veya şifre hatalı.")

    def register(self):
        u = self.entry_user.get().strip()
        p = self.entry_pass.get().strip()
        success, msg = self.user_manager.register(u, p)
        if success:
            messagebox.showinfo("Başarılı", f"Kullanıcı oluşturuldu: {u}")
        else:
            messagebox.showerror("Hata", msg)

class EtkinlikTakipUygulamasi:
    def __init__(self, root, current_user, logout_callback):
        self.root = root
        self.current_user = current_user
        self.logout_callback = logout_callback
        self.json_dosya_adi = os.path.join(DATA_KLASORU, f"{self.current_user}.json")
        self.root.title(f"Etkinlik Takip Paneli - Kullanıcı: {self.current_user} ({MEVCUT_SURUM})")
        
        self.main_container = tk.Frame(root)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.veriler = {} 
        self.aktif_etkinlik_adi = tk.StringVar()
        self.tarih_listesi = [] 
        self.secilen_yil = tk.StringVar()

        self.veri_tabanini_yukle()

        main_pane = tk.PanedWindow(self.main_container, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        self.sidebar = tk.Frame(main_pane, width=280, bg="#f0f0f0", relief=tk.RIDGE, borderwidth=1)
        main_pane.add(self.sidebar)
        self.olustur_sidebar()

        self.content_frame = tk.Frame(main_pane, bg="white")
        main_pane.add(self.content_frame)

        self.etkinlik_degistir(None)
        self.karsilama_ekrani()
        
        UpdateManager.kontrol_et(manuel=False)

    def veri_tabanini_yukle(self):
        if os.path.exists(self.json_dosya_adi):
            with open(self.json_dosya_adi, "r", encoding="utf-8") as f:
                try: self.veriler = json.load(f)
                except json.JSONDecodeError: self.veriler = {}
        if not self.veriler and os.path.exists(ESKI_TXT_DOSYA_ADI):
            if messagebox.askyesno("Veri Aktarımı", "Eski veriler bulundu. Hesabınıza aktarılsın mı?"):
                eski = []
                with open(ESKI_TXT_DOSYA_ADI, "r") as f:
                    for s in f:
                        c = s.split(']')[-1].strip() if ']' in s else s.strip()
                        if c: eski.append(c)
                self.veriler["Genel Etkinlik"] = eski
                self.json_kaydet()
        if not self.veriler:
            self.veriler = {"Genel Etkinlik": []}
            self.json_kaydet()

    def json_kaydet(self):
        with open(self.json_dosya_adi, "w", encoding="utf-8") as f:
            json.dump(self.veriler, f, ensure_ascii=False, indent=4)

    def aktif_verileri_yukle(self):
        secili = self.aktif_etkinlik_adi.get()
        if not secili or secili not in self.veriler:
            if self.veriler: secili = list(self.veriler.keys())[0]; self.aktif_etkinlik_adi.set(secili)
            else: self.tarih_listesi = []; return
        raw = self.veriler[secili]
        self.tarih_listesi = []
        for d in raw:
            try: self.tarih_listesi.append(datetime.strptime(d, "%d.%m.%Y"))
            except ValueError: continue
        self.tarih_listesi.sort()
        self.guncelle_yil_combo()

    def cikis_yap(self):
        if messagebox.askyesno("Çıkış", "Oturumu kapatmak istiyor musunuz?"):
            self.main_container.destroy()
            self.logout_callback()

    def olustur_sidebar(self):
        uf = tk.Frame(self.sidebar, bg="#cfd8dc", pady=10); uf.pack(fill=tk.X)
        tk.Label(uf, text=f"👤 {self.current_user}", bg="#cfd8dc", font=("Arial", 12, "bold")).pack()
        
        tk.Label(self.sidebar, text="Aktif Etkinlik:", bg="#f0f0f0", font=("Arial", 10, "bold")).pack(pady=(10, 2))
        self.combo_etkinlik = ttk.Combobox(self.sidebar, textvariable=self.aktif_etkinlik_adi, state="readonly", width=22)
        self.combo_etkinlik['values'] = list(self.veriler.keys())
        if self.veriler: self.combo_etkinlik.current(0)
        self.combo_etkinlik.bind("<<ComboboxSelected>>", self.etkinlik_degistir)
        self.combo_etkinlik.pack(pady=2)
        tk.Button(self.sidebar, text="⚙️ Etkinlikleri Yönet", command=self.etkinlik_yonetimi_penceresi, bg="#607d8b", fg="white", width=22).pack(pady=5)
        
        ttk.Separator(self.sidebar, orient='horizontal').pack(fill='x', padx=10, pady=10)
        tk.Label(self.sidebar, text="Çalışma Yılı:", bg="#f0f0f0").pack(pady=(5, 2))
        self.yil_combo = ttk.Combobox(self.sidebar, textvariable=self.secilen_yil, state="readonly", width=18)
        self.yil_combo.pack(pady=2)
        
        tk.Label(self.sidebar, text="Hızlı Tarih Ekle:", bg="#f0f0f0").pack(pady=(15, 2))
        self.cal_entry = DateEntry(self.sidebar, width=16, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd.mm.yyyy', locale='tr_TR')
        self.cal_entry.pack(pady=2)
        tk.Button(self.sidebar, text="Ekle", command=self.tarih_ekle, bg="#4CAF50", fg="white", width=22).pack(pady=5)
        
        ttk.Separator(self.sidebar, orient='horizontal').pack(fill='x', padx=10, pady=20)
        btn_style = {"width": 24, "pady": 2, "bg": "white", "anchor": "w", "padx": 10}
        tk.Button(self.sidebar, text="📋 Kayıt Listesi & Düzenle", command=self.veri_yonetimi_goster, **btn_style).pack(pady=2)
        tk.Button(self.sidebar, text="📈 Zaman Çizelgesi", command=self.grafik_goster, **btn_style).pack(pady=2)
        tk.Button(self.sidebar, text="🟩 Yoğunluk Haritası", command=self.isi_haritasi_goster, **btn_style).pack(pady=2)
        tk.Button(self.sidebar, text="📊 Fark Analizi", command=self.fark_grafik_goster, **btn_style).pack(pady=2)
        tk.Button(self.sidebar, text="📊 Alışkanlık Histogramı", command=self.histogram_goster, **btn_style).pack(pady=2)
        tk.Button(self.sidebar, text="📅 Aylık Dağılım", command=self.aylik_ozet_goster, **btn_style).pack(pady=2)
        
        ttk.Separator(self.sidebar, orient='horizontal').pack(fill='x', padx=10, pady=10)
        tk.Button(self.sidebar, text="🔄 Güncellemeleri Kontrol Et", command=lambda: UpdateManager.kontrol_et(manuel=True), bg="#e0f7fa", width=24).pack(pady=5)

        tk.Button(self.sidebar, text="🚪 Çıkış Yap", command=self.cikis_yap, bg="#ffab91", width=22).pack(side=tk.BOTTOM, pady=20)
        self.lbl_bilgi = tk.Label(self.sidebar, text="", bg="#f0f0f0", fg="blue", wraplength=200); self.lbl_bilgi.pack(side=tk.BOTTOM, pady=5)

    def etkinlik_degistir(self, event):
        self.aktif_verileri_yukle()
        self.lbl_bilgi.config(text=f"Seçili: {self.aktif_etkinlik_adi.get()}", fg="#333")
        self.temizle_sag_panel()
        self.karsilama_ekrani()

    def etkinlik_yonetimi_penceresi(self):
        top = tk.Toplevel(self.root); top.title("Etkinlik Yönetimi"); top.geometry("400x400")
        tk.Label(top, text="Kayıtlı Etkinlikler:", font=("Arial", 10, "bold")).pack(pady=10)
        listbox = tk.Listbox(top, font=("Arial", 11)); listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        for k in self.veriler.keys(): listbox.insert(tk.END, k)
        btn_frame = tk.Frame(top); btn_frame.pack(pady=10)
        
        def yeni():
            ad = simpledialog.askstring("Yeni", "Etkinlik Adı:")
            if ad:
                if ad in self.veriler: messagebox.showerror("Hata", "Mevcut")
                else: self.veriler[ad]=[]; self.json_kaydet(); listbox.insert(tk.END, ad); self.combo_etkinlik['values']=list(self.veriler.keys()); self.combo_etkinlik.set(ad); self.etkinlik_degistir(None)
        def sil():
            sel = listbox.curselection()
            if not sel: return
            ad = listbox.get(sel)
            if len(self.veriler)==1: messagebox.showwarning("Uyarı", "Son etkinlik silinemez."); return
            if messagebox.askyesno("Sil", f"'{ad}' silinsin mi?"): del self.veriler[ad]; self.json_kaydet(); listbox.delete(sel); self.combo_etkinlik['values']=list(self.veriler.keys()); self.combo_etkinlik.current(0); self.etkinlik_degistir(None)
        def duzenle():
            sel = listbox.curselection()
            if not sel: return
            eski = listbox.get(sel)
            yeni = simpledialog.askstring("Düzenle", "Yeni Ad:", initialvalue=eski)
            if yeni and yeni!=eski:
                if yeni in self.veriler: messagebox.showerror("Hata", "Mevcut")
                else: self.veriler[yeni]=self.veriler.pop(eski); self.json_kaydet(); listbox.delete(sel); listbox.insert(sel, yeni); self.combo_etkinlik['values']=list(self.veriler.keys()); self.combo_etkinlik.set(yeni); self.aktif_verileri_yukle()

        tk.Button(btn_frame, text="➕ Yeni", command=yeni, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="✏️ Düzenle", command=duzenle, bg="#FFC107").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ Sil", command=sil, bg="#F44336", fg="white").pack(side=tk.LEFT, padx=5)

    def karsilama_ekrani(self):
        self.temizle_sag_panel()
        secili = self.aktif_etkinlik_adi.get()
        sayi = len(self.tarih_listesi)
        frame = tk.Frame(self.content_frame, bg="white")
        frame.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(frame, text=f"Hoşgeldin, {self.current_user}!", font=("Arial", 16), bg="white", fg="#607d8b").pack(pady=5)
        tk.Label(frame, text=f"Aktif Etkinlik: {secili}", font=("Arial", 20, "bold"), bg="white", fg="#333").pack(pady=10)
        tk.Label(frame, text=f"Toplam Kayıt: {sayi}", font=("Arial", 14), bg="white", fg="#666").pack(pady=5)

    def temizle_sag_panel(self):
        for widget in self.content_frame.winfo_children(): widget.destroy()
    def grafigi_panele_gom(self, fig):
        self.temizle_sag_panel(); canvas = FigureCanvasTkAgg(fig, master=self.content_frame); canvas.draw()
        toolbar_frame = tk.Frame(self.content_frame); toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame); toolbar.update()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def guncelle_yil_combo(self):
        curr = self.secilen_yil.get()
        yillar = sorted(list(set(t.year for t in self.tarih_listesi)), reverse=True) if self.tarih_listesi else []
        vals = ["Tümü"] + [str(y) for y in yillar]
        self.yil_combo['values'] = vals
        if curr in vals: self.secilen_yil.set(curr)
        else: self.secilen_yil.set("Tümü")
    def get_filtrelenmis_tarihler(self):
        sel = self.secilen_yil.get()
        if sel == "Tümü" or not sel: return sorted(self.tarih_listesi)
        try: return sorted([t for t in self.tarih_listesi if t.year == int(sel)])
        except: return sorted(self.tarih_listesi)
    def tarih_ekle(self):
        t_str = self.cal_entry.get_date().strftime("%d.%m.%Y"); akt = self.aktif_etkinlik_adi.get()
        if t_str in self.veriler[akt]: messagebox.showwarning("Bilgi", "Zaten ekli."); return
        self.veriler[akt].append(t_str); self.json_kaydet(); self.aktif_verileri_yukle(); self.lbl_bilgi.config(text=f"Eklendi: {t_str} ({akt})", fg="green")
        if hasattr(self, 'tree_widget') and self.tree_widget.winfo_exists(): self.veri_yonetimi_goster()

    def veri_yonetimi_goster(self):
        self.temizle_sag_panel()
        fr = tk.Frame(self.content_frame, bg="white"); fr.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(fr, text=f"Liste: {self.aktif_etkinlik_adi.get()}", font=("Arial", 12, "bold"), bg="white").pack(side=tk.LEFT)
        bf = tk.Frame(fr, bg="white"); bf.pack(side=tk.RIGHT)
        tk.Button(bf, text="✏️ Düzenle", command=self.kayit_duzenle, bg="#fff0c2").pack(side=tk.LEFT, padx=5)
        tk.Button(bf, text="🗑️ Sil", command=self.kayit_sil, bg="#ffcccc", fg="red").pack(side=tk.LEFT, padx=5)
        
        cols = ('tarih', 'gun')
        self.tree_widget = ttk.Treeview(self.content_frame, columns=cols, show='headings', height=20)
        self.tree_widget.heading('tarih', text='Tarih'); self.tree_widget.heading('gun', text='Gün')
        self.tree_widget.column('tarih', width=150, anchor='center'); self.tree_widget.column('gun', width=150, anchor='center')
        
        sb = ttk.Scrollbar(self.content_frame, orient=tk.VERTICAL, command=self.tree_widget.yview)
        self.tree_widget.configure(yscroll=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        for t in reversed(self.get_filtrelenmis_tarihler()):
            self.tree_widget.insert('', tk.END, values=(t.strftime("%d.%m.%Y"), t.strftime("%A")))

    def kayit_sil(self):
        selected = self.tree_widget.selection()
        if not selected: return
        tarih_str = self.tree_widget.item(selected, "values")[0]
        if messagebox.askyesno("Onay", f"{tarih_str} silinsin mi?"):
            aktif = self.aktif_etkinlik_adi.get()
            if tarih_str in self.veriler[aktif]:
                self.veriler[aktif].remove(tarih_str)
                self.json_kaydet()
                self.aktif_verileri_yukle()
                self.veri_yonetimi_goster()
                self.lbl_bilgi.config(text=f"Silindi: {tarih_str}", fg="red")

    def kayit_duzenle(self):
        selected = self.tree_widget.selection()
        if not selected: return
        eski_str = self.tree_widget.item(selected, "values")[0]
        eski_dt = datetime.strptime(eski_str, "%d.%m.%Y")
        
        top = tk.Toplevel(self.root)
        top.title("Düzenle")
        top.geometry("300x150")
        tk.Label(top, text=f"Eski: {eski_str}").pack(pady=10)
        ent = DateEntry(top, width=16, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd.mm.yyyy', locale='tr_TR')
        ent.set_date(eski_dt)
        ent.pack(pady=5)
        
        def kaydet():
            yeni_str = ent.get_date().strftime("%d.%m.%Y")
            aktif = self.aktif_etkinlik_adi.get()
            if eski_str in self.veriler[aktif]:
                self.veriler[aktif].remove(eski_str)
                self.veriler[aktif].append(yeni_str)
                self.json_kaydet()
                self.aktif_verileri_yukle()
                self.veri_yonetimi_goster()
                top.destroy()
            else: messagebox.showerror("Hata", "Kayıt bulunamadı.")
        tk.Button(top, text="Kaydet", command=kaydet, bg="#4CAF50", fg="white").pack(pady=10)

    def grafik_goster(self):
        tarih_listesi = self.get_filtrelenmis_tarihler()
        if not tarih_listesi: messagebox.showerror("Hata", "Veri yok."); return
        tarih_listesi.sort()
        sayilar = list(range(1, len(tarih_listesi) + 1))
        fig = Figure(figsize=(12, 7), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(tarih_listesi, sayilar, marker='o', linestyle='-', zorder=10)
        ax.set_title(f"Timeline: {self.aktif_etkinlik_adi.get()} ({self.secilen_yil.get()})")
        ax.set_ylabel("Toplam Sayı"); ax.grid(True, alpha=0.5)
        ax.text(tarih_listesi[-1], len(tarih_listesi), f"{len(tarih_listesi)}", fontsize=9, ha='right', color='blue', fontweight='bold')
        
        secim = self.secilen_yil.get(); bugun = datetime.today()
        if secim == "Tümü" or not secim: ilk_tarih = min(tarih_listesi); son_gun = bugun
        else: yil = int(secim); ilk_tarih = datetime(yil, 1, 1); son_gun = min(datetime(yil, 12, 31), bugun)
        ax.set_xlim(ilk_tarih, son_gun)
        
        ilk_pazartesi = ilk_tarih - timedelta(days=ilk_tarih.weekday())
        son_pazartesi = son_gun - timedelta(days=son_gun.weekday())
        hafta_durumu = defaultdict(list)
        for t in tarih_listesi: hafta_durumu[t - timedelta(days=t.weekday())].append(t)
        
        cur = ilk_pazartesi
        y_txt = max(sayilar)/2 if sayilar else 10
        while cur <= son_pazartesi:
            cnt = len(hafta_durumu[cur])
            if cnt==0: c,a,t="red",0.05,"Yok"
            elif cnt==1: c,a,t="orange",0.05,"1"
            elif cnt==2: c,a,t="green",0.08,"2"
            elif cnt==3: c,a,t="blue",0.08,"3"
            else: c,a,t="purple",0.1,"4+"
            ax.axvspan(cur, cur+timedelta(days=6), alpha=a, color=c)
            ax.text(cur+timedelta(days=3.5), y_txt, t, rotation=90, ha='center', fontsize=8, color=c, fontweight='bold', alpha=0.7)
            cur += timedelta(weeks=1)
        
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%B %Y'))
        fig.autofmt_xdate(rotation=45, ha='right')
        self.grafigi_panele_gom(fig)

    def histogram_goster(self):
        tarih_listesi = self.get_filtrelenmis_tarihler()
        if len(tarih_listesi) < 1: messagebox.showwarning("Uyarı", "Veri yok."); return
        tarih_listesi.sort()
        gap_pairs = defaultdict(list); farklar = []
        for i in range(1, len(tarih_listesi)):
            diff = (tarih_listesi[i] - tarih_listesi[i-1]).days
            if diff > 0: farklar.append(diff); gap_pairs[diff].append((tarih_listesi[i-1], tarih_listesi[i]))
        bugun = datetime.today(); son = tarih_listesi[-1]; diff_son = (bugun - son).days
        if diff_son > 0: farklar.append(diff_son); gap_pairs[diff_son].append((son, bugun))
        if not farklar: messagebox.showwarning("Bilgi", "Aralık yok."); return
        
        counts = Counter(farklar); days = sorted(counts.keys()); freqs = [counts[d] for d in days]
        fig = Figure(figsize=(10, 6), dpi=100); ax = fig.add_subplot(111)
        colors = ['#66bb6a' if d<=3 else '#ffa726' if d<=7 else '#ef5350' for d in days]
        bars = ax.bar(days, freqs, color=colors, edgecolor='black', alpha=0.8, picker=True)
        ax.set_title(f"Sıklık: {self.aktif_etkinlik_adi.get()}"); ax.set_xticks(days); ax.grid(True, axis='y', alpha=0.3)
        for bar in bars: ax.text(bar.get_x()+bar.get_width()/2., bar.get_height(), f'{int(bar.get_height())}', ha='center', va='bottom')
        
        def on_pick(event):
            if isinstance(event.artist, Rectangle):
                d = int(round(event.artist.get_x() + event.artist.get_width() / 2))
                if d in gap_pairs: self.detay_penceresi_goster(d, gap_pairs[d])
        fig.canvas.mpl_connect('pick_event', on_pick)
        self.grafigi_panele_gom(fig)

    def detay_penceresi_goster(self, gun, pairs):
        top = tk.Toplevel(self.root); top.title(f"{gun} Günlük"); top.geometry("400x300")
        tk.Label(top, text=f"{len(pairs)} Kez, {gun} Gün Ara:", font=("Arial", 11, "bold")).pack(pady=10)
        fr = tk.Frame(top); fr.pack(fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(fr, orient=tk.VERTICAL); lb = tk.Listbox(fr, yscrollcommand=sb.set, font=("Consolas", 10))
        sb.config(command=lb.yview); sb.pack(side=tk.RIGHT, fill=tk.Y); lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        today = datetime.today().date()
        for i, (t1, t2) in enumerate(pairs, 1):
            if t2.date() == today: lb.insert(tk.END, f"{i}. {t1.strftime('%d.%m')} -> Bugün (GÜNCEL)"); lb.itemconfig(tk.END, {'bg': '#fff9c4'})
            else: lb.insert(tk.END, f"{i}. {t1.strftime('%d.%m')} -> {t2.strftime('%d.%m')}")

    def isi_haritasi_goster(self):
        secim = self.secilen_yil.get()
        hedef = datetime.now().year if secim == "Tümü" or not secim else int(secim)
        liste = [t for t in self.tarih_listesi if t.year == hedef]
        counts = Counter(t.date() for t in liste)
        start = datetime(hedef, 1, 1); end = datetime(hedef, 12, 31)
        xh, yg, clr = [], [], []
        def get_color(c): return "#ebedf0" if c==0 else "#9be9a8" if c==1 else "#40c463" if c==2 else "#30a14e" if c==3 else "#216e39"
        cur = start
        while cur <= end:
            xh.append(int(cur.strftime("%W"))); yg.append(6 - cur.weekday()); clr.append(get_color(counts[cur.date()])); cur += timedelta(days=1)
        fig = Figure(figsize=(12, 5), dpi=100); ax = fig.add_subplot(111)
        ax.scatter(xh, yg, c=clr, marker='s', s=180)
        ax.set_title(f"{hedef} Yoğunluk (Top: {len(liste)})"); ax.set_yticks([0, 2, 4, 6]); ax.set_yticklabels(["Paz", "Cum", "Çar", "Pzt"])
        lbls, tcks = [], []
        for m in range(1, 13): d=datetime(hedef, m, 1); tcks.append(int(d.strftime("%W"))); lbls.append(d.strftime("%b"))
        ax.set_xticks(tcks); ax.set_xticklabels(lbls); ax.set_aspect('equal')
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False); ax.spines['left'].set_visible(False); ax.spines['bottom'].set_visible(False); ax.tick_params(length=0)
        patches = [Patch(facecolor=get_color(i), label=str(i) if i<4 else "4+") for i in range(5)]
        ax.legend(handles=patches, loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=5, frameon=False); fig.subplots_adjust(bottom=0.2)
        self.grafigi_panele_gom(fig)

    def fark_grafik_goster(self):
        self.histogram_goster() # Basitlik için yönlendirme

    def aylik_ozet_goster(self):
        s=self.secilen_yil.get()
        if s=="Tümü": messagebox.showwarning("Uyarı","Yıl seç"); return
        l=self.get_filtrelenmis_tarihler(); c=Counter(t.month for t in l)
        mn=["Oca","Şub","Mar","Nis","May","Haz","Tem","Ağu","Eyl","Eki","Kas","Ara"]; v=[c[i] for i in range(1,13)]
        fig=Figure(figsize=(8,6), dpi=100); ax=fig.add_subplot(111); b=ax.bar(mn, v, color='cornflowerblue')
        for x in b: 
            if x.get_height()>0: ax.text(x.get_x()+x.get_width()/2, x.get_height(), str(int(x.get_height())), ha='center', va='bottom')
        self.grafigi_panele_gom(fig)

def main():
    root = tk.Tk(); root.geometry("400x300")
    def start(u): 
        for w in root.winfo_children(): w.destroy()
        root.geometry("1200x800"); EtkinlikTakipUygulamasi(root, u, restart)
    def restart(): 
        for w in root.winfo_children(): w.destroy()
        root.geometry("400x350"); LoginWindow(root, start)
    restart(); root.mainloop()

if __name__ == "__main__": main()