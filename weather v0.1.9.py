import sys
import requests
import random
import math
import geonamescache
import os
import json
from timezonefinder import TimezoneFinder
from zoneinfo import ZoneInfo
import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QGridLayout, QPushButton, QSizePolicy, QLineEdit, QCompleter
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QRectF, QObject, QThread, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QRadialGradient, QFont, QPainterPath

LAT = 17.3850
LON = 78.4867


# ---------- Animated Analog Clock ----------
class AnalogClock(QWidget):
    def __init__(self):
        super().__init__()
        # --- cached drawing resources ---
        self.cached_gradients = {}
        self.cached_brushes = {
            "white": QBrush(QColor(255, 255, 255))
        }
        self.setFixedSize(120, 120)
        self.tz = ZoneInfo("UTC")
        
        # Update every second
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)
    
    def set_timezone(self, tz_name):
        try:
            self.tz = ZoneInfo(tz_name)
        except:
            self.tz = ZoneInfo("UTC")

    def paintEvent(self, event):
        import datetime
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Center point
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = min(center_x, center_y) - 10
        
        # Clock face - outer glow
        gradient = QRadialGradient(center_x, center_y, radius)
        gradient.setColorAt(0, QColor(255, 255, 255, 30))
        gradient.setColorAt(0.8, QColor(255, 255, 255, 10))
        gradient.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(center_x - radius), int(center_y - radius), 
                          int(radius * 2), int(radius * 2))
        
        # Clock circle
        painter.setPen(QPen(QColor(255, 255, 255, 100), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(int(center_x - radius), int(center_y - radius), 
                          int(radius * 2), int(radius * 2))
        
        # Hour markers
        painter.setPen(QPen(QColor(255, 255, 255, 150), 2))
        for i in range(12):
            angle = math.radians(i * 30 - 90)
            x1 = center_x + math.cos(angle) * (radius - 10)
            y1 = center_y + math.sin(angle) * (radius - 10)
            x2 = center_x + math.cos(angle) * (radius - 5)
            y2 = center_y + math.sin(angle) * (radius - 5)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        # Get current time
        now = datetime.datetime.now(self.tz)
        hour = now.hour % 12
        minute = now.minute
        second = now.second
        
        # Hour hand
        hour_angle = math.radians((hour + minute / 60) * 30 - 90)
        painter.setPen(QPen(QColor(255, 255, 255, 200), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(
            int(center_x), int(center_y),
            int(center_x + math.cos(hour_angle) * radius * 0.5),
            int(center_y + math.sin(hour_angle) * radius * 0.5)
        )
        
        # Minute hand
        minute_angle = math.radians(minute * 6 - 90)
        painter.setPen(QPen(QColor(0, 217, 255), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(
            int(center_x), int(center_y),
            int(center_x + math.cos(minute_angle) * radius * 0.7),
            int(center_y + math.sin(minute_angle) * radius * 0.7)
        )
        
        # Second hand (animated)
        second_angle = math.radians(second * 6 - 90)
        painter.setPen(QPen(QColor(255, 51, 102), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(
            int(center_x), int(center_y),
            int(center_x + math.cos(second_angle) * radius * 0.8),
            int(center_y + math.sin(second_angle) * radius * 0.8)
        )
        
        # Center dot
        painter.setBrush(QBrush(QColor(255, 51, 102)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(center_x - 4), int(center_y - 4), 8, 8)


# ---------- Collapsible Address Panel ----------
class AddressPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.expanded = False
        self.target_height = 0
        self.current_height = 0
        
        self.setStyleSheet("""
            QFrame {
                background: rgba(26, 26, 26, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 0px;
            }
        """)
        
        self.current_height = 0

        self.setMinimumHeight(40)     # button always visible
        self.setMaximumHeight(40)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Toggle button
        self.toggle_btn = QPushButton("▼ LOCATION INFO")
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: rgba(255, 255, 255, 0.6);
                border: none;
                padding: 12px;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 2px;
                text-align: left;
            }
            QPushButton:hover {
                color: #00D9FF;
                background: rgba(255, 255, 255, 0.05);
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle)
        
        # Content (hidden by default)
        self.content = QFrame()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 10, 20, 15)
        content_layout.setSpacing(8)
        
        # Coordinates
        coord_label = QLabel("COORDINATES")
        coord_label.setStyleSheet("""
            font-size: 9px;
            color: #666;
            font-weight: 600;
            letter-spacing: 1.5px;
        """)
        
        self.coords = QLabel(f"{LAT}°N, {LON}°E")
        self.coords.setStyleSheet("""
            font-size: 13px;
            color: #00D9FF;
            font-weight: 600;
            font-family: 'Courier New';
        """)
        
        # Full address
        addr_label = QLabel("ADDRESS")
        addr_label.setStyleSheet("""
            font-size: 9px;
            color: #666;
            font-weight: 600;
            letter-spacing: 1.5px;
            margin-top: 8px;
        """)
        
        self.full_address = QLabel("Loading...")
        self.full_address.setStyleSheet("""
            font-size: 11px;
            color: rgba(255, 255, 255, 0.7);
            font-weight: 400;
        """)
        self.full_address.setWordWrap(True)
        
        content_layout.addWidget(coord_label)
        content_layout.addWidget(self.coords)
        content_layout.addWidget(addr_label)
        content_layout.addWidget(self.full_address)
        
        self.content.setLayout(content_layout)
        self.content.setVisible(False)

        
        main_layout.addWidget(self.toggle_btn)
        main_layout.addWidget(self.content)
        
        self.setLayout(main_layout)
        
        # Animation
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.animate_height)
        
    def toggle(self):
        self.expanded = not self.expanded
        if self.expanded:
            self.toggle_btn.setText("▲ LOCATION INFO")
            self.target_height = 140
        else:
            self.toggle_btn.setText("▼ LOCATION INFO")
            self.target_height = 0
        
        self.anim_timer.start(16)
    
    def animate_height(self):
        diff = self.target_height - self.current_height
        if abs(diff) < 1:
            self.current_height = self.target_height
            self.anim_timer.stop()
        else:
            self.current_height += diff * 0.2
        
        total_height = int(40 + self.current_height)  # 40 for button
        self.setMaximumHeight(total_height)

        
        if self.current_height > 0:
            self.content.setVisible(True)
        else:
            self.content.setVisible(False)


    
    def set_address(self, full_addr):
        self.full_address.setText(full_addr)


# ---------- Geometric Icon Widget ----------
class GeometricIcon(QWidget):
    def __init__(self, icon_type, color):
        super().__init__()
        self.icon_type = icon_type
        self.color = QColor(color)
        self.setFixedSize(40, 40)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self.color))
        
        if self.icon_type == "humidity":
            # Water droplet
            path = QPainterPath()
            path.moveTo(20, 10)
            path.cubicTo(10, 15, 10, 25, 20, 32)
            path.cubicTo(30, 25, 30, 15, 20, 10)
            painter.drawPath(path)
            
        elif self.icon_type == "pressure":
            # Arrow down
            painter.drawRect(16, 8, 8, 16)
            points = [QPoint(20, 30), QPoint(12, 22), QPoint(28, 22)]
            painter.drawPolygon(points)
            
        elif self.icon_type == "wind":
            # Wind lines
            painter.setPen(QPen(self.color, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(10, 12, 30, 12)
            painter.drawLine(10, 20, 25, 20)
            painter.drawLine(10, 28, 32, 28)
            
        elif self.icon_type == "visibility":
            # Eye
            painter.drawEllipse(12, 16, 16, 8)
            painter.setBrush(QBrush(QColor("#0a0a0a")))
            painter.drawEllipse(17, 18, 6, 6)
            
        elif self.icon_type == "uv":
            # Sun rays
            painter.drawEllipse(14, 14, 12, 12)
            painter.setPen(QPen(self.color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            for i in range(8):
                angle = i * 45
                rad = math.radians(angle)
                x1 = 20 + math.cos(rad) * 10
                y1 = 20 + math.sin(rad) * 10
                x2 = 20 + math.cos(rad) * 14
                y2 = 20 + math.sin(rad) * 14
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
                
        elif self.icon_type == "feels":
            # Thermometer
            painter.drawRect(17, 8, 6, 18)
            painter.drawEllipse(14, 24, 12, 12)
            painter.setBrush(QBrush(QColor("#0a0a0a")))
            painter.drawRect(19, 12, 2, 12)
            
        elif self.icon_type == "cloud":
            # Cloud
            path = QPainterPath()
            path.addEllipse(10, 18, 10, 10)
            path.addEllipse(16, 14, 12, 12)
            path.addEllipse(22, 18, 10, 10)
            painter.drawPath(path)


# ---------- Particle System ----------
class Particle:
    def __init__(self, x, y, weather_type="clear"):
        self.x = x
        self.y = y
        self.weather_type = weather_type
        
        if weather_type == "rain":
            self.vx = random.uniform(-0.5, 0.5)
            self.vy = random.uniform(3, 6)
            self.size = random.uniform(1, 3)
            self.opacity = random.uniform(0.3, 0.7)
        elif weather_type == "snow":
            self.vx = random.uniform(-0.3, 0.3)
            self.vy = random.uniform(0.5, 2)
            self.size = random.uniform(2, 5)
            self.opacity = random.uniform(0.5, 0.9)
        else:  # ambient
            self.vx = random.uniform(-0.2, 0.2)
            self.vy = random.uniform(-0.3, 0.3)
            self.size = random.uniform(1, 3)
            self.opacity = random.uniform(0.1, 0.3)
            self.pulse = random.uniform(0, math.pi * 2)
        
    def update(self, width, height):
        self.x += self.vx
        self.y += self.vy
        
        if self.weather_type in ["rain", "snow"]:
            if self.y > height:
                self.y = -10
                self.x = random.uniform(0, width)
        else:
            self.pulse += 0.05
            if self.x < 0 or self.x > width:
                self.vx *= -1
            if self.y < 0 or self.y > height:
                self.vy *= -1


# ---------- Metric Display ----------
class MetricBar(QFrame):
    def __init__(self, icon_type, label, color):
        super().__init__()
        self.color = color
        self.current_value = 0
        self.target_value = 0
        
        self.setMinimumHeight(40)
        self.setStyleSheet(f"""
            QFrame {{
                background: #1a1a1a;
                border-left: 4px solid {color};
                border-radius: 0px;
            }}
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(16)
        
        # Geometric Icon
        icon_widget = GeometricIcon(icon_type, color)
        
        # Content
        content = QVBoxLayout()
        content.setSpacing(4)
        
        self.label = QLabel(label)
        self.label.setStyleSheet("""
            font-size: 10px;
            color: #666;
            font-weight: 600;
            letter-spacing: 1.5px;
        """)
        
        self.value = QLabel("--")
        self.value.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 800;
            color: {color};
            font-family: 'Courier New';
        """)
        
        content.addWidget(self.label)
        content.addWidget(self.value)
        
        layout.addWidget(icon_widget)
        layout.addLayout(content)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Animation timer
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.animate_value)
        
    def set_value(self, value, suffix=""):
        self.target_value = value
        self.suffix = suffix
        self.anim_timer.start(20)
        
    def animate_value(self):
        diff = self.target_value - self.current_value
        if abs(diff) < 0.1:
            self.current_value = self.target_value
            self.anim_timer.stop()
        else:
            self.current_value += diff * 0.15
        
        self.value.setText(f"{self.current_value:.1f}{self.suffix}")


# ---------- Stylish Digital Clock ----------
class DigitalClock(QWidget):
    def __init__(self):
        super().__init__()
        self.tz = ZoneInfo("UTC")

        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)

        # TIME
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("""
            font-size: 75px;
            font-weight: 700;
            color: white;
            font-family: "Old English Text MT";
            background: transparent;
        """)

        # DATE
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label.setStyleSheet("""
            font-size: 18px;
            color: rgba(255,255,255,0.75);
            font-family: "Old English Text MT";
            background: transparent;
        """)
        from PyQt6.QtWidgets import QSizePolicy

        self.time_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        self.date_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        layout.addWidget(self.time_label)
        layout.addWidget(self.date_label)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

        self.update_time()

    def set_timezone(self, tz_name):
        try:
            self.tz = ZoneInfo(tz_name)
        except:
            self.tz = ZoneInfo("UTC")


    def update_time(self):
        now = datetime.datetime.now(self.tz)
        self.time_label.setText(now.strftime("%H:%M:%S"))
        self.date_label.setText(now.strftime("%a %d:%m:%Y"))


# ---------- Main Weather Display ----------
class WeatherDisplay(QFrame):
    def __init__(self):
        super().__init__()
        
        self.particles = []
        self.weather_type = "clear"
        # --- paint caches ---
        self.cached_gradients = {}
        self.cached_brushes = {
            "white": QBrush(QColor(255, 255, 255))
        }

        
        # Make background transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Particle timer
        self.particle_timer = QTimer()
        self.particle_timer.timeout.connect(self.update_particles)
        self.particle_timer.start(40)  # ~25fps
        
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # Top row: Location and Clock
        top_row = QHBoxLayout()
        top_row.setSpacing(20)
        
        # Location + search
        location_row = QHBoxLayout()
        location_row.setSpacing(8)

        self.location = QLabel("LOADING...")
        self.location.setStyleSheet("""
            font-size: 16px;
            color: white;
            font-weight: 700;
            letter-spacing: 3px;
            background: transparent;
        """)

        self.search_btn = QPushButton("⌕")
        self.search_btn.setFixedSize(26, 26)
        self.search_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: rgba(255,255,255,0.7);
                font-size: 14px;
            }
            QPushButton:hover {
                color: #00D9FF;
            }
        """)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter city...")
        self.search_input.setVisible(False)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: rgba(0,0,0,0.4);
                border: 1px solid rgba(255,255,255,0.2);
                color: white;
                padding: 4px;
            }
        """)

        location_row.addWidget(self.location)
        location_row.addWidget(self.search_btn)
        location_row.addWidget(self.search_input)

        # Analog clock
        self.clock = AnalogClock()
        clock_column = QVBoxLayout()
        clock_column.addWidget(self.clock, alignment=Qt.AlignmentFlag.AlignCenter)

        top_row.addLayout(location_row)
        top_row.addStretch()
        top_row.addLayout(clock_column)


        
        # Temperature (smaller now)
        self.temperature = QLabel("--°")
        self.temperature.setStyleSheet("""
            font-size: 100px;
            font-weight: 900;
            color: white;
            line-height: 0.9;
            font-family: 'Arial Black';
            background: transparent;
        """)
        
        # Condition
        self.condition = QLabel("Clear")
        self.condition.setStyleSheet("""
            font-size: 22px;
            color: rgba(255, 255, 255, 0.8);
            font-weight: 300;
            letter-spacing: 2px;
            background: transparent;
        """)
        
        layout.addLayout(top_row)
        layout.addSpacing(8)
        layout.addWidget(self.temperature)
        layout.addWidget(self.condition)
        layout.addStretch()
        self.digital_clock = DigitalClock()
        layout.addWidget(
            self.digital_clock,
            alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom
        )


        layout.addStretch()
        
        self.setLayout(layout)
        
    def set_weather_type(self, temp):
        if temp > 30:
            self.weather_type = "hot"
        elif temp > 20:
            self.weather_type = "clear"
        elif temp > 10:
            self.weather_type = "rain"
        else:
            self.weather_type = "snow"
        # Adaptive repaint rate
        if self.weather_type in ["rain", "snow"]:
            self.particle_timer.start(33)   # ~30 FPS
        else:
            self.particle_timer.start(70)   # ~14 FPS

        
        # Initialize particles
        self.particles = []
        if self.weather_type == "rain":
            count = int(60 * (self.width()/800 + 0.5))
            for _ in range(count):
                self.particles.append(
                    Particle(
                        random.uniform(0, self.width()),
                        random.uniform(0, self.height()),
                        "rain"
                    )
                )
        elif self.weather_type == "snow":
            count = int(40 * (self.width()/800 + 0.5))
            for _ in range(count):
                self.particles.append(
                    Particle(
                        random.uniform(0, self.width()),
                        random.uniform(0, self.height()),
                        "snow"
                    )
                )
        else:
            count = int(25 * (self.width()/800 + 0.5))
            for _ in range(count):
                self.particles.append(
                    Particle(
                        random.uniform(0, self.width()),
                        random.uniform(0, self.height()),
                        "ambient"
                    )
                )
    
    def get_gradient(self, weather_type):
        key = (weather_type, self.width(), self.height())

        if key in self.cached_gradients:
            return self.cached_gradients[key]

        gradient = QLinearGradient(0, 0, self.width(), self.height())

        if weather_type == "hot":
            gradient.setColorAt(0, QColor(255, 94, 77))
            gradient.setColorAt(1, QColor(245, 166, 35))
        elif weather_type == "rain":
            gradient.setColorAt(0, QColor(30, 60, 114))
            gradient.setColorAt(1, QColor(42, 82, 152))
        elif weather_type == "snow":
            gradient.setColorAt(0, QColor(162, 205, 234))
            gradient.setColorAt(1, QColor(230, 240, 250))
        else:
            gradient.setColorAt(0, QColor(0, 180, 219))
            gradient.setColorAt(1, QColor(0, 131, 176))

        self.cached_gradients[key] = gradient
        return gradient

    def update_particles(self):
        for p in self.particles:
            p.update(self.width(), self.height())
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        gradient = self.get_gradient(self.weather_type)

        painter.fillRect(self.rect(), gradient)
        
        # Draw particles
        for p in self.particles:
            painter.setOpacity(p.opacity)
            if self.weather_type == "rain":
                painter.setPen(QPen(QColor(255, 255, 255), p.size))
                painter.drawLine(int(p.x), int(p.y), int(p.x - p.vx * 3), int(p.y - p.vy * 3))
            elif self.weather_type == "snow":
                painter.setBrush(self.cached_brushes["white"])
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(int(p.x), int(p.y), int(p.size), int(p.size))
            else:
                glow_opacity = (math.sin(p.pulse) + 1) / 2
                painter.setOpacity(p.opacity * glow_opacity)
                painter.setBrush(self.cached_brushes["white"])
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(int(p.x), int(p.y), int(p.size), int(p.size))
        
        painter.setOpacity(1)

def get_appdata_file():
    base = Path(os.getenv("APPDATA") or Path.home() / ".local/share")
    app_dir = base / "WeatherBuddy"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir / "recent_cities.json"


def load_recent_cities():
    file = get_appdata_file()
    if file.exists():
        try:
            return json.loads(file.read_text())
        except:
            return []
    return []


def save_recent_city(city):
    file = get_appdata_file()
    cities = load_recent_cities()

    if city in cities:
        cities.remove(city)

    cities.insert(0, city)
    cities = cities[:10]  # keep last 10

    file.write_text(json.dumps(cities))

class WeatherWorker(QObject):
    finished = pyqtSignal(dict, dict)
    error = pyqtSignal(str)

    def __init__(self, lat, lon):
        super().__init__()
        self.lat = lat
        self.lon = lon

    def run(self):
        try:
            weather_url = (
                "https://api.open-meteo.com/v1/forecast"
                f"?latitude={self.lat}&longitude={self.lon}"
                "&current=temperature_2m,relativehumidity_2m,pressure_msl,wind_speed_10m,apparent_temperature,uv_index,cloud_cover"
                "&hourly=visibility"
            )

            geo_url = (
                "https://nominatim.openstreetmap.org/reverse"
                f"?lat={self.lat}&lon={self.lon}&format=json"
            )

            weather = requests.get(weather_url, timeout=5).json()
            geo = requests.get(
    geo_url,
    headers={"User-Agent": "weather-app"},
    timeout=(2, 4)   # connect timeout, read timeout
).json()

            self.finished.emit(weather, geo)

        except Exception as e:
            self.error.emit(str(e))

# ---------- Main Window ----------
class WeatherApp(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("WEATHER")
        self.setMinimumSize(600, 800)
        self.resize(650, 850)
        self.setStyleSheet("""
            QWidget {
                background: #0a0a0a;
                color: white;
            }
        """)
        self.lat = LAT
        self.lon = LON
        self.tzf = TimezoneFinder()

        main = QVBoxLayout()
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)
        
        # Main weather display (top half)
        self.weather_display = WeatherDisplay()
        self.weather_display.search_btn.clicked.connect(self.show_search)
        self.weather_display.search_input.returnPressed.connect(self.search_city)

        self.gc = geonamescache.GeonamesCache()
        self.city_data = self.gc.get_cities()

        self.weather_display.setMinimumHeight(380)
        
        # Metrics container
        metrics_container = QFrame()
        metrics_container.setStyleSheet("background: #0a0a0a;")
        self.refresh_completer()
        
        metrics_layout = QGridLayout()
        metrics_layout.setContentsMargins(0, 5, 0, 10)
        metrics_layout.setHorizontalSpacing(1)
        metrics_layout.setVerticalSpacing(1)
        
        # Header
        header = QLabel("LIVE METRICS")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            font-size: 12px;
            color: #444;
            font-weight: 700;
            letter-spacing: 3px;
            padding: 5px;
        """)
        
        # Create a container for the header
        header_container = QFrame()
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(header)
        header_container.setLayout(header_layout)
        
        # Add header spanning both columns
        metrics_layout.addWidget(header_container, 0, 0, 1, 2)
        
        # Metric bars in 2-column grid layout
        self.humidity_bar = MetricBar("humidity", "HUMIDITY", "#00D9FF")
        self.pressure_bar = MetricBar("pressure", "PRESSURE", "#FF3366")
        self.wind_bar = MetricBar("wind", "WIND SPEED", "#FFD700")
        self.visibility_bar = MetricBar("visibility", "VISIBILITY", "#00FF88")
        self.uv_bar = MetricBar("uv", "UV INDEX", "#FF6B35")
        self.feels_bar = MetricBar("feels", "FEELS LIKE", "#A78BFA")
        self.cloud_bar = MetricBar("cloud", "CLOUD COVER", "#60A5FA")
        
        # Add to grid (row, column)
        metrics_layout.addWidget(self.humidity_bar, 1, 0)
        metrics_layout.addWidget(self.pressure_bar, 1, 1)
        metrics_layout.addWidget(self.wind_bar, 2, 0)
        metrics_layout.addWidget(self.visibility_bar, 2, 1)
        metrics_layout.addWidget(self.uv_bar, 3, 0)
        metrics_layout.addWidget(self.feels_bar, 3, 1)
        metrics_layout.addWidget(self.cloud_bar, 4, 0, 1, 2)  # Span both columns
        
        metrics_container.setLayout(metrics_layout)
        
        # Address panel (collapsible)
        self.address_panel = AddressPanel()
        
        # Assembly
        main.addWidget(self.weather_display)
        main.addWidget(self.address_panel)
        main.addWidget(metrics_container)
        
        self.setLayout(main)
        
        # Load data
        QTimer.singleShot(10, self.load_weather)
        
        # Glitch effect on temperature
        self.glitch_timer = QTimer()
        self.glitch_timer.timeout.connect(self.glitch_effect)
        self.glitch_timer.start(5000)
        self.refresh_completer()

    def refresh_completer(self):
        cities = self.city_data

        CITY_LIST = sorted({c['name'] for c in self.city_data.values()})
        RECENT = load_recent_cities()
        CITY_LIST = RECENT + [c for c in CITY_LIST if c not in RECENT]

        completer = QCompleter(CITY_LIST)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)

        popup = completer.popup()
        popup.setStyleSheet("""
        QListView {
            background: #0f0f0f;
            color: white;
            border: 1px solid rgba(255,255,255,0.1);
            padding: 4px;
            font-size: 12px;
        }
        QListView::item { padding: 6px 10px; }
        QListView::item:selected {
            background: rgba(0,217,255,0.25);
            color: #00D9FF;
        }
        """)

        self.weather_display.search_input.setCompleter(completer)
    
        
    def glitch_effect(self):
        """Subtle glitch animation on temperature"""
        original = self.weather_display.temperature.styleSheet()
        
        # Flash red briefly
        glitched = original.replace("color: white", "color: #FF0066")
        self.weather_display.temperature.setStyleSheet(glitched)
        QTimer.singleShot(50, lambda: self.weather_display.temperature.setStyleSheet(original))
    
    def show_search(self):
        box = self.weather_display.search_input
        box.setVisible(not box.isVisible())
        box.setFocus()

    def search_city(self):
        city = self.weather_display.search_input.text().split(",")[0].strip()
        if not city:
            return

        try:
            geo_url = (
                "https://nominatim.openstreetmap.org/search"
                f"?q={city}&format=json&limit=1"
            )
            res = requests.get(
                geo_url,
                headers={"User-Agent": "weather-app"},
                timeout=(2, 4)   # connect timeout, read timeout
            ).json()
            if res:
                self.lat = float(res[0]["lat"])
                self.lon = float(res[0]["lon"])

                save_recent_city(city)   
                self.refresh_completer()

                self.load_weather()


        except Exception as e:
            print(e)

        self.weather_display.search_input.clear()
        self.weather_display.search_input.setVisible(False)
  
    def load_weather(self):
        self.thread = QThread()
        self.worker = WeatherWorker(self.lat, self.lon)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_weather_loaded)
        self.worker.error.connect(self.on_weather_error)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def on_weather_loaded(self, weather, geo):
        current = weather["current"]
        visibility = weather["hourly"]["visibility"][0]
        addr = geo["address"]

        city = addr.get("city", addr.get("town", addr.get("village", "Unknown"))).upper()
        temp = current['temperature_2m']

        road = addr.get("road", "")
        suburb = addr.get("suburb", "")
        state = addr.get("state", "")
        country = addr.get("country", "")
        postcode = addr.get("postcode", "")

        address_parts = [p for p in [road, suburb, state, postcode, country] if p]
        full_address = ", ".join(address_parts)

        tz_name = self.tzf.timezone_at(lat=self.lat, lng=self.lon)
        if tz_name:
            self.weather_display.digital_clock.set_timezone(tz_name)
            self.weather_display.clock.set_timezone(tz_name)

        self.weather_display.location.setText(city)
        self.weather_display.temperature.setText(f"{int(temp)}°")
        self.address_panel.set_address(full_address)

        if temp > 30:
            condition = "SCORCHING"
        elif temp > 25:
            condition = "WARM"
        elif temp > 15:
            condition = "MILD"
        else:
            condition = "COOL"

        self.weather_display.condition.setText(condition)
        self.weather_display.set_weather_type(temp)

        self.humidity_bar.set_value(current['relativehumidity_2m'], "%")
        self.pressure_bar.set_value(current['pressure_msl'], " hPa")
        self.wind_bar.set_value(current['wind_speed_10m'], " km/h")
        self.visibility_bar.set_value(visibility/1000, " km")
        self.uv_bar.set_value(current.get('uv_index', 0), "")
        self.feels_bar.set_value(current.get('apparent_temperature', temp), "°C")
        self.cloud_bar.set_value(current.get('cloud_cover', 0), "%")
   
    def on_weather_error(self, msg):
        print("Weather error:", msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WeatherApp()
    window.show()
    sys.exit(app.exec())