# -*- coding: utf-8 -*-
"""
REVLO Dash - application Windows basee sur PySide6 + QtWebEngine.

Points cles :
  * profil WebEngine persistant dans %LOCALAPPDATA%\\REVLO Dash (cookies, sessions, cache)
  * AUCUN blocage de pop-ups : chaque window.open() / target="_blank" / redirection
    ouvre une fenetre independante qui partage le meme profil (createWindow)
  * barres de defilement masquees (attribut natif + CSS), le defilement reste actif
  * interface minimaliste : pas de barre d'adresse, pas de boutons de navigation

Lancement de test des pop-ups :  python main.py --test
"""
import ctypes
import gc
import html
import os
import sys
import traceback

APP_NAME = "REVLO Dash"
APP_ORG = "REVLO"
APP_URL = "https://dash-revlo.ct.ws/"
APP_USER_MODEL_ID = "REVLO.Dash.App"
SINGLE_INSTANCE_KEY = "REVLO-Dash-single-instance-v1"
WINDOW_SIZE = (1200, 800)
BG_COLOR = "#0f172a"

# Schemas ouverts par l'application externe (ex. Telegram Desktop pour tg://)
EXTERNAL_SCHEMES = ("tg", "mailto", "tel", "sms", "whatsapp", "skype")


# --------------------------------------------------------------------------- #
#  Chemins, journal
# --------------------------------------------------------------------------- #
def resource_path(relative):
    """Chemin d'une ressource (dev ou executable PyInstaller)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


def get_data_dir():
    """Dossier de donnees persistant (AppData\\Local\\REVLO Dash), jamais le dossier temporaire PyInstaller."""
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    path = os.path.join(base, APP_NAME)
    for sub in ("", "profile", "cache", "logs"):
        os.makedirs(os.path.join(path, sub), exist_ok=True)
    return path


def setup_logging(log_dir):
    """En mode --windowed, sys.stdout/sys.stderr valent None : on les redirige vers un fichier journal."""
    path = os.path.join(log_dir, "revlo-dash.log")
    try:
        if os.path.exists(path) and os.path.getsize(path) > 1_000_000:
            os.remove(path)
        stream = open(path, "a", encoding="utf-8", buffering=1)
    except OSError:
        stream = open(os.devnull, "w")
    if sys.stdout is None:
        sys.stdout = stream
    if sys.stderr is None:
        sys.stderr = stream

    def excepthook(exc_type, exc, tb):
        traceback.print_exception(exc_type, exc, tb, file=stream)
        if sys.__stderr__ is not None:
            traceback.print_exception(exc_type, exc, tb, file=sys.__stderr__)

    sys.excepthook = excepthook


# --------------------------------------------------------------------------- #
#  Imports Qt (apres la configuration du journal)
# --------------------------------------------------------------------------- #
from PySide6.QtCore import QCoreApplication, QEvent, Qt, QTimer, QUrl  # noqa: E402
from PySide6.QtGui import QColor, QDesktopServices, QIcon, QKeySequence, QShortcut  # noqa: E402
from PySide6.QtNetwork import QLocalServer, QLocalSocket  # noqa: E402
from PySide6.QtWebEngineCore import (  # noqa: E402
    QWebEngineLoadingInfo,
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineScript,
    QWebEngineSettings,
)
from PySide6.QtWebEngineWidgets import QWebEngineView  # noqa: E402
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMenu  # noqa: E402

try:  # PySide6 >= 6.8
    from PySide6.QtWebEngineCore import QWebEnginePermission
except ImportError:  # pragma: no cover
    QWebEnginePermission = None


# --------------------------------------------------------------------------- #
#  CSS : masquer les barres de defilement sans desactiver le defilement
# --------------------------------------------------------------------------- #
HIDE_SCROLLBARS_JS = r"""
(function () {
  var css =
    'html, body, * { scrollbar-width: none !important; -ms-overflow-style: none !important; }' +
    '*::-webkit-scrollbar, ::-webkit-scrollbar { width: 0 !important; height: 0 !important;' +
    ' display: none !important; background: transparent !important; }';
  try {
    // Feuille de style "constructable" : non soumise a la CSP du site et disponible des la creation du document.
    var sheet = new CSSStyleSheet();
    sheet.replaceSync(css);
    document.adoptedStyleSheets = document.adoptedStyleSheets.concat([sheet]);
    return;
  } catch (e) { /* repli ci-dessous */ }
  function inject() {
    var style = document.createElement('style');
    style.textContent = css;
    (document.head || document.documentElement).appendChild(style);
  }
  if (document.head || document.documentElement) { inject(); }
  else { document.addEventListener('DOMContentLoaded', inject); }
})();
"""

ERROR_HTML = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><title>REVLO Dash</title>
<style>
  html,body{height:100%;margin:0;background:#0f172a;color:#e2e8f0;
            font-family:"Segoe UI",system-ui,sans-serif;overflow:hidden}
  .box{height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;
       text-align:center;padding:24px;box-sizing:border-box}
  h1{font-size:22px;font-weight:600;margin:0 0 10px}
  p{margin:4px 0;color:#94a3b8;font-size:14px}
  small{display:block;margin-top:14px;color:#64748b;font-size:12px}
  button{margin-top:22px;padding:10px 28px;border:0;border-radius:8px;background:#2563eb;
         color:#fff;font-size:14px;cursor:pointer}
  button:hover{background:#1d4ed8}
</style></head>
<body><div class="box">
  <h1>Impossible de charger REVLO Dash</h1>
  <p>V&eacute;rifiez votre connexion Internet, puis r&eacute;essayez.</p>
  <button onclick="location.href='{{URL}}'">R&eacute;essayer</button>
  <small>{{DETAIL}} &nbsp;&middot;&nbsp; F5 pour recharger</small>
</div></body></html>
"""

TEST_HTML = r"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><title>REVLO Dash - Test des pop-ups</title>
<style>
  body{font-family:"Segoe UI",sans-serif;background:#0f172a;color:#e2e8f0;margin:0;padding:28px}
  button,a.b{display:inline-block;margin:6px 8px 6px 0;padding:9px 16px;border:0;border-radius:6px;
             background:#2563eb;color:#fff;text-decoration:none;font-size:14px;cursor:pointer}
  pre{background:#020617;padding:14px;border-radius:8px;min-height:110px;color:#86efac}
  .long{height:2600px;margin-top:24px;border:1px dashed #475569;padding:12px;color:#94a3b8}
</style></head><body>
<h2>REVLO Dash &mdash; page de test</h2>
<p>Chaque test doit ouvrir une fen&ecirc;tre ind&eacute;pendante. Rien ne doit &ecirc;tre bloqu&eacute;.</p>
<button onclick="t1()">1. window.open (clic)</button>
<a class="b" href="https://example.org/" target="_blank">2. Lien target="_blank"</a>
<button onclick="t3()">3. window.open sans clic (apr&egrave;s 2 s)</button>
<button onclick="t4()">4. Pop-up local + window.opener</button>
<a class="b" href="https://t.me/telegram" target="_blank">5. Lien t.me (Telegram web)</a>
<a class="b" href="tg://resolve?domain=telegram">6. Lien tg:// (Telegram Desktop)</a>
<pre id="log">R&eacute;sultats :
</pre>
<div class="long">Zone longue : v&eacute;rifiez que le d&eacute;filement (molette) fonctionne et
qu'AUCUNE barre de d&eacute;filement n'est visible, ni verticale ni horizontale.</div>
<script>
function log(m){ document.getElementById('log').textContent += m + '\n'; }
window.addEventListener('message', function(e){ log('OK  message re\u00e7u du pop-up (window.opener fonctionne) : ' + e.data); });
function t1(){ var w = window.open('https://example.org/', '_blank'); log(w ? 'OK  window.open' : 'ECHEC window.open (null)'); }
function t3(){
  log('Pop-up dans 2 s, sans nouveau clic...');
  setTimeout(function(){
    var w = window.open('https://example.org/', '_blank');
    log(w ? 'OK  pop-up declenche par JavaScript sans geste utilisateur' : 'ECHEC pop-up bloque');
  }, 2000);
}
function t4(){
  var w = window.open('', '_blank', 'width=480,height=360');
  if(!w){ log('ECHEC pop-up local bloque'); return; }
  w.document.write('<title>Pop-up local</title><body style="font-family:sans-serif;background:#111827;color:#fff;padding:24px">' +
    '<h3>Pop-up local</h3>' +
    '<button onclick="window.opener.postMessage(\'opener-ok\',\'*\')">Envoyer un message a la fenetre principale</button> ' +
    '<button onclick="window.close()">Fermer (window.close)</button></body>');
  w.document.close();
  log('OK  pop-up local ouvert');
}
</script></body></html>
"""

# Les fenetres secondaires doivent rester referencees cote Python (sinon : destruction par le garbage collector).
_POPUPS = set()


def load_app_icon():
    for rel in (os.path.join("assets", "revlo-logo.ico"), "revlo-logo.svg"):
        path = resource_path(rel)
        if os.path.exists(path):
            icon = QIcon(path)
            if not icon.isNull():
                return icon
    return QIcon()


# --------------------------------------------------------------------------- #
#  Vue / Page
# --------------------------------------------------------------------------- #
class RevloView(QWebEngineView):
    """Vue sans les entrees de menu contextuel de type 'navigateur'."""

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        try:
            page = self.page()
            W = QWebEnginePage.WebAction
            hidden = []
            for name in ("Back", "Forward", "ViewSource", "SavePage", "InspectElement"):
                action = getattr(W, name, None)
                if action is not None:
                    hidden.append(page.action(action))
            for act in list(menu.actions()):
                if act in hidden:
                    menu.removeAction(act)
        except Exception:
            pass
        if not menu.actions():
            menu.deleteLater()
            return
        menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        menu.popup(event.globalPos())


class RevloPage(QWebEnginePage):
    """Page commune a la fenetre principale et aux pop-ups. Aucune logique de blocage."""

    def __init__(self, profile, parent):
        super().__init__(profile, parent)
        self.setBackgroundColor(QColor(BG_COLOR))
        self.fullScreenRequested.connect(self._on_fullscreen)
        if hasattr(self, "permissionRequested"):          # Qt >= 6.8
            self.permissionRequested.connect(self._on_permission)
        else:                                             # Qt < 6.8
            self.featurePermissionRequested.connect(self._on_feature_permission)

    # -- Fenetres secondaires : window.open(), target="_blank", etc. -------------
    def createWindow(self, window_type):
        popup = PopupWindow(self.profile())      # meme profil => cookies et sessions partages
        popup.show()
        popup.raise_()
        popup.activateWindow()
        return popup.page_                        # la page retournee charge elle-meme l'URL (window.opener conserve)

    # -- Schemas externes (tg://...) ---------------------------------------------
    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        if url.scheme().lower() in EXTERNAL_SCHEMES:
            QDesktopServices.openUrl(url)
            win = self.view().window() if self.view() is not None else None
            if isinstance(win, PopupWindow) and (self.url().isEmpty() or self.url().toString() == "about:blank"):
                QTimer.singleShot(0, win.close)   # pop-up vide dont le seul but etait d'ouvrir l'application externe
            return False
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)

    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        pass  # pas de console visible

    # -- Plein ecran HTML --------------------------------------------------------
    def _on_fullscreen(self, request):
        request.accept()
        win = self.view().window() if self.view() is not None else None
        if isinstance(win, BaseWindow):
            win.set_fullscreen(request.toggleOn())

    # -- Permissions : presse-papiers autorise, le reste refuse (securite) -------
    def _on_permission(self, permission):
        try:
            allowed = getattr(QWebEnginePermission.PermissionType, "ClipboardReadWrite", None)
            if allowed is not None and permission.permissionType() == allowed:
                permission.grant()
            else:
                permission.deny()
        except Exception:
            pass

    def _on_feature_permission(self, origin, feature):
        policy = QWebEnginePage.PermissionPolicy
        allowed = getattr(QWebEnginePage.Feature, "ClipboardReadWrite", None)
        ok = allowed is not None and feature == allowed
        self.setFeaturePermission(
            origin, feature, policy.PermissionGrantedByUser if ok else policy.PermissionDeniedByUser
        )


# --------------------------------------------------------------------------- #
#  Fenetres
# --------------------------------------------------------------------------- #
class BaseWindow(QMainWindow):
    def __init__(self, title):
        super().__init__(None)
        self.setWindowTitle(title)
        self.setWindowIcon(QApplication.windowIcon())
        self.setStyleSheet("QMainWindow { background-color: %s; }" % BG_COLOR)
        self._was_maximized = False
        QShortcut(QKeySequence("F11"), self, activated=self.toggle_fullscreen)

    def set_fullscreen(self, on):
        if on and not self.isFullScreen():
            self._was_maximized = self.isMaximized()
            self.showFullScreen()
        elif not on and self.isFullScreen():
            if self._was_maximized:
                self.showMaximized()
            else:
                self.showNormal()

    def toggle_fullscreen(self):
        self.set_fullscreen(not self.isFullScreen())


class PopupWindow(BaseWindow):
    """Fenetre independante pour chaque pop-up (Telegram, OAuth, target="_blank"...)."""

    def __init__(self, profile):
        super().__init__(APP_NAME)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.resize(900, 700)

        self.view = RevloView(self)
        self.page_ = RevloPage(profile, self.view)
        self.view.setPage(self.page_)
        self.setCentralWidget(self.view)

        self.page_.windowCloseRequested.connect(self.close)          # window.close() cote JavaScript
        self.page_.titleChanged.connect(self._update_title)
        self.page_.urlChanged.connect(lambda _url: self._update_title())
        self.page_.geometryChangeRequested.connect(self._on_geometry)  # window.open(..., 'width=..,height=..')

        QShortcut(QKeySequence("F5"), self, activated=self.view.reload)
        QShortcut(QKeySequence("Ctrl+W"), self, activated=self.close)

        self._place()
        _POPUPS.add(self)   # reference Python conservee jusqu'a la fermeture

    def _screen_geometry(self):
        screen = self.screen() or QApplication.primaryScreen()
        return screen.availableGeometry()

    def _place(self):
        geo = self._screen_geometry()
        offset = 28 * (len(_POPUPS) % 8)
        x = geo.x() + (geo.width() - self.width()) // 2 + offset
        y = geo.y() + (geo.height() - self.height()) // 2 + offset
        x = max(geo.x(), min(x, geo.right() - self.width()))
        y = max(geo.y(), min(y, geo.bottom() - self.height()))
        self.move(x, y)

    def _on_geometry(self, rect):
        if rect.width() <= 0 or rect.height() <= 0:
            return
        geo = self._screen_geometry()
        self.resize(max(320, min(rect.width(), geo.width())), max(200, min(rect.height(), geo.height())))
        self._place()

    def _update_title(self, *_):
        title = self.page_.title() or ""
        host = self.page_.url().host()
        if title and host:
            self.setWindowTitle("%s \u2014 %s" % (title, host))   # le domaine reste visible (securite des connexions)
        else:
            self.setWindowTitle(title or host or APP_NAME)

    def closeEvent(self, event):
        # Liberation differee de la reference Python (evite de detruire l'objet pendant son propre closeEvent).
        QTimer.singleShot(0, lambda w=self: _POPUPS.discard(w))
        super().closeEvent(event)


class MainWindow(BaseWindow):
    def __init__(self, profile, test_mode=False):
        super().__init__(APP_NAME)
        self.resize(*WINDOW_SIZE)
        self.setMinimumSize(480, 360)
        geo = QApplication.primaryScreen().availableGeometry()
        self.move(geo.x() + (geo.width() - self.width()) // 2, geo.y() + (geo.height() - self.height()) // 2)

        self.view = RevloView(self)
        self.page_ = RevloPage(profile, self.view)
        self.view.setPage(self.page_)
        self.setCentralWidget(self.view)

        self._error_shown = False
        self._skip_success = False

        self.page_.loadingChanged.connect(self._on_loading_changed)
        self.page_.renderProcessTerminated.connect(self._on_render_terminated)
        self.page_.windowCloseRequested.connect(self.close)

        for seq in ("F5", "Ctrl+R"):
            QShortcut(QKeySequence(seq), self, activated=self.reload_site)

        if test_mode:
            self.page_.setHtml(TEST_HTML, QUrl("https://revlo.test/"))
        else:
            self.page_.load(QUrl(APP_URL))

    # -- Chargement / erreurs ---------------------------------------------------
    def reload_site(self):
        if self._error_shown:
            self._error_shown = False
            self.page_.load(QUrl(APP_URL))
        else:
            self.view.reload()

    def _on_loading_changed(self, info):
        status = info.status()
        S = QWebEngineLoadingInfo.LoadStatus
        if status == S.LoadFailedStatus:
            if info.errorCode() == -3:      # ERR_ABORTED : navigation annulee / remplacee, pas une vraie erreur
                return
            detail = info.errorString() or "Erreur de chargement"
            QTimer.singleShot(0, lambda d=detail: self._show_error(d))
        elif status == S.LoadSucceededStatus:
            if self._skip_success:          # fin de chargement de notre propre page d'erreur
                self._skip_success = False
            else:
                self._error_shown = False

    def _show_error(self, detail):
        self._error_shown = True
        self._skip_success = True
        page = ERROR_HTML.replace("{{URL}}", APP_URL).replace("{{DETAIL}}", html.escape(detail))
        self.page_.setHtml(page, QUrl(APP_URL))

    def _on_render_terminated(self, status, exit_code):
        normal = QWebEnginePage.RenderProcessTerminationStatus.NormalTerminationStatus
        if status != normal:                # plantage du moteur : on recharge pour eviter une fenetre blanche
            QTimer.singleShot(800, self.reload_site)

    def closeEvent(self, event):
        for popup in list(_POPUPS):
            popup.close()
        super().closeEvent(event)


# --------------------------------------------------------------------------- #
#  Profil WebEngine persistant
# --------------------------------------------------------------------------- #
def create_profile(app, data_dir):
    profile = QWebEngineProfile("REVLODash", app)
    profile.setPersistentStoragePath(os.path.join(data_dir, "profile"))
    profile.setCachePath(os.path.join(data_dir, "cache"))
    # Les cookies de session sont aussi conserves : la connexion survit a la fermeture de l'application.
    profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
    profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
    profile.setHttpCacheMaximumSize(0)  # 0 = gestion automatique

    A = QWebEngineSettings.WebAttribute
    wanted = {
        "JavascriptEnabled": True,
        "JavascriptCanOpenWindows": True,            # window.open() autorise (y compris sans geste utilisateur)
        "AllowWindowActivationFromJavaScript": True,
        "JavascriptCanAccessClipboard": True,
        "JavascriptCanPaste": True,
        "LocalStorageEnabled": True,
        "PlaybackRequiresUserGesture": False,
        "FullScreenSupportEnabled": True,
        "ScrollAnimatorEnabled": True,
        "PluginsEnabled": True,
        "PdfViewerEnabled": True,
        "AutoLoadImages": True,
        "WebGLEnabled": True,
        "Accelerated2dCanvasEnabled": True,
        "DnsPrefetchEnabled": True,
        "FocusOnNavigationEnabled": True,
        "ErrorPageEnabled": False,                   # page d'erreur Chromium remplacee par la notre
        "ShowScrollBars": False,                     # masque les barres natives, le defilement reste actif
        "AllowRunningInsecureContent": False,
    }
    settings = profile.settings()
    for name, value in wanted.items():
        attr = getattr(A, name, None)
        if attr is not None:
            settings.setAttribute(attr, value)

    script = QWebEngineScript()
    script.setName("revlo-hide-scrollbars")
    script.setSourceCode(HIDE_SCROLLBARS_JS)
    script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
    script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
    script.setRunsOnSubFrames(True)
    profile.scripts().insert(script)

    def on_download(download):
        default_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        suggested = os.path.join(default_dir, download.downloadFileName() or "telechargement")
        path, _ = QFileDialog.getSaveFileName(QApplication.activeWindow(), "Enregistrer le fichier", suggested)
        if not path:
            download.cancel()
            return
        download.setDownloadDirectory(os.path.dirname(path))
        download.setDownloadFileName(os.path.basename(path))
        download.accept()

    profile.downloadRequested.connect(on_download)
    return profile


# --------------------------------------------------------------------------- #
#  Instance unique (evite deux processus sur le meme profil)
# --------------------------------------------------------------------------- #
class SingleInstance:
    def __init__(self, key):
        self.key = key
        self.server = None
        self.callback = None

    def already_running(self):
        sock = QLocalSocket()
        sock.connectToServer(self.key)
        if sock.waitForConnected(300):
            sock.write(b"activate")
            sock.flush()
            sock.waitForBytesWritten(300)
            sock.disconnectFromServer()
            return True
        return False

    def listen(self, callback):
        self.callback = callback
        QLocalServer.removeServer(self.key)
        self.server = QLocalServer()
        self.server.listen(self.key)
        self.server.newConnection.connect(self._on_connection)

    def _on_connection(self):
        conn = self.server.nextPendingConnection()
        if conn is not None:
            conn.disconnected.connect(conn.deleteLater)
            conn.disconnectFromServer()
        if self.callback:
            self.callback()


def bring_to_front(window):
    if window.isMinimized():
        window.showNormal()
    window.show()
    window.raise_()
    window.activateWindow()


# --------------------------------------------------------------------------- #
#  Point d'entree
# --------------------------------------------------------------------------- #
def main():
    data_dir = get_data_dir()
    setup_logging(os.path.join(data_dir, "logs"))
    test_mode = "--test" in sys.argv

    if os.environ.get("REVLO_SAFE_GRAPHICS") == "1":     # depannage : ecran blanc / pilotes graphiques
        os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu")

    if os.name == "nt":                                   # icone correcte dans la barre des taches
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
        except Exception:
            pass

    try:
        QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    except Exception:
        pass

    app = QApplication([sys.argv[0]])
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setOrganizationName(APP_ORG)
    app.setWindowIcon(load_app_icon())
    app.setQuitOnLastWindowClosed(True)

    single = SingleInstance(SINGLE_INSTANCE_KEY)
    if not test_mode and single.already_running():
        return 0

    profile = create_profile(app, data_dir)
    window = MainWindow(profile, test_mode=test_mode)
    if not test_mode:
        single.listen(lambda: bring_to_front(window))
    window.show()

    code = app.exec()

    # Arret propre : les pages doivent etre detruites avant le profil (ecriture correcte des cookies).
    for popup in list(_POPUPS):
        popup.close()
    window.close()
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _POPUPS.clear()
    del window
    gc.collect()
    return code


if __name__ == "__main__":
    sys.exit(main())
