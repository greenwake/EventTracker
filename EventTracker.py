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

# --- SABİTLER VE AYARLAR ---
DATA_KLASORU = "Data"
USERS_DOSYASI = "users.json"
ESKI_TXT_DOSYA_ADI = "eventList.txt"

if not os.path.exists(DATA_KLASORU):
    os.makedirs(DATA_KLASORU)

# --- GÜVENLİ KULLANICI YÖNETİCİSİ (Salt + PBKDF2) ---
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
        """
        Şifreyi Tuzlama (Salting) ve PBKDF2 ile güvenli hale getirir.
        Format: salt_hex:hash_hex
        """
        if salt is None:
            # Yeni kayıt için 16 byte'lık rastgele tuz oluştur
            salt = os.urandom(16)
        else:
            # Giriş kontrolü için mevcut tuzu kullan
            salt = bytes.fromhex(salt)

        # PBKDF2 algoritması: 100.000 iterasyon (Kırılması çok güç)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        
        # Salt ve Hash'i birleştirip kaydet (salt olmadan hash doğrulanamaz)
        return f"{salt.hex()}:{pwd_hash.hex()}"

    def register(self, username, password):
        if username in self.users:
            return False, "Bu kullanıcı adı zaten alınmış."
        if not username or not password:
            return False, "Kullanıcı adı ve şifre boş olamaz."
        
        # Şifreyi tuzlayarak kaydet
        self.users[username] = self.hash_password(password)
        self.save_users()
        return True, "Kayıt başarılı."

    def login(self, username, password):
        if username not in self.users:
            return False
        
        stored_data = self.users[username]
        try:
            salt_hex, stored_hash_hex = stored_data.split(':')
            
            # Girilen şifreyi, kayıtlı TUZ ile tekrar şifrele
            new_hash_data = self.hash_password(password, salt_hex)
            _, new_hash_hex = new_hash_data.split(':')
            
            # Zamanlama saldırılarını önlemek için güvenli karşılaştırma (hmac.compare_digest)
            if hmac.compare_digest(stored_hash_hex, new_hash_hex):
                return True
        except ValueError:
            return False # Veri bozulmuşsa giriş yapma
            
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

        tk.Label(box, text="Event Tracker v13", font=("Arial", 20, "bold"), bg="white", fg="#455a64").pack(pady=(0, 20))
        tk.Label(box, text="Güvenli Giriş (Salted SHA256)", font=("Arial", 8), bg="white", fg="green").pack(pady=(0, 10))

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

# --- ANA UYGULAMA (Geri kalan kısım v12 ile aynı mantıkta) ---
class EtkinlikTakipUygulamasi:
    def __init__(self, root, current_user, logout_callback):
        self.root = root
        self.current_user = current_user
        self.logout_callback = logout_callback
        self.json_dosya_adi = os.path.join(DATA_KLASORU, f"{self.current_user}.json")
        self.root.title(f"Etkinlik Takip Paneli - Kullanıcı: {self.current_user}")
        
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
        btn_style = {"width": 24, "pady": 4, "bg": "white", "anchor": "w", "padx": 10}
        tk.Button(self.sidebar, text="📋 Kayıt Listesi & Düzenle", command=self.veri_yonetimi_goster, **btn_style).pack(pady=2)
        tk.Button(self.sidebar, text="📈 Zaman Çizelgesi", command=self.grafik_goster, **btn_style).pack(pady=2)
        tk.Button(self.sidebar, text="🟩 Yoğunluk Haritası", command=self.isi_haritasi_goster, **btn_style).pack(pady=2)
        tk.Button(self.sidebar, text="📊 Fark Analizi", command=self.fark_grafik_goster, **btn_style).pack(pady=2)
        tk.Button(self.sidebar, text="📊 Alışkanlık Histogramı", command=self.histogram_goster, **btn_style).pack(pady=2)
        tk.Button(self.sidebar, text="📅 Aylık Dağılım", command=self.aylik_ozet_goster, **btn_style).pack(pady=2)
        tk.Button(self.sidebar, text="🚪 Çıkış Yap", command=self.cikis_yap, bg="#ffab91", width=22).pack(side=tk.BOTTOM, pady=20)
        self.lbl_bilgi = tk.Label(self.sidebar, text="", bg="#f0f0f0", fg="blue", wraplength=200); self.lbl_bilgi.pack(side=tk.BOTTOM, pady=5)

    def etkinlik_degistir(self, event):
        self.aktif_verileri_yukle()
        self.lbl_bilgi.config(text=f"Seçili: {self.aktif_etkinlik_adi.get()}", fg="#333")
        self.temizle_sag_panel()
        self.karsilama_ekrani()

    def karsilama_ekrani(self):
        self.temizle_sag_panel()
        secili = self.aktif_etkinlik_adi.get()
        sayi = len(self.tarih_listesi)
        frame = tk.Frame(self.content_frame, bg="white")
        frame.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(frame, text=f"Hoşgeldin, {self.current_user}!", font=("Arial", 16), bg="white", fg="#607d8b").pack(pady=5)
        tk.Label(frame, text=f"Aktif Etkinlik: {secili}", font=("Arial", 20, "bold"), bg="white", fg="#333").pack(pady=10)
        tk.Label(frame, text=f"Toplam Kayıt: {sayi}", font=("Arial", 14), bg="white", fg="#666").pack(pady=5)

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
        self.veriler[akt].append(t_str); self.json_kaydet(); self.aktif_verileri_yukle(); self.lbl_bilgi.config(text=f"Eklendi: {t_str}", fg="green")
        if hasattr(self, 'tree_widget') and self.tree_widget.winfo_exists(): self.veri_yonetimi_goster()

    def veri_yonetimi_goster(self):
        self.temizle_sag_panel()
        fr = tk.Frame(self.content_frame, bg="white"); fr.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(fr, text=f"Liste: {self.aktif_etkinlik_adi.get()}", font=("Arial", 12, "bold"), bg="white").pack(side=tk.LEFT)
        bf = tk.Frame(fr, bg="white"); bf.pack(side=tk.RIGHT)
        tk.Button(bf, text="✏️ Düzenle", command=self.kayit_duzenle, bg="#fff0c2").pack(side=tk.LEFT, padx=5)
        tk.Button(bf, text="🗑️ Sil", command=self.kayit_sil, bg="#ffcccc", fg="red").pack(side=tk.LEFT, padx=5)
        self.tree_widget = ttk.Treeview(self.content_frame, columns=('t','g'), show='headings', height=20)
        self.tree_widget.heading('t', text='Tarih'); self.tree_widget.heading('g', text='Gün')
        self.tree_widget.column('t', anchor='center'); self.tree_widget.column('g', anchor='center')
        sb = ttk.Scrollbar(self.content_frame, orient=tk.VERTICAL, command=self.tree_widget.yview); self.tree_widget.configure(yscroll=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y); self.tree_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=5)
        for t in reversed(self.get_filtrelenmis_tarihler()): self.tree_widget.insert('', tk.END, values=(t.strftime("%d.%m.%Y"), t.strftime("%A")))

    def kayit_sil(self):
        sel = self.tree_widget.selection()
        if not sel: return
        t_str = self.tree_widget.item(sel, "values")[0]
        if messagebox.askyesno("Onay", "Silinsin mi?"):
            akt = self.aktif_etkinlik_adi.get()
            self.veriler[akt].remove(t_str); self.json_kaydet(); self.aktif_verileri_yukle(); self.veri_yonetimi_goster()
    def kayit_duzenle(self):
        sel = self.tree_widget.selection()
        if not sel: return
        eski = self.tree_widget.item(sel, "values")[0]
        top = tk.Toplevel(self.root); top.title("Düzenle"); top.geometry("300x150")
        tk.Label(top, text=f"Eski: {eski}").pack(pady=10)
        ent = DateEntry(top, locale='tr_TR'); ent.set_date(datetime.strptime(eski, "%d.%m.%Y")); ent.pack(pady=5)
        def sav():
            yeni = ent.get_date().strftime("%d.%m.%Y"); akt = self.aktif_etkinlik_adi.get()
            self.veriler[akt].remove(eski); self.veriler[akt].append(yeni); self.json_kaydet(); self.aktif_verileri_yukle(); self.veri_yonetimi_goster(); top.destroy()
        tk.Button(top, text="Kaydet", command=sav, bg="#4CAF50").pack(pady=10)

    # --- GRAFİKLER ---
    def grafik_goster(self):
        tl = self.get_filtrelenmis_tarihler()
        if not tl: messagebox.showerror("Hata", "Veri yok."); return
        tl.sort(); num = list(range(1, len(tl)+1))
        fig = Figure(figsize=(12, 7), dpi=100); ax = fig.add_subplot(111)
        ax.plot(tl, num, marker='o', linestyle='-', zorder=10); ax.grid(True, alpha=0.5)
        ax.set_title(f"Timeline: {self.aktif_etkinlik_adi.get()}"); ax.text(tl[-1], len(tl), str(len(tl)), ha='right', color='blue', fontweight='bold')
        sel = self.secilen_yil.get(); tod = datetime.today()
        if sel=="Tümü" or not sel: s=min(tl); e=tod
        else: s=datetime(int(sel),1,1); e=min(datetime(int(sel),12,31), tod)
        ax.set_xlim(s, e)
        hd = defaultdict(list)
        for t in tl: hd[t-timedelta(days=t.weekday())].append(t)
        cur = s - timedelta(days=s.weekday())
        end_w = e - timedelta(days=e.weekday())
        ymax = max(num)/2 if num else 10
        while cur <= end_w:
            c = len(hd[cur])
            if c==0: col,a,tx="red",0.05,"Yok"
            elif c==1: col,a,tx="orange",0.05,"1"
            elif c==2: col,a,tx="green",0.08,"2"
            else: col,a,tx="blue",0.1,"3+"
            ax.axvspan(cur, cur+timedelta(days=6), alpha=a, color=col)
            ax.text(cur+timedelta(days=3.5), ymax, tx, rotation=90, ha='center', fontsize=8, color=col, alpha=0.7)
            cur+=timedelta(weeks=1)
        ax.xaxis.set_major_locator(mdates.MonthLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter('%B %Y')); fig.autofmt_xdate(); self.grafigi_panele_gom(fig)

    def histogram_goster(self):
        tl = self.get_filtrelenmis_tarihler()
        if len(tl)<1: messagebox.showwarning("Uyarı","Veri yok"); return
        tl.sort(); gps=defaultdict(list); diffs=[]
        for i in range(1, len(tl)):
            d=(tl[i]-tl[i-1]).days; 
            if d>0: diffs.append(d); gps[d].append((tl[i-1], tl[i]))
        ls=(datetime.today()-tl[-1]).days
        if ls>0: diffs.append(ls); gps[ls].append((tl[-1], datetime.today()))
        if not diffs: messagebox.showwarning("Bilgi","Aralık yok"); return
        c=Counter(diffs); d=sorted(c.keys()); f=[c[k] for k in d]
        fig=Figure(figsize=(10,6), dpi=100); ax=fig.add_subplot(111)
        cols=['#66bb6a' if x<=3 else '#ef5350' for x in d]
        bars=ax.bar(d, f, color=cols, picker=True)
        ax.set_title("Alışkanlık Sıklığı"); ax.set_xticks(d)
        for b in bars: ax.text(b.get_x()+b.get_width()/2, b.get_height(), str(int(b.get_height())), ha='center', va='bottom')
        def pk(ev): 
            if isinstance(ev.artist, Rectangle): 
                v=int(round(ev.artist.get_x()+ev.artist.get_width()/2))
                if v in gps: self.detay_penceresi_goster(v, gps[v])
        fig.canvas.mpl_connect('pick_event', pk); self.grafigi_panele_gom(fig)

    def detay_penceresi_goster(self, gun, pairs):
        top=tk.Toplevel(self.root); top.title(f"{gun} Gün"); top.geometry("400x300")
        fr=tk.Frame(top); fr.pack(fill=tk.BOTH, expand=True)
        sb=ttk.Scrollbar(fr, orient=tk.VERTICAL); lb=tk.Listbox(fr, yscrollcommand=sb.set); sb.config(command=lb.yview); sb.pack(side=tk.RIGHT, fill=tk.Y); lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tod=datetime.today().date()
        for i, (t1,t2) in enumerate(pairs, 1):
            if t2.date()==tod: lb.insert(tk.END, f"{i}. {t1.strftime('%d.%m')} -> Bugün"); lb.itemconfig(tk.END, {'bg':'#fff9c4'})
            else: lb.insert(tk.END, f"{i}. {t1.strftime('%d.%m')} -> {t2.strftime('%d.%m')}")

    def isi_haritasi_goster(self):
        s=self.secilen_yil.get(); y=datetime.now().year if s=="Tümü" or not s else int(s)
        l=[t for t in self.tarih_listesi if t.year==y]; c=Counter(t.date() for t in l)
        st=datetime(y,1,1); en=datetime(y,12,31); x,yy,cl=[],[],[]
        curr=st
        while curr<=en: x.append(int(curr.strftime("%W"))); yy.append(6-curr.weekday()); v=c[curr.date()]; cl.append("#ebedf0" if v==0 else "#9be9a8" if v==1 else "#30a14e"); curr+=timedelta(days=1)
        fig=Figure(figsize=(12,5), dpi=100); ax=fig.add_subplot(111); ax.scatter(x,yy,c=cl,marker='s',s=180); ax.set_title(f"{y} Yoğunluk"); ax.set_aspect('equal')
        ax.set_yticks([0,2,4,6]); ax.set_yticklabels(["Paz","Cum","Çar","Pzt"]); ax.axis('off'); self.grafigi_panele_gom(fig)

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