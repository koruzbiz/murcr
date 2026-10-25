import os
import wx
from config import conf

try:
    from gui.settingsDialogs import SettingsPanel, registerSettingsPanel, NVDASettingsDialog
except Exception:
    from gui import settingsDialogs
    SettingsPanel = settingsDialogs.SettingsPanel
    registerSettingsPanel = None
    NVDASettingsDialog = settingsDialogs.NVDASettingsDialog

try:
    from . import tr as _pkg_tr
    def tr(msg): return _pkg_tr(msg)
except Exception:
    def tr(msg): return msg

SECTION = "KoruzBiz_MurCr"
KEY_OUTPUT_DIR = "outputDir"

def _get_documents_dir() -> str:
    try:
        import ctypes, ctypes.wintypes as wt
        CSIDL_PERSONAL = 5
        SHGFP_TYPE_CURRENT = 0
        buf = ctypes.create_unicode_buffer(wt.MAX_PATH)
        if ctypes.windll.shell32.SHGetFolderPathW(0, CSIDL_PERSONAL, 0, SHGFP_TYPE_CURRENT, buf) == 0 and buf.value:
            return buf.value
    except Exception:
        pass
    return os.path.join(os.path.expanduser("~"), "Documents")

def _murcr_default_project_dir() -> str:
    return os.path.join(_get_documents_dir(), "MurCr")

def _log(kind, msg):
    try:
        from .KoruzBiz_MurCr import logger
        getattr(logger, kind)(msg)
    except Exception:
        pass

def _murcr_config_file_pt() -> str:
    """MurCr'nin sabit config dosyasindaki proje dizini (file_pt).
    Yol her zaman %APPDATA%\\Koruz_Biz\\murcr\\config.txt (kurulum dizininden bagimsiz)."""
    import json
    adaylar = []
    for kok in (os.getenv("APPDATA"), os.path.join(os.path.expanduser("~"), "AppData", "Roaming")):
        if kok:
            p = os.path.join(kok, "Koruz_Biz", "murcr", "config.txt")
            if p not in adaylar:
                adaylar.append(p)
    for cfg in adaylar:
        try:
            if not os.path.isfile(cfg):
                _log("info", f"[Ayarlar] config yok: {cfg}")
                continue
            with open(cfg, "r", encoding="utf-8-sig", errors="replace") as f:
                data = json.load(f)
            p = (data.get("file_pt") or "").strip()
            _log("info", f"[Ayarlar] {cfg} -> file_pt={p!r}")
            if p:
                return os.path.normpath(p)
        except Exception as e:
            _log("error", f"[Ayarlar] config okunamadi ({cfg}): {e}")
    return ""

def _ensure_defaults():
    if SECTION not in conf:
        conf[SECTION] = {}
    # Dizin adi bossa (ilk kurulum): once MurCr'nin config'indeki proje dizini, yoksa Belgelerim\\MurCr
    if not (conf[SECTION].get(KEY_OUTPUT_DIR) or "").strip():
        murcr_pt = _murcr_config_file_pt()
        conf[SECTION][KEY_OUTPUT_DIR] = murcr_pt if murcr_pt else _murcr_default_project_dir()
        _log("info", f"[Ayarlar] bos dizin dolduruldu: {conf[SECTION][KEY_OUTPUT_DIR]}")
        conf.save()

class MurCrSettingsPanel(SettingsPanel):
    title = tr("Koruz.biz MurCr")

    def makeSettings(self, sizer):
        _ensure_defaults()

        grid = wx.FlexGridSizer(rows=1, cols=2, vgap=6, hgap=6)
        grid.AddGrowableCol(1, 1)

        labelText = tr("MurCr Project Directory")
        label = wx.StaticText(self, label=labelText + ":")
        grid.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)

        startPath = conf[SECTION].get(KEY_OUTPUT_DIR, _murcr_default_project_dir())
        self.dirPicker = wx.DirPickerCtrl(
            self,
            path=startPath,
            message=tr("Select the project directory folder"),
            style=wx.DIRP_DIR_MUST_EXIST | wx.DIRP_USE_TEXTCTRL
        )
        grid.Add(self.dirPicker, flag=wx.EXPAND)

        try:
            import ui
            btn = self.dirPicker.GetPickerCtrl() if hasattr(self.dirPicker, "GetPickerCtrl") else None
            if btn:
                try:
                    btn.SetName(tr("Browse"))
                except Exception:
                    pass
                def _announce_after_browse_focus(evt):
                    wx.CallLater(80, lambda: ui.message(labelText))
                    evt.Skip()
                btn.Bind(wx.EVT_SET_FOCUS, _announce_after_browse_focus)
        except Exception:
            pass

        sizer.Add(grid, flag=wx.ALL | wx.EXPAND, border=12)

    def onSave(self):
        try:
            if hasattr(self, "dirPicker"):
                path = self.dirPicker.GetPath()
                if path and os.path.isdir(path):
                    conf[SECTION][KEY_OUTPUT_DIR] = path
                    conf.save()
        except Exception:
            pass

    def save(self):
        return self.onSave()

_MurCr_SETTINGS_REGISTERED = False
def _register_settings_panel_once():
    global _MurCr_SETTINGS_REGISTERED
    if _MurCr_SETTINGS_REGISTERED:
        return
    try:
        if registerSettingsPanel:
            registerSettingsPanel(MurCrSettingsPanel)
        else:
            if MurCrSettingsPanel not in NVDASettingsDialog.categoryClasses:
                NVDASettingsDialog.categoryClasses.append(MurCrSettingsPanel)
    except Exception:
        pass
    else:
        _MurCr_SETTINGS_REGISTERED = True

_register_settings_panel_once()
