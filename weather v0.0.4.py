import sys
import requests
import random
import math
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QRadialGradient, QFont, QPainterPath

LAT = 17.3850
LON = 78.4867


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
    def __init__(self, icon, label, color):
        super().__init__()
        self.color = color
        self.current_value = 0
        self.target_value = 0
        
        self.setFixedHeight(90)
        self.setStyleSheet(f"""
            QFrame {{
                background: #1a1a1a;
                border-left: 4px solid {color};
                border-radius: 0px;
            }}
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            font-size: 36px;
            color: {color};
        """)
        icon_label.setFixedWidth(50)
        
        # Content
        content = QVBoxLayout()
        content.setSpacing(4)
        
        self.label = QLabel(label)
        self.label.setStyleSheet("""
            font-size: 11px;
            color: #666;
            font-weight: 600;
            letter-spacing: 1.5px;
        """)
        
        self.value = QLabel("--")
        self.value.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 800;
            color: {color};
            font-family: 'Courier New';
        """)
        
        content.addWidget(self.label)
        content.addWidget(self.value)
        
        layout.addWidget(icon_label)
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
        
        # Particle timer
        self.particle_timer = QTimer()
        self.particle_timer.timeout.connect(self.update_particles)
        self.particle_timer.start(16)  # ~60fps
        
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Location
        self.location = QLabel("LOADING...")
        self.location.setStyleSheet("""
            font-size: 16px;
            color: #666;
            font-weight: 700;
            letter-spacing: 3px;
        """)
        
        # Temperature (huge and bold)
        self.temperature = QLabel("--°")
        self.temperature.setStyleSheet("""
            font-size: 160px;
            font-weight: 900;
            color: white;
            line-height: 0.9;
            font-family: 'Arial Black';
        """)
        
        # Condition
        self.condition = QLabel("Clear")
        self.condition.setStyleSheet("""
            font-size: 28px;
            color: #999;
            font-weight: 300;
            letter-spacing: 2px;
        """)
        
        layout.addWidget(self.location)
        layout.addSpacing(10)
        layout.addWidget(self.temperature)
        layout.addWidget(self.condition)
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
        self.setFixedSize(600, 850)
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
        self.weather_display.setFixedHeight(450)
        
        # Metrics container
        metrics_container = QFrame()
        metrics_container.setStyleSheet("background: #0a0a0a;")
        
        metrics_layout = QVBoxLayout()
        metrics_layout.setContentsMargins(0, 30, 0, 30)
        metrics_layout.setSpacing(1)  # Thin divider effect
        
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
        metrics_layout.addWidget(header)
        
        # Metric bars
        self.humidity_bar = MetricBar("💧", "HUMIDITY", "#00D9FF")
        self.pressure_bar = MetricBar("⬇️", "PRESSURE", "#FF3366")
        self.wind_bar = MetricBar("💨", "WIND SPEED", "#FFD700")
        self.visibility_bar = MetricBar("👁", "VISIBILITY", "#00FF88")
        
        metrics_layout.addWidget(self.humidity_bar)
        metrics_layout.addWidget(self.pressure_bar)
        metrics_layout.addWidget(self.wind_bar)
        metrics_layout.addWidget(self.visibility_bar)
        
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
        self.weather_display.temperature.setStyleSheet(original.replace("color: white", "color: #FF0066"))
        QTimer.singleShot(50, lambda: self.weather_display.temperature.setStyleSheet(original))
        
    def load_weather(self):
        try:
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
            geo = requests.get(geo_url, headers={"User-Agent": "weather-app"}).json()
            
            current = weather["current"]
            visibility = weather["hourly"]["visibility"][0]
            addr = geo["address"]
            
            city = addr.get("city", "Unknown").upper()
            temp = current['temperature_2m']
            
            # Update main display
            self.weather_display.location.setText(city)
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
            
        except Exception as e:
            print(f"Error: {e}")
            self.weather_display.location.setText("ERROR")
            self.weather_display.temperature.setText("--°")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WeatherApp()
    window.show()
    sys.exit(app.exec())