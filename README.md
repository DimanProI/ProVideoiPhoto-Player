# ProVideoiPhoto Player

[Русский](#russian) | [English](#english)

<a name="russian"></a>
## 🇷🇺 Описание
**ProVideoiPhoto Player** — это профессиональное приложение для управления презентацией медиа-контента (фото и видео) на втором экране. Программа разработана для использования на мероприятиях, конференциях и шоу, где требуется надежное воспроизведение контента в высоком разрешении с возможностью предварительного просмотра и управления с основного экрана оператора.

### Основные возможности
*   **Двухэкранный режим**: Панель управления на основном мониторе и полноэкранный вывод на втором (проектор, LED-экран).
*   **Поддержка форматов**: Воспроизведение популярных видео (MP4, MOV, MKV) и изображений (JPG, PNG).
*   **Профессиональный плеер**: Основан на мощном движке **libmpv**, обеспечивающем высокую производительность и аппаратное ускорение.
*   **Управление плейлистом**: Добавление файлов через Drag & Drop, навигация по списку.
*   **Инструменты презентации**:
    *   Функция "Black Screen" (черный экран) для мгновенного скрытия контента.
    *   Встроенный таймер для отслеживания времени выступления.
    *   Предпросмотр контента в интерфейсе оператора.
*   **Горячие клавиши**: Настраиваемое управление с клавиатуры (F1 для справки).

### Технологический стек
Приложение создано с использованием современных технологий:
*   **Язык**: Python 3.13+
*   **Интерфейс**: PyQt6 (Qt Framework)
*   **Медиа-движок**: LibMPV (через python-mpv)

### Установка и запуск

#### Вариант 1: Готовый EXE (Рекомендуется для пользователей)
1.  Перейдите в раздел [Releases](https://github.com/DimanProI/ProVideoiPhoto-Player/releases).
2.  Скачайте архив с последней версией для вашей ОС (например, `ProVideoiPhoto_Player_Clean_v2.zip`).
3.  Распакуйте архив в удобное место.
4.  Запустите файл `ProVideoiPhoto.exe`.
    *   *Примечание: Все необходимые библиотеки (включая libmpv) уже встроены.*

#### Вариант 2: Запуск из исходного кода (Для разработчиков)
1.  Установите Python 3.13+.
2.  Установите зависимости: `pip install -r requirements.txt`
3.  Убедитесь, что библиотека `libmpv-2.dll` (или `libmpv.so` для Linux) доступна.
4.  Запустите приложение: `python -m src.main`

---
*Продукт был создан Дмитрием Сальниковым для открытого распространения, все права защищены.*

---
---

<a name="english"></a>
## 🇺🇸 Description
**ProVideoiPhoto Player** is a professional application for managing media content presentation (photos and videos) on a secondary screen. The program is designed for events, conferences, and shows where reliable high-resolution playback is required, along with preview capabilities and control from the operator's main screen.

### Key Features
*   **Dual Screen Mode**: Control panel on the primary monitor and full-screen output on the secondary one (projector, LED screen).
*   **Format Support**: Playback of popular video formats (MP4, MOV, MKV) and images (JPG, PNG).
*   **Professional Player**: Powered by the robust **libmpv** engine, ensuring high performance and hardware acceleration.
*   **Playlist Management**: Drag & Drop file addition, list navigation.
*   **Presentation Tools**:
    *   "Black Screen" function to instantly hide content.
    *   Built-in timer to track presentation time.
    *   Content preview in the operator interface.
*   **Hotkeys**: Configurable keyboard controls (F1 for help).

### Tech Stack
The application is built using modern technologies:
*   **Language**: Python 3.13+
*   **Interface**: PyQt6 (Qt Framework)
*   **Media Engine**: LibMPV (via python-mpv)

### Installation and Usage

#### Option 1: Pre-built EXE (Recommended for Users)
1.  Go to the [Releases](https://github.com/DimanProI/ProVideoiPhoto-Player/releases) section.
2.  Download the archive with the latest version (e.g., `ProVideoiPhoto_Player_Clean_v2.zip`).
3.  Unzip the archive.
4.  Run `ProVideoiPhoto.exe`.
    *   *Note: All dependencies (including libmpv) are already bundled.*

#### Option 2: Running from Source (For Developers)
1.  Install Python 3.13+.
2.  Install dependencies: `pip install -r requirements.txt`
3.  Ensure the `libmpv-2.dll` library (or `libmpv.so` for Linux) is available.
4.  Run the application: `python -m src.main`

---
*Product created by Dmitry Salnikov for open distribution, all rights reserved.*
