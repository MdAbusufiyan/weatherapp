import sys
import requests
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout,
    QPushButton, QGridLayout, QFrame
)
from PyQt6.QtCore import Qt

LAT = 17.3850
LON = 78.4867


class InfoCard(QFrame):
    def __init__(self, title):
        super().__init__()

        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255,255,255,0.15);
                border-radius: 14px;
            }
        """)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title = QLabel(title)
        self.title.setStyleSheet("font-size: 14px;")

        self.value = QLabel("--")
        self.value.setStyleSheet("font-size: 22px; font-weight: bold;")

        layout.addWidget(self.title)
        layout.addWidget(self.value)
        self.setLayout(layout)


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

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.city = QLabel("My Location")
        self.city.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.city.setStyleSheet("font-size: 28px; font-weight: bold;")

        self.temp = QLabel("--°C")
        self.temp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.temp.setStyleSheet("font-size: 72px;")

        # info cards
        grid = QGridLayout()

        self.humidity_card = InfoCard("Humidity")
        self.pressure_card = InfoCard("Pressure")
        self.visibility_card = InfoCard("Visibility")
        self.wind_card = InfoCard("Wind")

        grid.addWidget(self.humidity_card, 0, 0)
        grid.addWidget(self.pressure_card, 0, 1)
        grid.addWidget(self.visibility_card, 1, 0)
        grid.addWidget(self.wind_card, 1, 1)

        self.button = QPushButton("Refresh Weather")
        self.button.clicked.connect(self.load_weather)

        main_layout.addWidget(self.city)
        main_layout.addWidget(self.temp)
        main_layout.addSpacing(20)
        main_layout.addLayout(grid)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.button)

        self.setLayout(main_layout)
        self.load_weather()

    def load_weather(self):
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={LAT}&longitude={LON}"
            "&current=temperature_2m,relativehumidity_2m,pressure_msl,wind_speed_10m"
            "&hourly=visibility"
        )

        try:
            data = requests.get(url).json()

            current = data["current"]
            visibility = data["hourly"]["visibility"][0]

            self.temp.setText(f"{current['temperature_2m']}°C")
            self.humidity_card.value.setText(f"{current['relativehumidity_2m']}%")
            self.pressure_card.value.setText(f"{current['pressure_msl']} hPa")
            self.wind_card.value.setText(f"{current['wind_speed_10m']} km/h")
            self.visibility_card.value.setText(f"{int(visibility/1000)} km")

        except Exception:
            self.temp.setText("Error")


app = QApplication(sys.argv)
window = WeatherApp()
window.show()
sys.exit(app.exec())
