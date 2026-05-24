import sys
import os
import json

from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget,
    QToolBar, QLineEdit, QListWidget, QDockWidget
)
from PyQt6.QtWebEngineWidgets import QWebEngineView


class DBrowser(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("D-Browser")
        self.setGeometry(120, 80, 1400, 900)

        # =========================
        # STORAGE
        # =========================
        self.data_file = "d_browser_data.json"
        self.bookmarks = []

        # =========================
        # TABS (CHROME SAFE)
        # =========================
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)

        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.sync_urlbar)

        self.setCentralWidget(self.tabs)

        # =========================
        # TOOLBAR (CLEAN / NOT CLUTTERED)
        # =========================
        nav = QToolBar()
        nav.setMovable(False)
        self.addToolBar(nav)

        nav.setStyleSheet("""
            QToolBar {
                background: #202124;
                padding: 6px;
                spacing: 6px;
                border-bottom: 1px solid #2a2a2a;
            }

            QLineEdit {
                background: #303134;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 16px;
                font-size: 13px;
            }

            QToolButton {
                background: transparent;
                color: white;
            }
        """)

        # minimal chrome-like controls
        nav.addAction("←").triggered.connect(self.safe_back)
        nav.addAction("→").triggered.connect(self.safe_forward)
        nav.addAction("⟳").triggered.connect(self.safe_reload)
        nav.addAction("🏠").triggered.connect(self.home)
        nav.addAction("+").triggered.connect(self.add_tab)

        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.go_url)
        nav.addWidget(self.urlbar)

        # =========================
        # BOOKMARKS (SIDEBAR)
        # =========================
        self.book_dock = QDockWidget("Bookmarks", self)
        self.book_list = QListWidget()
        self.book_list.itemClicked.connect(self.open_bookmark)

        self.book_dock.setWidget(self.book_list)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.book_dock)

        # =========================
        # LOAD SESSION
        # =========================
        self.load()

        if self.tabs.count() == 0:
            self.add_tab()

    # =========================
    # SAFE TAB HANDLING (NO CRASH ZONE)
    # =========================
    def current(self):
        w = self.tabs.currentWidget()
        return w if isinstance(w, QWebEngineView) else None

    def add_tab(self, url=None):
        browser = QWebEngineView()

        if url:
            browser.setUrl(QUrl(url))
            title = "Tab"
        else:
            browser.setUrl(QUrl("https://www.google.com"))
            title = "New Tab"

        i = self.tabs.addTab(browser, title)
        self.tabs.setCurrentIndex(i)

        browser.urlChanged.connect(lambda q, b=browser: self.update_url(q, b))
        browser.titleChanged.connect(lambda t, i=i: self.tabs.setTabText(i, t[:15]))

    def close_tab(self, i):
        if self.tabs.count() > 1:
            self.tabs.removeTab(i)

    # =========================
    # NAVIGATION (SAFE WRAPPERS)
    # =========================
    def safe_back(self):
        v = self.current()
        if v and v.history().canGoBack():
            v.back()

    def safe_forward(self):
        v = self.current()
        if v and v.history().canGoForward():
            v.forward()

    def safe_reload(self):
        v = self.current()
        if v:
            v.reload()

    def go_url(self):
        v = self.current()
        if not v:
            return

        url = self.urlbar.text().strip()

        if not url:
            return

        if "." not in url:
            url = "https://www.google.com/search?q=" + url
        elif not url.startswith("http"):
            url = "https://" + url

        v.setUrl(QUrl(url))

    def home(self):
        v = self.current()
        if v:
            v.setUrl(QUrl("https://www.google.com"))

    # =========================
    # URL SYNC
    # =========================
    def update_url(self, q, browser):
        if browser == self.current():
            self.urlbar.setText(q.toString())

    def sync_urlbar(self):
        v = self.current()
        if v:
            self.urlbar.setText(v.url().toString())

    # =========================
    # BOOKMARKS
    # =========================
    def add_bookmark(self):
        v = self.current()
        if not v:
            return

        url = v.url().toString()
        if url not in self.bookmarks:
            self.bookmarks.append(url)
            self.book_list.addItem(url)

    def open_bookmark(self, item):
        v = self.current()
        if v:
            v.setUrl(QUrl(item.text()))

    # =========================
    # SAVE / LOAD (CRASH PROOF)
    # =========================
    def save(self):
        try:
            tabs = []
            for i in range(self.tabs.count()):
                w = self.tabs.widget(i)
                if isinstance(w, QWebEngineView):
                    tabs.append(w.url().toString())

            data = {
                "tabs": tabs,
                "bookmarks": self.bookmarks,
                "current": self.tabs.currentIndex()
            }

            with open(self.data_file, "w") as f:
                json.dump(data, f, indent=2)

        except:
            pass

    def load(self):
        if not os.path.exists(self.data_file):
            return

        try:
            with open(self.data_file, "r") as f:
                data = json.load(f)
        except:
            return

        self.bookmarks = data.get("bookmarks", [])
        for b in self.bookmarks:
            self.book_list.addItem(b)

        for t in data.get("tabs", []):
            self.add_tab(t)

        if not data.get("tabs"):
            self.add_tab()

        self.tabs.setCurrentIndex(data.get("current", 0))

    def closeEvent(self, e):
        self.save()
        e.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = DBrowser()
    w.show()
    sys.exit(app.exec())