from .runtime import DesktopAppRuntime


def run_gui(project_root="."):
    try:
        from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QListWidget, QTabWidget, QLineEdit
    except Exception as exc:
        raise RuntimeError("PySide6 fehlt. Installiere mit: pip install PySide6") from exc

    import sys
    rt = DesktopAppRuntime(project_root)

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("SecondBrain OS Desktop")
            self.resize(1200, 760)
            tabs = QTabWidget()
            tabs.addTab(self.dashboard(), "Dashboard")
            tabs.addTab(self.chat(), "Chat")
            tabs.addTab(self.knowledge(), "Knowledge")
            tabs.addTab(self.tasks(), "Tasks")
            tabs.addTab(self.notifications(), "Notifications")
            tabs.addTab(self.settings(), "Settings")
            self.setCentralWidget(tabs)

        def dashboard(self):
            w = QWidget(); layout = QVBoxLayout()
            self.dashboard_label = QLabel(str(rt.status()))
            start = QPushButton("Runtime starten"); stop = QPushButton("Runtime stoppen"); refresh = QPushButton("Aktualisieren")
            start.clicked.connect(lambda: (rt.start_runtime(), self.refresh_dashboard()))
            stop.clicked.connect(lambda: (rt.stop_runtime(), self.refresh_dashboard()))
            refresh.clicked.connect(self.refresh_dashboard)
            layout.addWidget(self.dashboard_label); layout.addWidget(start); layout.addWidget(stop); layout.addWidget(refresh)
            w.setLayout(layout); return w

        def refresh_dashboard(self):
            self.dashboard_label.setText(str(rt.status()))

        def chat(self):
            w = QWidget(); layout = QVBoxLayout()
            self.chat_history = QTextEdit(); self.chat_history.setReadOnly(True)
            self.chat_input = QLineEdit(); send = QPushButton("Senden")
            send.clicked.connect(self.send_chat)
            layout.addWidget(self.chat_history); layout.addWidget(self.chat_input); layout.addWidget(send)
            w.setLayout(layout); self.refresh_chat(); return w

        def send_chat(self):
            if self.chat_input.text():
                rt.chat(self.chat_input.text()); self.chat_input.clear(); self.refresh_chat()

        def refresh_chat(self):
            self.chat_history.setText("\\n".join([f"{m['role']}: {m['text']}" for m in rt.messages()]))

        def knowledge(self):
            w = QWidget(); layout = QVBoxLayout()
            self.knowledge_list = QListWidget(); self.knowledge_input = QLineEdit(); add = QPushButton("Wissen hinzufügen")
            add.clicked.connect(self.add_knowledge)
            layout.addWidget(self.knowledge_list); layout.addWidget(self.knowledge_input); layout.addWidget(add)
            w.setLayout(layout); self.refresh_knowledge(); return w

        def add_knowledge(self):
            if self.knowledge_input.text():
                rt.add_knowledge(self.knowledge_input.text()); self.knowledge_input.clear(); self.refresh_knowledge()

        def refresh_knowledge(self):
            self.knowledge_list.clear()
            for item in rt.knowledge(): self.knowledge_list.addItem(item["title"])

        def tasks(self):
            w = QWidget(); layout = QVBoxLayout()
            self.task_list = QListWidget(); self.task_input = QLineEdit(); add = QPushButton("Task hinzufügen")
            add.clicked.connect(self.add_task)
            layout.addWidget(self.task_list); layout.addWidget(self.task_input); layout.addWidget(add)
            w.setLayout(layout); self.refresh_tasks(); return w

        def add_task(self):
            if self.task_input.text():
                rt.add_task(self.task_input.text()); self.task_input.clear(); self.refresh_tasks()

        def refresh_tasks(self):
            self.task_list.clear()
            for item in rt.tasks(): self.task_list.addItem(f"{item['column']} | {item['priority']} | {item['title']}")

        def notifications(self):
            w = QWidget(); layout = QVBoxLayout()
            self.notification_list = QListWidget(); add = QPushButton("Testbenachrichtigung")
            add.clicked.connect(lambda: (rt.notify("Test", "Benachrichtigung"), self.refresh_notifications()))
            layout.addWidget(self.notification_list); layout.addWidget(add)
            w.setLayout(layout); self.refresh_notifications(); return w

        def refresh_notifications(self):
            self.notification_list.clear()
            for item in rt.notifications(): self.notification_list.addItem(f"{item['level']} | {item['title']} | {item['message']}")

        def settings(self):
            w = QWidget(); layout = QVBoxLayout()
            self.settings_label = QLabel(str(rt.settings())); toggle = QPushButton("Theme wechseln")
            toggle.clicked.connect(self.toggle_theme)
            layout.addWidget(self.settings_label); layout.addWidget(toggle)
            w.setLayout(layout); return w

        def toggle_theme(self):
            theme = rt.settings().get("theme", "dark")
            rt.set_setting("theme", "light" if theme == "dark" else "dark")
            self.settings_label.setText(str(rt.settings()))

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()
