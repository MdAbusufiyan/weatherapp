import sys
import requests
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt

LAT = 17.3850   # change if needed
LON = 78.4867

class WeatherApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Weather")
        self.setFixedSize(360, 520)

        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1e3c72,
                    stop:1 #2a5298
                );
                color: white;
                font-family: Segoe UI;
            }

            QPushButton {
                background-color: rgba(255,255,255,0.2);
                border-radius: 12px;
                padding: 10px;
                font-size: 16px;
            }

            QPushButton:hover {
                background-color: rgba(255,255,255,0.35);
            }
        """)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.city = QLabel("My Location")
        self.city.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.city.setStyleSheet("font-size: 28px; font-weight: bold;")

        self.temp = QLabel("--°C")
        self.temp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.temp.setStyleSheet("font-size: 72px;")

        self.wind = QLabel("")
        self.wind.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wind.setStyleSheet("font-size: 18px;")

        self.button = QPushButton("Refresh Weather")
        self.button.clicked.connect(self.load_weather)

        layout.addWidget(self.city)
        layout.addSpacing(20)
        layout.addWidget(self.temp)
        layout.addWidget(self.wind)
        layout.addSpacing(30)
        layout.addWidget(self.button)

        self.setLayout(layout)
        self.load_weather()

    def load_weather(self):
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={LAT}&longitude={LON}&current_weather=true"
        )

        try:
            data = requests.get(url).json()
            w = data["current_weather"]

            self.temp.setText(f"{w['temperature']}°C")
            self.wind.setText(f"Wind: {w['windspeed']} km/h")
        except:
            self.temp.setText("Error")

app = QApplication(sys.argv)
window = WeatherApp()
window.show()
sys.exit(app.exec())
