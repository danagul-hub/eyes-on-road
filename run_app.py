"""
Скрипт для запуска Streamlit приложения детекции сонливости.
"""

import subprocess
import sys
import os

def check_dependencies():
    """Проверяет наличие необходимых зависимостей"""
    try:
        import streamlit
        import cv2
        import numpy
        import sklearn
        import joblib
        import pydeck
        import streamlit_js_eval
        print("✅ Все зависимости установлены")
        return True
    except ImportError as e:
        print(f"❌ Отсутствует зависимость: {e}")
        return False

def check_model_files():
    """Проверяет наличие файлов модели"""
    required_files = ['eye_classifier.pkl', 'class_mapping.pkl', 'lol.xml', 'bus_stops.json']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    scaler_files = ['eye_scaler.pkl', 'eye_scaler_fast.pkl', 'eye_scaler_universal.pkl']
    if not any(os.path.exists(file) for file in scaler_files):
        missing_files.append('eye_scaler.pkl или eye_scaler_fast.pkl')
    
    if missing_files:
        print(f"❌ Отсутствуют файлы модели: {missing_files}")
        print("Сначала запустите обучение: python train.py")
        return False
    else:
        print("✅ Все файлы модели найдены")
        return True

def main():
    """Основная функция запуска"""
    print("=== ЗАПУСК ПРИЛОЖЕНИЯ ДЕТЕКЦИИ СОНЛИВОСТИ ===")
    
    # Проверяем зависимости
    if not check_dependencies():
        print("\nУстановите зависимости:")
        print("pip install -r requirements.txt")
        return
    
    # Проверяем файлы модели
    if not check_model_files():
        return
    
    print("\n🚀 Запуск Streamlit приложения...")
    print("Приложение будет доступно по адресу: http://localhost:8501")
    print("Нажмите Ctrl+C для остановки")
    
    try:
        # Запускаем Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 Приложение остановлено")

if __name__ == "__main__":
    main()
