"""
PDF Editor — desktop application entry point.

Run with:
    python main.py

Dependencies (install via requirements.txt):
    pip install -r requirements.txt
"""


from app.ui.main_window import MainWindow


def main() -> None:
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
