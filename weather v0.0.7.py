import sys
import requests
import random
import math
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QRadialGradient, QFont, QPainterPath

LAT = 17.3850
LON = 78.4867


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
        
        self.setMinimumHeight(75)
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


# ---------- Main Weather Display ----------
class WeatherDisplay(QFrame):
    def __init__(self):
        super().__init__()
        
        self.particles = []
        self.weather_type = "clear"
        
        # Make background transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Particle timer
        self.particle_timer = QTimer()
        self.particle_timer.timeout.connect(self.update_particles)
        self.particle_timer.start(16)  # ~60fps
        
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # Location with full address
        location_container = QVBoxLayout()
        location_container.setSpacing(5)
        
        self.location = QLabel("LOADING...")
        self.location.setStyleSheet("""
            font-size: 16px;
            color: white;
            font-weight: 700;
            letter-spacing: 3px;
            background: transparent;
        """)
        
        self.address = QLabel("...")
        self.address.setStyleSheet("""
            font-size: 11px;
            color: rgba(255, 255, 255, 0.6);
            font-weight: 400;
            letter-spacing: 1px;
            background: transparent;
        """)
        
        location_container.addWidget(self.location)
        location_container.addWidget(self.address)
        
        # Temperature (huge and bold)
        self.temperature = QLabel("--°")
        self.temperature.setStyleSheet("""
            font-size: 140px;
            font-weight: 900;
            color: white;
            line-height: 0.9;
            font-family: 'Arial Black';
            background: transparent;
        """)
        
        # Condition
        self.condition = QLabel("Clear")
        self.condition.setStyleSheet("""
            font-size: 24px;
            color: rgba(255, 255, 255, 0.8);
            font-weight: 300;
            letter-spacing: 2px;
            background: transparent;
        """)
        
        # Clock and Date
        time_container = QVBoxLayout()
        time_container.setSpacing(5)
        time_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.clock = QLabel("00:00:00")
        self.clock.setStyleSheet("""
            font-size: 42px;
            font-weight: 700;
            color: white;
            font-family: 'Courier New';
            letter-spacing: 4px;
            background: transparent;
        """)
        self.clock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.date = QLabel("01/01/2024")
        self.date.setStyleSheet("""
            font-size: 16px;
            font-weight: 500;
            color: rgba(255, 255, 255, 0.6);
            letter-spacing: 2px;
            background: transparent;
        """)
        self.date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        time_container.addWidget(self.clock)
        time_container.addWidget(self.date)
        
        layout.addLayout(location_container)
        layout.addSpacing(8)
        layout.addWidget(self.temperature)
        layout.addWidget(self.condition)
        layout.addSpacing(15)
        layout.addLayout(time_container)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Update clock every second
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_time)
        self.clock_timer.start(1000)
        self.update_time()
        
    def update_time(self):
        from datetime import datetime
        now = datetime.now()
        self.clock.setText(now.strftime("%H:%M:%S"))
        self.date.setText(now.strftime("%d/%m/%Y"))
        
    def set_weather_type(self, temp):
        if temp > 30:
            self.weather_type = "hot"
        elif temp > 20:
            self.weather_type = "clear"
        elif temp > 10:
            self.weather_type = "rain"
        else:
            self.weather_type = "snow"
        
        # Initialize particles
        self.particles = []
        if self.weather_type == "rain":
            for _ in range(80):
                self.particles.append(
                    Particle(
                        random.uniform(0, self.width()),
                        random.uniform(0, self.height()),
                        "rain"
                    )
                )
        elif self.weather_type == "snow":
            for _ in range(50):
                self.particles.append(
                    Particle(
                        random.uniform(0, self.width()),
                        random.uniform(0, self.height()),
                        "snow"
                    )
                )
        else:
            for _ in range(30):
                self.particles.append(
                    Particle(
                        random.uniform(0, self.width()),
                        random.uniform(0, self.height()),
                        "ambient"
                    )
                )
    
    def update_particles(self):
        for p in self.particles:
            p.update(self.width(), self.height())
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background gradient
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        if self.weather_type == "hot":
            gradient.setColorAt(0, QColor(255, 94, 77))
            gradient.setColorAt(1, QColor(245, 166, 35))
        elif self.weather_type == "rain":
            gradient.setColorAt(0, QColor(30, 60, 114))
            gradient.setColorAt(1, QColor(42, 82, 152))
        elif self.weather_type == "snow":
            gradient.setColorAt(0, QColor(162, 205, 234))
            gradient.setColorAt(1, QColor(230, 240, 250))
        else:
            gradient.setColorAt(0, QColor(0, 180, 219))
            gradient.setColorAt(1, QColor(0, 131, 176))
        
        painter.fillRect(self.rect(), gradient)
        
        # Draw particles
        for p in self.particles:
            painter.setOpacity(p.opacity)
            if self.weather_type == "rain":
                painter.setPen(QPen(QColor(255, 255, 255), p.size))
                painter.drawLine(int(p.x), int(p.y), int(p.x - p.vx * 3), int(p.y - p.vy * 3))
            elif self.weather_type == "snow":
                painter.setBrush(QBrush(QColor(255, 255, 255)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(int(p.x), int(p.y), int(p.size), int(p.size))
            else:
                glow_opacity = (math.sin(p.pulse) + 1) / 2
                painter.setOpacity(p.opacity * glow_opacity)
                painter.setBrush(QBrush(QColor(255, 255, 255)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(int(p.x), int(p.y), int(p.size), int(p.size))
        
        painter.setOpacity(1)


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
        
        main = QVBoxLayout()
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)
        
        # Main weather display (top half)
        self.weather_display = WeatherDisplay()
        self.weather_display.setMinimumHeight(380)
        
        # Metrics container
        metrics_container = QFrame()
        metrics_container.setStyleSheet("background: #0a0a0a;")
        
        metrics_layout = QGridLayout()
        metrics_layout.setContentsMargins(0, 20, 0, 20)
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
            padding: 15px;
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
        
        # Assembly
        main.addWidget(self.weather_display)
        main.addWidget(metrics_container)
        
        self.setLayout(main)
        
        # Load data
        self.load_weather()
        
        # Glitch effect on temperature
        self.glitch_timer = QTimer()
        self.glitch_timer.timeout.connect(self.glitch_effect)
        self.glitch_timer.start(5000)
        
    def glitch_effect(self):
        """Subtle glitch animation on temperature"""
        original = self.weather_display.temperature.styleSheet()
        
        # Flash red briefly
        glitched = original.replace("color: white", "color: #FF0066")
        self.weather_display.temperature.setStyleSheet(glitched)
        QTimer.singleShot(50, lambda: self.weather_display.temperature.setStyleSheet(original))
        
    def load_weather(self):
        try:
            weather_url = (
                "https://api.open-meteo.com/v1/forecast"
                f"?latitude={LAT}&longitude={LON}"
                "&current=temperature_2m,relativehumidity_2m,pressure_msl,wind_speed_10m,apparent_temperature,uv_index,cloud_cover"
                "&hourly=visibility"
            )
            
            geo_url = (
                "https://nominatim.openstreetmap.org/reverse"
                f"?lat={LAT}&lon={LON}&format=json"
            )
            
            weather = requests.get(weather_url).json()
            geo = requests.get(geo_url, headers={"User-Agent": "weather-app"}).json()
            
            current = weather["current"]
            visibility = weather["hourly"]["visibility"][0]
            addr = geo["address"]
            
            city = addr.get("city", addr.get("town", addr.get("village", "Unknown"))).upper()
            temp = current['temperature_2m']
            
            # Build address string
            state = addr.get("state", "")
            country = addr.get("country", "")
            address_parts = [p for p in [state, country] if p]
            address_str = ", ".join(address_parts).upper()
            
            # Update main display
            self.weather_display.location.setText(city)
            self.weather_display.address.setText(address_str)
            self.weather_display.temperature.setText(f"{int(temp)}°")
            
            # Set condition and weather type
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
            
            # Update metrics with animation
            self.humidity_bar.set_value(current['relativehumidity_2m'], "%")
            self.pressure_bar.set_value(current['pressure_msl'], " hPa")
            self.wind_bar.set_value(current['wind_speed_10m'], " km/h")
            self.visibility_bar.set_value(visibility/1000, " km")
            self.uv_bar.set_value(current.get('uv_index', 0), "")
            self.feels_bar.set_value(current.get('apparent_temperature', temp), "°C")
            self.cloud_bar.set_value(current.get('cloud_cover', 0), "%")
            
        except Exception as e:
            print(f"Error: {e}")
            self.weather_display.location.setText("ERROR")
            self.weather_display.address.setText("UNABLE TO LOAD")
            self.weather_display.temperature.setText("--°")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WeatherApp()
    window.show()
    sys.exit(app.exec())