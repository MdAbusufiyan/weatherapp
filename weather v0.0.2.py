import sys
import requests
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout,
    QPushButton, QGridLayout, QFrame
)
from PyQt6.QtCore import Qt, QPropertyAnimation

LAT = 17.3850
LON = 78.4867


class InfoCard(QFrame):
    def __init__(self, title):
        super().__init__()

        self.setFixedHeight(100)

        self.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.10);
                border-radius: 20px;
                border: 1px solid rgba(255,255,255,0.22);
            }
        """)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title = QLabel(title)
        self.title.setStyleSheet("font-size:13px;color:rgba(255,255,255,0.7);")

        self.value = QLabel("--")
        self.value.setStyleSheet("font-size:26px;font-weight:600;")

        layout.addWidget(self.title)
        layout.addWidget(self.value)
        self.setLayout(layout)

        # subtle breathing glow
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(2400)
        self.anim.setStartValue(0.92)
        self.anim.setEndValue(1)
        self.anim.setLoopCount(-1)
        self.anim.start()


class WeatherApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Weather Glass")
        self.setFixedSize(380, 580)

        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0,y1:0,x2:1,y2:1,
                    stop:0 #0f2027,
                    stop:1 #203a43
                );
                color:white;
                font-family: Segoe UI;
            }

            QPushButton {
                background: rgba(255,255,255,0.10);
                border-radius: 14px;
                padding: 12px;
                font-size: 15px;
                border: 1px solid rgba(255,255,255,0.25);
            }
        """)

        main = QVBoxLayout()
        main.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.city = QLabel("Loading...")
        self.city.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.city.setStyleSheet("font-size:30px;font-weight:600;")

        self.temp = QLabel("--°C")
        self.temp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.temp.setStyleSheet("font-size:86px;font-weight:300;")

        grid = QGridLayout()
        grid.setSpacing(16)

        self.humidity = InfoCard("Humidity")
        self.pressure = InfoCard("Pressure")
        self.visibility = InfoCard("Visibility")
        self.wind = InfoCard("Wind")

        grid.addWidget(self.humidity, 0, 0)
        grid.addWidget(self.pressure, 0, 1)
        grid.addWidget(self.visibility, 1, 0)
        grid.addWidget(self.wind, 1, 1)

        self.button = QPushButton("Refresh")
        self.button.clicked.connect(self.load_weather)

        main.addWidget(self.city)
        main.addWidget(self.temp)
        main.addSpacing(20)
        main.addLayout(grid)
        main.addSpacing(20)
        main.addWidget(self.button)

        self.setLayout(main)

        self.load_weather()

    def load_weather(self):
        try:
            print("Fetching weather...")

            weather_url = (
                "https://api.open-meteo.com/v1/forecast"
                f"?latitude={LAT}&longitude={LON}"
                "&current=temperature_2m,relativehumidity_2m,pressure_msl,wind_speed_10m"
                "&hourly=visibility"
            )

            # reliable reverse geocode
            geo_url = (
                "https://nominatim.openstreetmap.org/reverse"
                f"?lat={LAT}&lon={LON}&format=json"
            )

            weather = requests.get(weather_url).json()
            geo = requests.get(
                geo_url,
                headers={"User-Agent": "weather-app"}
            ).json()

            print("Weather:", weather)
            print("Geo:", geo)

            current = weather["current"]
            visibility = weather["hourly"]["visibility"][0]

            city_name = geo.get("address", {}).get("city") \
                        or geo.get("address", {}).get("town") \
                        or geo.get("address", {}).get("village") \
                        or "Unknown"

            self.city.setText(city_name)
            self.temp.setText(f"{current['temperature_2m']}°C")
            self.humidity.value.setText(f"{current['relativehumidity_2m']}%")
            self.pressure.value.setText(f"{current['pressure_msl']} hPa")
            self.wind.value.setText(f"{current['wind_speed_10m']} km/h")
            self.visibility.value.setText(f"{int(visibility/1000)} km")

            print("Weather updated successfully")

        except Exception as e:
            print("ERROR:", e)
            self.temp.setText("Error")


app = QApplication(sys.argv)
window = WeatherApp()
window.show()
sys.exit(app.exec())
