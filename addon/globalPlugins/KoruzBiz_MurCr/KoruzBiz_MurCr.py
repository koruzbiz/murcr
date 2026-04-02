# -*- coding: utf-8 -*-
# Plug-in version: 2.2.2
# MurCr compatible version: 2.2.2

import os
import subprocess
import webbrowser
import winreg as reg
import winreg
import json
import wx
import scriptHandler
from config import conf

# Log kaydı yapmak isterseniz 'logger_pz' değerini 'True' yapın.
logger_pz = False

from ._log import baslat_loglama
LOG_DIZINI = os.path.dirname(os.path.abspath(__file__))
logger = baslat_loglama(
    appdata_dir=LOG_DIZINI,
    eklenti_adi="MurCr",
    stdout_yonlendir=False,
    aktif=logger_pz,
    excepthook_kur=logger_pz
)

import speech
import api
import ui
from scriptHandler import script
from keyboardHandler import KeyboardInputGesture as KIG

from . import tr

import globalPluginHandler
_BaseGlobalPlugin = getattr(globalPluginHandler, "GlobalPlugin", None)

# NVDA rol sabitleri
try:
    from controlTypes import Role
    ROLE_POPUPMENU = Role.POPUPMENU
    ROLE_MENU = Role.MENU
    ROLE_MENUITEM = Role.MENUITEM
except Exception:
    Role = None
    ROLE_POPUPMENU = ROLE_MENU = ROLE_MENUITEM = None

ALLOWED_EXTS = (".opus", ".mp3", ".mp4", ".m4a", ".mpeg", ".aac", ".flac", ".ogg", ".wav", ".dat", ".waptt")

MurCr_path = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.join(os.path.expanduser("~"), "AppData", "Local")),
    "Koruz_Biz",
    "MurCr",
    "MurCr.exe",
)

MurCr_INSTALLED = False

APP_DESKTOP = "desktop"
APP_EXPLORER = "explorer"
APP_UNKNOWN = "unknown"

SECTION = "KoruzBiz_MurCr"
KEY_OUTPUT_DIR = "outputDir"

def eklenti_ayarlarini_config_ile_senkronla():
    try:
        p = murcr_configten_file_pt_oku()
        if not p:
            return False
        if SECTION not in conf:
            conf[SECTION] = {}
        mevcut = (conf[SECTION].get(KEY_OUTPUT_DIR) or "").strip()
        mevcut = os.path.normpath(mevcut) if mevcut else ""
        if mevcut != p:
            conf[SECTION][KEY_OUTPUT_DIR] = p
            conf.save()
            logger.info(f"[Config] outputDir güncellendi: {mevcut} -> {p}")
        else:
            logger.info("[Config] outputDir zaten güncel")
        return True
    except Exception as e:
        logger.error(f"[Config] Senkron hata: {e}")
        return False

def _murcr_config_yolu():
    appdata = os.getenv("APPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    return os.path.join(appdata, "Koruz_Biz", "murcr", "config.txt")

def murcr_configten_file_pt_oku():
    try:
        cfg_path = _murcr_config_yolu()
        if not os.path.isfile(cfg_path):
            logger.info(f"[Config] Bulunamadı: {cfg_path}")
            return None
        with open(cfg_path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        p = (data.get("file_pt") or "").strip()
        if p:
            p = os.path.normpath(p)
        logger.info(f"[Config] file_pt okundu: {p}")
        return p if p else None
    except Exception as e:
        logger.error(f"[Config] file_pt okunamadı: {e}")
        return None

def explorerda_ac(klasor_yolu):
    try:
        if not klasor_yolu:
            return False
        p = os.path.normpath(klasor_yolu)
        if not os.path.isdir(p):
            logger.info(f"[Explorer] Dizin yok: {p}")
            return False
        subprocess.Popen(["explorer", p])
        logger.info(f"[Explorer] Açıldı: {p}")
        return True
    except Exception as e:
        logger.error(f"[Explorer] Açılamadı: {e}")
        return False

def MurCr_is_desktop_context():
    """Masaüstü (Explorer'ın Desktop yüzü) mü?"""
    try:
        obj = api.getForegroundObject()
        app_name = str(getattr(getattr(obj, "appModule", None), "appName", "")).lower()
        window_class = str(getattr(obj, "windowClassName", "")).lower()
        name = str(getattr(obj, "name", "")).lower()
        logger.info(f"[Ctx/Desktop] app={app_name}, class={window_class}, name={name}")
        if app_name == "explorer" and ("desktop" in name or "masaüstü" in name or window_class in ("progman", "folderview")):
            return True
        return False
    except Exception as e:
        logger.error(f"[Ctx/Desktop] f: MurCr_is_desktop_context. {e}")
        return False

def _MurCr_get_real_desktop():
    """Masaüstü taşınmış olsa bile gerçek yolunu döndür."""
    try:
        with reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as key:
            val, _ = reg.QueryValueEx(key, "Desktop")
            path = os.path.expandvars(val)
            if os.path.isdir(path):
                return path
    except Exception as e:
        logger.error(f"[Desktop] _MurCr_get_real_desktop Reg okunamadı: {e}")

    home = os.path.expanduser("~")
    cand = os.path.join(home, "Desktop")
    if os.path.isdir(cand):
        logger.info(f"[Desktop] Fallback: {cand}")
        return cand
    od = os.path.join(home, "OneDrive", "Desktop")
    if os.path.isdir(od):
        logger.info(f"[Desktop] OneDrive Fallback: {od}")
        return od

    logger.info("[Desktop] f: _MurCr_get_real_desktop Masaüstü bulunamadı")
    return None

def _MurCr_try_append_allowed_exts(base_without_ext):
    """Uzantı gizlenmişse izinli uzantıları deneyip var olanı döndür."""
    for ext in ALLOWED_EXTS:
        cand = base_without_ext + ext
        if os.path.isfile(cand):
            logger.info(f"[Desktop] Uzantı tahmini tuttu: {cand}")
            return cand
    return None

def _MurCr_resolve_shortcut_if_needed(path):
    """'.lnk' ise gerçek hedefi döndür; değilse olduğu gibi ver."""
    try:
        if path and path.lower().endswith(".lnk"):
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            target = shell.CreateShortcut(path).Targetpath
            if target and os.path.exists(target):
                logger.info(f"[Desktop] Kısayol hedefi: {target}")
                return target
    except Exception as e:
        logger.error(f"[Desktop] f: _MurCr_resolve_shortcut_if_needed Kısayol çözülemedi: {e}")
    return path

def _MurCr_get_selected_file_desktop():
    """Masaüstünde seçili dosyanın/dizinin yolunu tahmin eder. NVDA navigator object adını kullanır."""
    try:
        obj = api.getNavigatorObject()
        name = (getattr(obj, "name", None) or "").strip()
        desktop = _MurCr_get_real_desktop()
        logger.info(f"[Desktop] navigator.name='{name}', desktop='{desktop}'")
        if not name or not desktop:
            return None

        cand = os.path.join(desktop, name)
        if os.path.isfile(cand):
            return _MurCr_resolve_shortcut_if_needed(cand)
        if os.path.isdir(cand):
            return os.path.normpath(cand)

        no_ext = os.path.join(desktop, os.path.splitext(name)[0])
        guessed = _MurCr_try_append_allowed_exts(no_ext)
        if guessed:
            return _MurCr_resolve_shortcut_if_needed(guessed)

        if os.path.isdir(no_ext):
            return os.path.normpath(no_ext)

        logger.info("[Desktop] f: _MurCr_get_selected_file_desktop Seçili öğe bulunamadı.")
        return None
    except Exception as e:
        logger.error(f"[Desktop] f:_MurCr_get_selected_file_desktop {e}")
        return None

def MurCr_is_explorer_context():
    """Dosya Gezgini (klasör penceresi) mi? (Masaüstü hariç)"""
    try:
        if MurCr_is_desktop_context():
            return False

        obj = api.getForegroundObject()
        app_name = str(getattr(getattr(obj, "appModule", None), "appName", "")).lower()
        window_class = str(getattr(obj, "windowClassName", "")).lower()
        name = str(getattr(obj, "name", "")).lower()
        logger.info(f"[Ctx/Explorer] app={app_name}, class={window_class}, name={name}")

        if app_name == "explorer":
            return True
        if window_class in ("cabinetwclass", "explorer"):
            return True
        if "dosya gezgini" in name or "file explorer" in name:
            return True

        return False
    except Exception as e:
        logger.error(f"[Ctx/Explorer] f: MurCr_is_explorer_context {e}")
        return False

def MurCr_get_selected_file_explorer():
    """Sadece ön plandaki Explorer penceresinden seçili öğenin tam yolunu alır.
    Seçim yoksa klasör yolunu döndürür; bulunamazsa None.
    """
    try:
        import comtypes.client
        try:
            from winUser import getForegroundWindow
            fg_hwnd = int(getForegroundWindow())
        except Exception:
            import ctypes
            fg_hwnd = int(ctypes.windll.user32.GetForegroundWindow())
        logger.info(f"[Explorer] FG HWND: {fg_hwnd}")

        shell = comtypes.client.CreateObject("Shell.Application")
        for w in shell.Windows():
            try:
                w_hwnd = int(getattr(w, "HWND", 0))
                w_name = str(getattr(w, "Name", ""))
                logger.info(f"[Explorer] window: hwnd={w_hwnd} name={w_name!r}")
                if w_hwnd != fg_hwnd:
                    continue
                doc = getattr(w, "Document", None)
                if not doc:
                    logger.info("[Explorer] FG: Document yok")
                    break
                try:
                    sel = doc.SelectedItems()
                    if sel and getattr(sel, "Count", 0) > 0:
                        p = sel.Item(0).Path
                        logger.info(f"[Explorer] Seçili (FG): {p}")
                        return p
                except Exception as e_sel:
                    logger.error(f"[Explorer] FG: SelectedItems hatası: {e_sel}")
                try:
                    folderPath = doc.Folder.Self.Path
                    logger.info(f"[Explorer] Seçim yok, klasör yolu (FG): {folderPath}")
                    return folderPath
                except Exception as e_fold:
                    logger.error(f"[Explorer] FG: Folder.Path hatası: {e_fold}")
                break
            except Exception as e_loop:
                logger.error(f"[Explorer] FG döngü hatası: {e_loop}")

        logger.info("[Explorer] Başarısız: Seçili öğe bulunamadı (FG).")
        return None

    except Exception as e:
        logger.error(f"[Explorer] COM API hatası. f:MurCr_get_selected_file_explorer {e}")
        try:
            ps_cmd = r'''powershell -command "& { $sel = (New-Object -ComObject Shell.Application).Windows() | Where-Object { $_.Document.SelectedItems().Count -gt 0 } | ForEach-Object { $_.Document.SelectedItems().Item(0).Path }; Write-Output $sel }"'''
            result = subprocess.check_output(ps_cmd, shell=True, universal_newlines=True).strip()
            logger.info(f"[Explorer] PowerShell sonucu: {result}")
            return result if result else None
        except Exception as e2:
            logger.error(f"[Explorer] PowerShell hatası. f: MurCr_get_selected_file_explorer {e2}")
            return None

def MurCr_which_app():
    """Ön plandaki uygulamayı ayıklar."""
    try:
        if MurCr_is_desktop_context():
            logger.info("[Ctx] Tespit: Masaüstü")
            return APP_DESKTOP
        if MurCr_is_explorer_context():
            logger.info("[Ctx] Tespit: Gezgini")
            return APP_EXPLORER
        logger.info("[Ctx] Tespit: Unknown")
        return APP_UNKNOWN
    except Exception as e:
        logger.error(f"[Ctx] f: MurCr_which_app {e}")
        return APP_UNKNOWN

def MurCr_get_selected_file_smart():
    """Masaüstü/Explorer bağlamına göre seçili öğeyi döndürür."""
    try:
        if MurCr_is_desktop_context():
            logger.info("[Smart] Bağlam: Masaüstü")
            return _MurCr_get_selected_file_desktop()
        if MurCr_is_explorer_context():
            logger.info("[Smart] Bağlam: Gezgini")
            return MurCr_get_selected_file_explorer()
        logger.info("[Smart] Bağlam desteklenmiyor")
        return None
    except Exception as e:
        logger.error(f"[Smart] f: MurCr_get_selected_file_smart {e}")
        return None

def file_control(path_value):
    """Seçilen öğenin MurCr tarafından işlenebilir olup olmadığını kontrol eder (dosya veya dizin)."""
    if not path_value:
        return {"ok": False, "path": None, "kind": None, "ext": None, "reason": "missing"}

    p = os.path.abspath(path_value)

    if not os.path.exists(p):
        _, ext = os.path.splitext(p.lower())
        return {"ok": False, "path": p, "kind": None, "ext": ext or None, "reason": "not_exists"}

    if os.path.isdir(p):
        return {"ok": True, "path": p, "kind": "dir", "ext": None, "reason": None}

    _, ext = os.path.splitext(p.lower())
    if ext not in ALLOWED_EXTS:
        return {"ok": False, "path": p, "kind": "file", "ext": ext or None, "reason": "unsupported"}

    return {"ok": True, "path": p, "kind": "file", "ext": ext, "reason": None}

def Unputable_File(source, file_path, ext):
    """Desteklenmeyen dosya senaryosunu ele alır (Desktop/Explorer)."""
    try:
        ui.message(tr("The selected item is not supported by MurCr."))
        logger.info(f"Unputable_File: Desteklenmeyen uzantı | ext={ext} | path={file_path} | source={source}")
        return {"handled": True, "source": source, "file_path": file_path, "ext": ext}
    except Exception as e:
        logger.error(f"Unputable_File: İstisna: {e}")
        return {"handled": False, "source": source, "file_path": file_path, "ext": ext}

def get_murcr_exe_path():
    """Sadece HKCU\\App Paths\\MurCr.exe altındaki Default değeri varsa onu döndürür; yoksa varsayılan yolu döndürür."""
    subkey = r"Software\Microsoft\Windows\CurrentVersion\App Paths\MurCr.exe"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey, 0, winreg.KEY_READ) as k:
            try:
                val = winreg.QueryValue(k, None)
            except OSError:
                val = None
            if val and isinstance(val, str):
                return os.path.normpath(val.strip('"'))
    except OSError:
        pass
    return os.path.normpath(MurCr_path)

def MurCr_open(path_value=None, source=None):
    try:
        logger.info(f"MurCr_open tetiklendi | source: {source}")

        if path_value is None:
            logger.info(f"Öğe yolu belirtilmedi. Kaynak: {source}")
            path_value = MurCr_get_selected_file_smart()

        logger.info(f"Alınan yol (ham): {path_value}")
        fc = file_control(path_value)

        if not fc["ok"]:
            reason = fc.get("reason")
            full_path = fc.get("path")
            ext = fc.get("ext")

            if reason in ("missing", "not_exists"):
                ui.message(tr("Invalid procedure or file path."))
                logger.info(f"Başarısız: Yol alınamadı veya mevcut değil. path={full_path}")
                return

            if reason == "unsupported":
                Unputable_File(source=source, file_path=full_path, ext=ext)
                return

            ui.message(tr("An error occurred."))
            logger.info(f"Başarısız: Bilinmeyen kontrol sonucu: reason={reason} | path={full_path} | ext={ext}")
            return

        real_path = fc["path"]
        if fc["kind"] == "dir":
            logger.info(f"Dizin seçildi: {real_path}")
            ui.message(tr("Opening with MurCr."))
            subprocess.Popen([get_murcr_exe_path(), real_path])
            logger.info(f"MurCr çalıştırıldı (dizin): {real_path} -> {get_murcr_exe_path()}")
            return

        file_name = os.path.basename(real_path)
        logger.info(f"Dosya adı: {file_name} | Uzantı: {fc['ext']}")
        ui.message(tr("Opening with MurCr."))
        subprocess.Popen([get_murcr_exe_path(), real_path])
        logger.info(f"MurCr çalıştırıldı (dosya): {real_path} -> {get_murcr_exe_path()}")

    except Exception as e:
        ui.message(tr("An error occurred."))
        logger.error(f"MurCr_open istisnası: {e}")

def MurCr_probe_installation_on_load():
    """Eklenti yüklenirken veya ilk tetikte çağrılır."""
    global MurCr_INSTALLED
    try:
        exists = os.path.isfile(MurCr_path)
        MurCr_INSTALLED = bool(exists)
        logger.info(f"[Probe] MurCr var mı? {MurCr_INSTALLED} {MurCr_path}")
        if not MurCr_INSTALLED:
            logger.info("MurCr kurulu değil")
            MurCr_prompt_to_install_if_missing()
        return MurCr_INSTALLED
    except Exception as e:
        MurCr_INSTALLED = False
        logger.error("MurCr kurulu değil")
        logger.error(f"[Probe] f:MurCr_probe_installation_on_load {e}")
        MurCr_prompt_to_install_if_missing()
        return False

def MurCr_prompt_to_install_if_missing():
    """MurCr_INSTALLED True değilse çağrılır."""
    def _show():
        try:
            t = wx.Timer()
            def _onTimer(evt):
                try:
                    ui.message(tr("You cannot proceed without MurCr. Would you like to open the download page?"))
                finally:
                    t.Stop()
            t.Bind(wx.EVT_TIMER, _onTimer)
            t.Start(100)

            dlg = wx.MessageDialog(
                None,
                tr("You cannot proceed without MurCr. Would you like to open the download page?"),
                tr("MurCr not found"),
                style=wx.YES_NO | wx.ICON_WARNING
            )
            res = dlg.ShowModal()
            dlg.Destroy()

            logger.info(f"[Prompt] Sonuç id: {res}")

            if res == wx.ID_YES:
                try:
                    webbrowser.open("https://Koruz.biz", new=1)
                except Exception as e:
                    logger.error(f"[Prompt] URL açılamadı: {e}")
            elif res == wx.ID_NO:
                logger.info("[Prompt] HAYIR: Kullanıcı reddetti.")
            else:
                logger.info("[Prompt] Kapatıldı / iptal edildi.")
        except Exception as e:
            logger.error(f"[Prompt] pop up : {e}")

    wx.CallAfter(_show)

class GlobalPlugin(_BaseGlobalPlugin):
    def __init__(self):
        super().__init__()
        logger.info("Yüklendi")

        self._murcr_k_tmr = None
        self._murcr_k_beklemede = False

        try:
            if MurCr_probe_installation_on_load():
                eklenti_ayarlarini_config_ile_senkronla()
        except Exception:
            pass

    scriptCategory = tr("MurCr")

    __gestures = {
        "kb:NVDA+alt+k": "MurCr_master",
    }

    @script(description="MurCr kısayol tuşu")
    def script_MurCr_master(self, gesture):
        logger.info("#! Tetiklendi !#")
    
        try:
            tekrar = int(scriptHandler.getLastScriptRepeatCount())
        except Exception as e:
            tekrar = 0
            logger.error(f"[Repeat] Tekrar sayısı okunamadı: {e}")
    
        if not MurCr_INSTALLED:
            if not MurCr_probe_installation_on_load():
                return
    
        if tekrar >= 1:
            try:
                if getattr(self, "_murcr_k_tmr", None) is not None:
                    try:
                        self._murcr_k_tmr.Stop()
                    except Exception:
                        pass
                self._murcr_k_tmr = None
                self._murcr_k_beklemede = False
            except Exception:
                pass
    
            self._murcr_proje_dizinini_ac()
            return
    
        try:
            if getattr(self, "_murcr_k_beklemede", False):
                logger.info("[K] Tek basış zaten beklemede, atlandı")
                return
            self._murcr_k_beklemede = True
    
            def _calistir():
                self._murcr_k_beklemede = False
                self._murcr_k_tmr = None
                self._murcr_tek_basisi_isle()
    
            self._murcr_k_tmr = wx.CallLater(400, _calistir)
            logger.info("[K] Tek basış beklemeye alındı (çift basış kontrolü)")
        except Exception as e:
            self._murcr_k_beklemede = False
            self._murcr_k_tmr = None
            logger.error(f"[K] Bekletme kurulamadı: {e}")
            self._murcr_tek_basisi_isle()
    
    # Sınıf fonksiyonları
    def _murcr_proje_dizinini_ac(self):
        logger.info("#! Proje dizini aç tetiklendi !#")
    
        if not MurCr_INSTALLED:
            if not MurCr_probe_installation_on_load():
                return
    
        try:
            eklenti_ayarlarini_config_ile_senkronla()
            p = murcr_configten_file_pt_oku()
            if not p:
                ui.message(tr("Project folder path could not be found."))
                logger.info("[Proje] file_pt yok")
                return
            if not explorerda_ac(p):
                ui.message(tr("The project folder could not be opened."))
                logger.info("[Proje] Explorer açılamadı")
                return
            ui.message(tr("Project folder opened."))
        except Exception as e:
            ui.message(tr("An error occurred."))
            logger.error(f"[Proje] HATA: {e}")
    
    def _murcr_tek_basisi_isle(self):
        try:
            ctx = MurCr_which_app()
            logger.info(f"[Master] Bağlam: {ctx}")
    
            if ctx == APP_DESKTOP:
                MurCr_open(source=APP_DESKTOP)
                return
    
            if ctx == APP_EXPLORER:
                MurCr_open(source=APP_EXPLORER)
                return
    
            ui.message(tr("The MurCr add-on is not configured for this application."))
            logger.info("[Master] Başarısız: Bağlam desteklenmiyor")
        except Exception as e:
            ui.message(tr("An error occurred while identifying the application."))
            logger.error(f"[Master] HATA: {e}")
    
    