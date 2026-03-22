import sys
import requests
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout,
    QPushButton, QGridLayout, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QPropertyAnimation

LAT = 17.3850
LON = 78.4867


# ---------- Glass Metric Card ----------
class InfoCard(QFrame):
    def __init__(self, title):
        super().__init__()

        self.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.10);
                border-radius: 18px;
                border: 1px solid rgba(255,255,255,0.25);
                padding: 14px;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setOffset(0,4)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title = QLabel(title)
        self.title.setStyleSheet("font-size:14px;color:rgba(255,255,255,0.7);")

        self.value = QLabel("--")
        self.value.setStyleSheet("font-size:28px;font-weight:600;")

        layout.addWidget(self.title)
        layout.addWidget(self.value)
        self.setLayout(layout)


# ---------- Main Window ----------
class WeatherApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Weather")
        self.setFixedSize(420, 640)

        self.setStyleSheet("""
            QWidget {
                background:qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 #141e30, stop:1 #243b55);
                color:white;
                font-family: Segoe UI;
            }
        """)

        main = QVBoxLayout()
        main.setContentsMargins(24,24,24,24)
        main.setSpacing(18)

        # ---------- Header Glass Panel ----------
        header = QFrame()
        header.setStyleSheet("""
            QFrame{
                background: rgba(255,255,255,0.10);
                border-radius: 22px;
                border:1px solid rgba(255,255,255,0.25);
                padding:20px;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(35)
        shadow.setOffset(0,6)
        header.setGraphicsEffect(shadow)

        header_layout = QVBoxLayout()

        self.city = QLabel("Loading...")
        self.city.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.city.setStyleSheet("font-size:30px;font-weight:600;")

        self.temp = QLabel("--°C")
        self.temp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.temp.setStyleSheet("font-size:84px;font-weight:200;")

        header_layout.addWidget(self.city)
        header_layout.addWidget(self.temp)
        header.setLayout(header_layout)

        main.addWidget(header)

        # ---------- Metric Cards ----------
        grid = QGridLayout()
        grid.setSpacing(15)

        self.humidity = InfoCard("Humidity")
        self.pressure = InfoCard("Pressure")
        self.visibility = InfoCard("Visibility")
        self.wind = InfoCard("Wind")

        grid.addWidget(self.humidity,0,0)
        grid.addWidget(self.pressure,0,1)
        grid.addWidget(self.visibility,1,0)
        grid.addWidget(self.wind,1,1)

        main.addLayout(grid)

        self.setLayout(main)

        self.load_weather()

    # ---------- Load Weather ----------
    def load_weather(self):
        weather_url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={LAT}&longitude={LON}"
            "&current=temperature_2m,relativehumidity_2m,pressure_msl,wind_speed_10m"
            "&hourly=visibility"
        )

        geo_url = (
            "https://nominatim.openstreetmap.org/reverse"
            f"?lat={LAT}&lon={LON}&format=json"
        )

        weather = requests.get(weather_url).json()
        geo = requests.get(geo_url,headers={"User-Agent":"weather-app"}).json()

        current = weather["current"]
        visibility = weather["hourly"]["visibility"][0]

        addr = geo["address"]

        self.city.setText(addr.get("city","Unknown"))
        self.temp.setText(f"{current['temperature_2m']}°C")

        self.humidity.value.setText(f"{current['relativehumidity_2m']}%")
        self.pressure.value.setText(f"{current['pressure_msl']} hPa")
        self.wind.value.setText(f"{current['wind_speed_10m']} km/h")
        self.visibility.value.setText(f"{int(visibility/1000)} km")


app = QApplication(sys.argv)
window = WeatherApp()
window.show()
sys.exit(app.exec())
