"""
Streamlit приложение для детекции сонливости в реальном времени.
Использует веб-камеру для отслеживания глаз и показывает статус: Спит или Не Спит.
"""

import streamlit as st
import cv2
import numpy as np
import joblib
import os
import json
import math
import base64
from PIL import Image, ImageDraw, ImageFont
import time
from collections import deque
import statistics

import pydeck as pdk
import streamlit.components.v1 as components
from streamlit_js_eval import get_geolocation

# Настройка страницы
st.set_page_config(
    page_title="Eyes on Road",
    page_icon="😴",
    layout="wide"
)

LOGO_FILE = "WhatsApp Image 2026-05-14 at 12.15.35.jpeg"


def _image_to_data_uri(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    with open(path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def inject_custom_styles():
    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at 18% 10%, rgba(32, 224, 205, 0.20), transparent 34%),
                    linear-gradient(135deg, #006f67 0%, #008c80 46%, #075b56 100%);
                color: #ffffff;
            }

            [data-testid="stHeader"] {
                background: rgba(0, 96, 88, 0.78);
                backdrop-filter: blur(10px);
            }

            .stApp,
            .stApp p,
            .stApp span,
            .stApp label,
            .stApp div,
            .stApp h1,
            .stApp h2,
            .stApp h3,
            .stApp h4,
            .stApp li,
            .stApp [data-testid="stMarkdownContainer"],
            .stApp [data-testid="stMetricLabel"],
            .stApp [data-testid="stMetricValue"] {
                color: #ffffff;
            }

            .block-container {
                padding-top: 1.25rem;
            }

            .eyes-hero {
                display: grid;
                grid-template-columns: minmax(160px, 260px) 1fr;
                gap: 22px;
                align-items: center;
                padding: 22px;
                margin-bottom: 18px;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                background: rgba(0, 83, 77, 0.72);
                box-shadow: 0 18px 48px rgba(0, 0, 0, 0.24);
            }

            .eyes-hero img {
                width: 100%;
                max-height: 160px;
                object-fit: cover;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.12);
            }

            .eyes-hero h1 {
                margin: 0 0 8px 0;
                font-size: clamp(2rem, 5vw, 4.4rem);
                line-height: 1;
                letter-spacing: 0;
                color: #ffffff;
            }

            .eyes-hero p {
                margin: 0;
                max-width: 820px;
                color: #ffffff;
                font-size: 1.05rem;
            }

            .alert-strip {
                padding: 14px 16px;
                border-radius: 8px;
                margin: 12px 0;
                background: rgba(255, 74, 74, 0.24);
                border: 1px solid rgba(255, 107, 107, 0.65);
                color: #ffffff;
                font-weight: 700;
            }

            .ready-strip {
                padding: 12px 14px;
                border-radius: 8px;
                margin: 12px 0;
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.34);
                color: #ffffff;
            }

            div[data-testid="stMetric"] {
                background: rgba(0, 91, 84, 0.55);
                border: 1px solid rgba(255, 255, 255, 0.22);
                border-radius: 8px;
                padding: 12px;
            }

            div.stButton > button {
                min-height: 46px;
                border-radius: 8px;
                font-weight: 700;
                border: 1px solid rgba(255, 255, 255, 0.42);
                color: #ffffff;
                background: rgba(255, 255, 255, 0.12);
            }

            div.stButton > button[kind="primary"] {
                background: #19d4c2;
                color: #ffffff;
                border-color: #19d4c2;
            }

            .control-note {
                margin: 4px 0 14px;
                color: #ffffff;
                font-size: 0.95rem;
            }

            .section-label {
                margin: 0 0 8px;
                color: #ffffff;
                font-weight: 800;
            }

            div[data-baseweb="select"] * ,
            div[data-baseweb="input"] * ,
            input {
                color: #ffffff;
            }

            div[data-baseweb="select"] > div,
            div[data-baseweb="input"] > div {
                background: rgba(0, 76, 70, 0.72);
                border-color: rgba(255, 255, 255, 0.28);
            }

            .stAlert {
                color: #ffffff;
            }

            @media (max-width: 760px) {
                .eyes-hero {
                    grid-template-columns: 1fr;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header():
    logo_uri = _image_to_data_uri(LOGO_FILE)
    logo_html = f'<img src="{logo_uri}" alt="Eyes on Road logo" />' if logo_uri else ""
    st.markdown(
        f"""
        <div class="eyes-hero">
            {logo_html}
            <div>
                <h1>Eyes on Road</h1>
                <p>Детекция сонливости водителя в реальном времени: камера, статус глаз, предупреждения и ближайшие точки отдыха.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def trigger_browser_notification(title: str, body: str, key_suffix: str):
    components.html(
        f"""
        <script>
        (async () => {{
            const title = {json.dumps(title)};
            const body = {json.dumps(body)};
            if (!("Notification" in window)) return;
            try {{
                let permission = Notification.permission;
                if (permission === "default") {{
                    permission = await Notification.requestPermission();
                }}
                if (permission === "granted") {{
                    new Notification(title, {{ body, tag: "eyes-on-road-alert" }});
                }}
            }} catch (err) {{
                console.warn("Notification error", err);
            }}
        }})();
        </script>
        """,
        height=0,
    )


def trigger_audio_alarm(key_suffix: str):
    components.html(
        f"""
        <script>
        (() => {{
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) return;
            const ctx = new AudioContext();
            const gain = ctx.createGain();
            gain.gain.setValueAtTime(0.0001, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.75, ctx.currentTime + 0.04);
            gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 1.8);
            gain.connect(ctx.destination);

            [0, 0.28, 0.56, 0.84, 1.12].forEach((offset, index) => {{
                const osc = ctx.createOscillator();
                osc.type = "square";
                osc.frequency.setValueAtTime(index % 2 === 0 ? 980 : 760, ctx.currentTime + offset);
                osc.connect(gain);
                osc.start(ctx.currentTime + offset);
                osc.stop(ctx.currentTime + offset + 0.22);
            }});
        }})();
        </script>
        """,
        height=0,
    )

@st.cache_resource
def load_model():
    """
    Загружает обученную модель и связанные файлы с кэшированием
    """
    try:
        classifier = joblib.load('eye_classifier.pkl')
        scaler_candidates = [
            'eye_scaler.pkl',
            'eye_scaler_fast.pkl',
            'eye_scaler_universal.pkl',
        ]
        scaler_path = next((path for path in scaler_candidates if os.path.exists(path)), None)
        if scaler_path is None:
            raise FileNotFoundError(
                "Не найден scaler-файл: eye_scaler.pkl, eye_scaler_fast.pkl или eye_scaler_universal.pkl"
            )
        scaler = joblib.load(scaler_path)
        class_mapping = joblib.load('class_mapping.pkl')
        st.session_state.model_scaler_path = scaler_path
        return classifier, scaler, class_mapping
    except FileNotFoundError as e:
        st.error(f"Файл модели не найден: {e}")
        st.error("Сначала запустите обучение: python train.py")
        return None, None, None
    except Exception as e:
        st.error(f"Ошибка при загрузке модели: {e}")
        return None, None, None

def load_bus_stops():
    """
    Загружает данные остановок из JSON файла
    """
    try:
        with open('bus_stops.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Файл bus_stops.json не найден")
        return None
    except Exception as e:
        st.error(f"Ошибка при загрузке остановок: {e}")
        return None

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Вычисляет расстояние между двумя точками по формуле Haversine
    Возвращает расстояние в километрах
    """
    # Радиус Земли в километрах
    R = 6371.0
    
    # Конвертируем градусы в радианы
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Разности координат
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Формула Haversine
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def find_nearest_stop(user_lat, user_lon, route_name, bus_stops_data):
    """
    Находит ближайшую остановку на указанном маршруте
    """
    if not bus_stops_data or route_name not in bus_stops_data['routes']:
        return None
    
    route_stops = bus_stops_data['routes'][route_name]['stops']
    nearest_stop = None
    min_distance = float('inf')
    
    for stop in route_stops:
        distance = calculate_distance(user_lat, user_lon, stop['lat'], stop['lng'])
        if distance < min_distance:
            min_distance = distance
            nearest_stop = stop.copy()
            nearest_stop['distance_km'] = round(distance, 2)
    
    return nearest_stop


def is_rest_point_stop(stop: dict) -> bool:
    """
    «Точка для отдыха» на карте (явные правила):
    - основной критерий: в services есть «отель» (ночлёг);
    - дополнительно: одновременно «кафе» и «туалет» — короткая остановка для отдыха/санитарии.
    Остановки только с convenience без services не попадают в этот слой.
    """
    services = [str(s).lower() for s in stop.get("services", [])]
    if "отель" in services:
        return True
    if "кафе" in services and "туалет" in services:
        return True
    return False


def _unwrap_streamlit_js_eval_payload(raw):
    """Компонент streamlit-js-eval передаёт в Python обёртку {value, dataType: 'json'}."""
    if raw is None:
        return None
    if isinstance(raw, dict) and raw.get("dataType") == "json" and "value" in raw:
        inner = raw["value"]
        if isinstance(inner, str):
            try:
                return json.loads(inner)
            except json.JSONDecodeError:
                return inner
        return inner
    return raw


def _view_state_for_points(points: list[tuple[float, float]]) -> pdk.ViewState:
    if not points:
        return pdk.ViewState(latitude=48.0, longitude=67.0, zoom=4)
    lats = [p[0] for p in points]
    lngs = [p[1] for p in points]
    c_lat = sum(lats) / len(lats)
    c_lon = sum(lngs) / len(lngs)
    lat_spread = max(max(lats) - min(lats), 0.02)
    zoom = 7.0 - math.log(lat_spread * 100) / math.log(2)
    zoom = float(max(4.0, min(12.0, zoom)))
    return pdk.ViewState(latitude=c_lat, longitude=c_lon, zoom=zoom, pitch=0)


def build_route_map_deck(
    bus_stops_data: dict,
    route_id: str,
    user_lat: float | None,
    user_lon: float | None,
) -> pdk.Deck | None:
    """Карта маршрута: слой «отдых» + опционально маркер пользователя (GPS или ручная точка)."""
    if not bus_stops_data or route_id not in bus_stops_data.get("routes", {}):
        return None
    stops = bus_stops_data["routes"][route_id]["stops"]
    framing = [(float(s["lat"]), float(s["lng"])) for s in stops if "lat" in s and "lng" in s]
    rest_stops = [s for s in stops if is_rest_point_stop(s)]
    rest_data = [
        {"name": s.get("name", "—"), "lat": float(s["lat"]), "lng": float(s["lng"])}
        for s in rest_stops
    ]

    layers: list[pdk.Layer] = []
    if rest_data:
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=rest_data,
                id="rest_points",
                get_position="[lng, lat]",
                get_fill_color=[255, 140, 0, 220],
                get_radius=6000,
                pickable=True,
            )
        )

    user_data = []
    if user_lat is not None and user_lon is not None:
        user_data.append({"name": "Вы (GPS или ручной ввод)", "lat": float(user_lat), "lng": float(user_lon)})
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=user_data,
                id="user_position",
                get_position="[lng, lat]",
                get_fill_color=[30, 144, 255, 255],
                get_radius=9000,
                pickable=True,
            )
        )

    frame_pts = list(framing)
    if user_lat is not None and user_lon is not None:
        frame_pts.append((float(user_lat), float(user_lon)))
    view = _view_state_for_points(frame_pts)

    tooltip = {
        "html": "<b>{name}</b><br/>lat {lat}, lng {lng}",
        "style": {"backgroundColor": "#1e1e1e", "color": "white"},
    }

    return pdk.Deck(
        layers=layers,
        initial_view_state=view,
        tooltip=tooltip,
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    )


def detect_eyes(gray_img, eye_cascade):
    """
    Детекция глаз с оптимизированными параметрами
    """
    height, width = gray_img.shape
    
    if width > 1920:
        scale_factor = 1.05
        min_neighbors = 3
        min_size = (40, 40)
    elif width > 1280:
        scale_factor = 1.1
        min_neighbors = 4
        min_size = (35, 35)
    else:
        scale_factor = 1.1
        min_neighbors = 5
        min_size = (30, 30)
    
    eyes = eye_cascade.detectMultiScale(
        gray_img,
        scaleFactor=scale_factor, 
        minNeighbors=min_neighbors, 
        minSize=min_size,
        maxSize=(width//4, height//4)
    )
    
    return eyes

def classify_eye_state_fast(eye_img, classifier, scaler):
    """
    Быстрая классификация состояния глаза
    """
    if classifier is None or scaler is None:
        return None
    
    # Изменяем размер до 32x32 (как при обучении)
    eye_resized = cv2.resize(eye_img, (32, 32))
    eye_flattened = eye_resized.flatten().reshape(1, -1)
    
    # Нормализация и предсказание
    eye_scaled = scaler.transform(eye_flattened)
    prediction = classifier.predict(eye_scaled)[0]
    probability = classifier.predict_proba(eye_scaled)[0]
    
    return prediction, probability

def get_drowsiness_status(eyes, classifier, scaler, class_mapping):
    """
    Определяет общий статус сонливости на основе обнаруженных глаз
    """
    if not eyes or classifier is None:
        return "Неизвестно", 0.0
    
    drowsy_count = 0
    total_eyes = len(eyes)
    total_confidence = 0
    
    for (x, y, w, h) in eyes:
        # Здесь нужно будет получить ROI глаза для классификации
        # Пока используем упрощенную логику
        pass
    
    # Упрощенная логика для демонстрации
    # В реальности здесь должна быть классификация каждого глаза
    if total_eyes > 0:
        # Если найдены глаза, считаем что человек не спит
        return "Не Спит", 0.8
    else:
        return "Спит", 0.6

def main():
    """
    Основная функция Streamlit приложения
    """
    inject_custom_styles()
    render_header()
    
    # Загружаем модель и данные остановок
    classifier, scaler, class_mapping = load_model()
    bus_stops_data = load_bus_stops()
    
    if classifier is None:
        st.stop()
    
    # Информация о модели
    with st.expander("Информация о модели"):
        st.write(f"**Загружена модель для {len(class_mapping)} классов:**")
        for name, class_id in class_mapping.items():
            st.write(f"- {name}: класс {class_id}")
    
    # Основные колонки
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader("Камера и детекция")
        st.markdown(
            '<p class="control-note">Запустите камеру, держите лицо в кадре. Предупреждение появится после 3 секунд закрытых глаз, звук после 5 секунд.</p>',
            unsafe_allow_html=True,
        )
        
        # Кнопка для запуска/остановки камеры
        if 'camera_running' not in st.session_state:
            st.session_state.camera_running = False
        
        start_col, stop_col, state_col = st.columns([1, 1, 1.35])
        with start_col:
            if st.button("Старт", type="primary", disabled=st.session_state.camera_running, use_container_width=True):
                st.session_state.camera_running = True
                st.session_state.eye_closed_since = None
                st.session_state.warning_sent = False
                st.session_state.alarm_sent = False
                st.session_state.closed_seconds = 0.0
                st.session_state.missing_eye_frames = 0
                st.session_state.last_warning_at = 0.0
                st.session_state.last_alarm_at = 0.0
        
        with stop_col:
            if st.button("Стоп", disabled=not st.session_state.camera_running, use_container_width=True):
                st.session_state.camera_running = False

        with state_col:
            if st.session_state.camera_running:
                st.markdown('<div class="ready-strip">Камера активна</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="ready-strip">Камера выключена</div>', unsafe_allow_html=True)
        
        # Показываем видео с камеры
        if st.session_state.camera_running:
            # Создаем placeholder для видео
            video_placeholder = st.empty()
            alert_placeholder = st.empty()
            notification_placeholder = st.empty()
            alarm_placeholder = st.empty()
            
            # Инициализируем камеру
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                st.error("Не удалось открыть веб-камеру.")
                st.session_state.camera_running = False
                cap.release()
                return
            
            # Загружаем каскадный классификатор
            eye_cascade = cv2.CascadeClassifier('lol.xml')
            if eye_cascade.empty():
                st.error("Не удалось загрузить каскадный классификатор.")
                st.session_state.camera_running = False
                cap.release()
                return
            
            st.info("Камера запущена. Смотрите прямо в объектив.")
            
            # Основной цикл обработки видео
            while st.session_state.camera_running:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Зеркально отображаем изображение
                frame = cv2.flip(frame, 1)
                
                # Конвертируем в серый
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Детектируем глаза
                eyes = detect_eyes(gray, eye_cascade)
                
                # Обрабатываем каждый найденный глаз
                drowsiness_detected = False
                total_confidence = 0
                classified_eyes = 0
                open_eye_detected = False
                
                for (x, y, w, h) in eyes:
                    eye_roi = gray[y:y+h, x:x+w]
                    
                    result = classify_eye_state_fast(eye_roi, classifier, scaler)
                    if result is not None:
                        eye_state, probability = result
                        confidence = probability[eye_state]
                        classified_eyes += 1
                        total_confidence += confidence
                        
                        # Определяем цвет рамки на основе состояния глаза
                        if eye_state == 0 and confidence >= 0.62:  # Закрытые глаза
                            color = (0, 0, 255)  # Красный
                            drowsiness_detected = True
                        elif eye_state == 1 and confidence >= 0.66:  # Сонные глаза
                            color = (0, 165, 255)  # Оранжевый
                            drowsiness_detected = True
                        elif eye_state == 2:  # Открытые глаза
                            color = (0, 255, 0)  # Зеленый
                            open_eye_detected = True
                        else:
                            color = (0, 255, 255)  # Желтый: нужна проверка
                        
                        # Рисуем рамку вокруг глаза
                        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                
                # Определяем общий статус
                if len(eyes) == 0:
                    st.session_state.missing_eye_frames = st.session_state.get("missing_eye_frames", 0) + 1
                else:
                    st.session_state.missing_eye_frames = 0

                eyes_missing = len(eyes) == 0
                eyes_missing_too_long = st.session_state.get("missing_eye_frames", 0) >= 8
                eyes_closed_now = drowsiness_detected or eyes_missing
                if drowsiness_detected or eyes_missing_too_long:
                    status = "Спит"
                    status_color = (0, 0, 255)  # Красный
                elif eyes_missing:
                    status = "Ищу глаза"
                    status_color = (0, 255, 255)  # Желтый
                elif open_eye_detected or classified_eyes > 0:
                    status = "Не Спит"
                    status_color = (0, 255, 0)  # Зеленый
                else:
                    status = "Ищу глаза"
                    status_color = (0, 255, 255)  # Желтый

                now = time.monotonic()
                if eyes_closed_now:
                    if st.session_state.get("eye_closed_since") is None:
                        st.session_state.eye_closed_since = now
                    closed_seconds = now - st.session_state.eye_closed_since
                else:
                    st.session_state.eye_closed_since = None
                    st.session_state.warning_sent = False
                    st.session_state.alarm_sent = False
                    st.session_state.last_warning_at = 0.0
                    st.session_state.last_alarm_at = 0.0
                    closed_seconds = 0.0
                    alert_placeholder.markdown(
                        '<div class="ready-strip">Глаза открыты. Система наблюдения активна.</div>',
                        unsafe_allow_html=True,
                    )

                if eyes_closed_now and closed_seconds < 3:
                    alert_placeholder.markdown(
                        f'<div class="ready-strip">Глаза закрыты {closed_seconds:.1f} c. Предупреждение сработает на 3 c.</div>',
                        unsafe_allow_html=True,
                    )

                warning_due = (
                    closed_seconds >= 3
                    and now - st.session_state.get("last_warning_at", 0.0) >= 5
                )
                if warning_due:
                    st.session_state.warning_sent = True
                    st.session_state.last_warning_at = now
                    alert_placeholder.markdown(
                        '<div class="alert-strip">Внимание: глаза закрыты уже 3 секунды. Откройте глаза или остановитесь для отдыха.</div>',
                        unsafe_allow_html=True,
                    )
                    with notification_placeholder:
                        trigger_browser_notification(
                            "Eyes on Road",
                            "Глаза закрыты 3 секунды. Пожалуйста, проверьте состояние водителя.",
                            str(int(now * 1000)),
                        )

                alarm_due = (
                    closed_seconds >= 5
                    and now - st.session_state.get("last_alarm_at", 0.0) >= 5
                )
                if alarm_due:
                    st.session_state.alarm_sent = True
                    st.session_state.last_alarm_at = now
                    alert_placeholder.markdown(
                        '<div class="alert-strip">Критично: глаза закрыты 5 секунд. Звуковое оповещение повторяется каждые 5 секунд.</div>',
                        unsafe_allow_html=True,
                    )
                    with alarm_placeholder:
                        trigger_audio_alarm(str(int(now * 1000)))
                
                # Вычисляем среднюю уверенность
                avg_confidence = total_confidence / max(classified_eyes, 1)
                
                # Обновляем статус в session_state для отображения в боковой панели
                st.session_state.current_status = status
                st.session_state.current_confidence = avg_confidence
                st.session_state.eyes_detected = len(eyes)
                st.session_state.closed_seconds = closed_seconds
                
                # Добавляем информацию на кадр (с поддержкой кириллицы через PIL)
                def draw_text_pil_bgr(bgr_image: np.ndarray, text: str, position: tuple, 
                                      font_size: int = 24, text_color=(255, 255, 255)) -> np.ndarray:
                    # Конвертируем BGR -> RGB для PIL
                    rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(rgb_image)
                    draw = ImageDraw.Draw(pil_img)
                    # Пытаемся найти шрифт с поддержкой кириллицы (Windows)
                    font_paths = [
                        "C:/Windows/Fonts/arial.ttf",
                        "C:/Windows/Fonts/segoeui.ttf",
                        "C:/Windows/Fonts/tahoma.ttf",
                    ]
                    font = None
                    for p in font_paths:
                        try:
                            font = ImageFont.truetype(p, font_size)
                            break
                        except Exception:
                            continue
                    if font is None:
                        # Фолбэк на стандартный шрифт (может не отрисовать кириллицу, но не упадём)
                        font = ImageFont.load_default()
                    draw.text(position, text, font=font, fill=tuple(int(c) for c in text_color))
                    # Обратно RGB -> BGR
                    result = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                    return result

                # Текст слева сверху
                info_overlay = frame.copy()
                cv2.rectangle(info_overlay, (8, 8), (330, 112), (0, 0, 0), -1)
                frame = cv2.addWeighted(info_overlay, 0.42, frame, 0.58, 0)
                frame = draw_text_pil_bgr(frame, f"Глаз в кадре: {len(eyes)}", (18, 16), 23, (255, 255, 255))
                frame = draw_text_pil_bgr(frame, f"Состояние: {status}", (18, 48), 23, status_color)
                frame = draw_text_pil_bgr(frame, f"Таймер: {closed_seconds:.1f} c", (18, 80), 23, status_color)

                # Бейдж статуса в правом верхнем углу
                h, w = frame.shape[:2]
                badge_text = f"{status}"
                # Рисуем полупрозрачный фон под бейдж
                overlay = frame.copy()
                badge_w, badge_h = 210, 40
                x1, y1 = w - badge_w - 10, 10
                x2, y2 = w - 10, 10 + badge_h
                bg_color = (0, 0, 0)
                cv2.rectangle(overlay, (x1, y1), (x2, y2), bg_color, -1)
                alpha = 0.35
                frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
                # Текст поверх бейджа (через PIL, чтобы не было "????")
                frame = draw_text_pil_bgr(frame, badge_text, (x1 + 10, y1 + 8), 24, status_color)
                
                # Конвертируем BGR в RGB для Streamlit
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Отображаем кадр
                video_placeholder.image(frame_rgb, channels="RGB", width=640)
                
                # Небольшая задержка для плавности
                time.sleep(0.1)
            
            # Освобождаем камеру
            cap.release()
        else:
            st.info("Нажмите «Старт», чтобы начать детекцию.")
    
    with col2:
        st.subheader("Статус")
        
        # Отображаем текущий статус
        if 'current_status' in st.session_state:
            status = st.session_state.current_status
            
            if status == "Спит":
                st.error(f"**{status}**")
                st.markdown("**Внимание: обнаружена сонливость.**")
            elif status == "Не Спит":
                st.success(f"**{status}**")
                st.markdown("**Водитель бодрствует.**")
            else:
                st.info(f"**{status}**")
                st.markdown("**Посмотрите прямо в камеру, чтобы система увидела глаза.**")
            
            # Дополнительная информация
            if 'current_confidence' in st.session_state:
                confidence = st.session_state.current_confidence
                st.metric("Уверенность", f"{confidence:.2f}")
            
            if 'eyes_detected' in st.session_state:
                eyes_count = st.session_state.eyes_detected
                st.metric("Глаз в кадре", eyes_count)

            if 'closed_seconds' in st.session_state:
                st.metric("Таймер закрытия", f"{st.session_state.closed_seconds:.1f} c")
        else:
            st.info("Запустите камеру, чтобы увидеть статус.")
        
        # Информация о ближайшей остановке
        st.markdown("---")
        st.markdown("### Остановка для отдыха")
        
        if 'nearest_stop' in st.session_state:
            stop = st.session_state.nearest_stop
            st.success(f"**{stop['name']}**")
            st.metric("Расстояние", f"{stop['distance_km']} км")
            _svc = stop.get("services") or []
            st.markdown(f"**Услуги:** {', '.join(_svc) if _svc else '—'}")
            
            # Рекомендация по отдыху
            if 'current_status' in st.session_state and st.session_state.current_status == "Спит":
                if stop['distance_km'] <= 20:
                    st.warning("**Рекомендуется немедленный отдых.** Близкая остановка найдена.")
                else:
                    st.error("**Критично.** Нужен отдых, но ближайшая остановка далеко.")
            else:
                if stop['distance_km'] <= 30:
                    st.info("**Близкая остановка.** Можно планировать отдых.")
                else:
                    st.info("**Дальняя остановка.** Продолжайте движение внимательно.")
        else:
            st.info("Выберите маршрут и найдите ближайшую остановку справа.")
        
        # Инструкции
        st.markdown("---")
        st.markdown("### Как проверить")
        st.markdown("""
        1. Нажмите **Старт**.
        2. Смотрите прямо в камеру.
        3. Закройте глаза и держите их закрытыми.
        4. На 3 секунде появится предупреждение.
        5. На 5 секунде включится звук.
        """)
        
        # Статистика
        st.markdown("---")
        st.markdown("### Модель")
        st.write(f"**Классы:** {len(class_mapping)}")
        for name, class_id in class_mapping.items():
            st.write(f"- {name} (ID: {class_id})")
    
    with col3:
        st.subheader("Маршрут")
        
        if bus_stops_data:
            # Выбор маршрута
            sorted_routes = sorted(
                bus_stops_data['routes'].items(),
                key=lambda item: 0 if item[0] == "oral-aktobe" else 1,
            )
            route_options = {
                route_data['name']: route_id
                for route_id, route_data in sorted_routes
            }
            
            selected_route_name = st.selectbox(
                "Маршрут",
                options=list(route_options.keys()),
                index=0
            )
            
            selected_route_id = route_options[selected_route_name]

            if "user_gps_lat" not in st.session_state:
                st.session_state.user_gps_lat = None
                st.session_state.user_gps_lon = None
            if "pending_geolocation" not in st.session_state:
                st.session_state.pending_geolocation = False
            if "geo_nonce" not in st.session_state:
                st.session_state.geo_nonce = 0
            if "map_manual_lat" not in st.session_state:
                st.session_state.map_manual_lat = None
                st.session_state.map_manual_lon = None

            # Геолокация: в браузере нажмите «Разрешить» в системном запросе. Нужен безопасный контекст
            # (https:// или http://localhost при streamlit run); обычный http по IP/домену без TLS может быть заблокирован.

            if st.button("Получить GPS", use_container_width=True):
                st.session_state.pending_geolocation = True
                st.session_state.geo_nonce += 1
                st.info("Разрешите доступ к геолокации в браузере (значок замка / запрос у адресной строки).")

            if st.session_state.pending_geolocation:
                st.caption("Запрос координат у браузера…")
                raw_geo = get_geolocation(component_key=f"geo_{st.session_state.geo_nonce}")
                loc = _unwrap_streamlit_js_eval_payload(raw_geo)
                if loc is not None:
                    st.session_state.pending_geolocation = False
                    if isinstance(loc, dict) and loc.get("error"):
                        err = loc["error"]
                        msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
                        st.warning(f"Геолокация недоступна: {msg}")
                    else:
                        coords = loc.get("coords") or {}
                        lat, lon = coords.get("latitude"), coords.get("longitude")
                        if lat is not None and lon is not None:
                            st.session_state.user_gps_lat = float(lat)
                            st.session_state.user_gps_lon = float(lon)
                            st.success("Координаты получены с GPS.")
                        else:
                            st.warning("Браузер не вернул координаты.")
            
            # Ручной ввод координат (для тестирования)
            st.markdown("**Координаты вручную**")
            col_lat, col_lon = st.columns(2)
            
            with col_lat:
                user_lat = st.number_input(
                    "Широта",
                    value=43.2220,  # Алматы
                    min_value=-90.0,
                    max_value=90.0,
                    step=0.001,
                    format="%.3f"
                )
            
            with col_lon:
                user_lon = st.number_input(
                    "Долгота",
                    value=76.8512,  # Алматы
                    min_value=-180.0,
                    max_value=180.0,
                    step=0.001,
                    format="%.3f"
                )
            
            # Поиск ближайшей остановки
            if st.button("Найти остановку", type="primary", use_container_width=True):
                st.session_state.map_manual_lat = float(user_lat)
                st.session_state.map_manual_lon = float(user_lon)
                nearest_stop = find_nearest_stop(user_lat, user_lon, selected_route_id, bus_stops_data)
                
                if nearest_stop:
                    st.success("Остановка найдена.")
                    
                    st.markdown(f"**{nearest_stop['name']}**")
                    st.markdown(f"**Расстояние:** {nearest_stop['distance_km']} км")
                    st.markdown(f"**Описание:** {nearest_stop.get('description', '—')}")
                    
                    # Услуги
                    _ns = nearest_stop.get("services") or []
                    services_text = ", ".join(_ns)
                    st.markdown(f"**Услуги:** {services_text if services_text else '—'}")
                    
                    # Цветовая индикация расстояния
                    if nearest_stop['distance_km'] <= 10:
                        st.success("Близко. Подходит для отдыха.")
                    elif nearest_stop['distance_km'] <= 50:
                        st.warning("Умеренное расстояние.")
                    else:
                        st.info("Остановка далеко.")
                    
                    # Сохраняем в session_state для отображения в основной панели
                    st.session_state.nearest_stop = nearest_stop
                else:
                    st.error("Не удалось найти остановку.")

            st.markdown("---")
            st.markdown("### Карта маршрута")
            st.caption(
                "Синий маркер — ваше положение. Оранжевые маркеры — точки для отдыха на выбранном маршруте."
            )
            u_lat, u_lon = None, None
            if st.session_state.user_gps_lat is not None and st.session_state.user_gps_lon is not None:
                u_lat = st.session_state.user_gps_lat
                u_lon = st.session_state.user_gps_lon
            elif st.session_state.map_manual_lat is not None:
                u_lat = st.session_state.map_manual_lat
                u_lon = st.session_state.map_manual_lon

            deck = build_route_map_deck(bus_stops_data, selected_route_id, u_lat, u_lon)
            if deck is not None:
                st.pydeck_chart(deck, height=520, use_container_width=True)
            else:
                st.info("Нет данных для карты.")
        else:
            st.error("Данные остановок не загружены.")

if __name__ == "__main__":
    main()
