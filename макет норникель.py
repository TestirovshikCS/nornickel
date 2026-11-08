# ================================================================
# ЦИФРОВОЙ ДВОЙНИК ПЛАНЕТАРНОГО РЕДУКТОРА ПРИВОДА МПС
# Демонстрационный проект: Python + Streamlit + Plotly
#
# Авторская учебная модель для демонстрации:
# - кинематики планетарной передачи;
# - вращения солнечной шестерни и сателлитов;
# - изменения нагрузки и температуры;
# - моделирования повреждения зуба;
# - оценки технического состояния оборудования.
#
# ВНИМАНИЕ: геометрия и диагностические пороги условные.
# Это не модель конкретного редуктора промышленного предприятия.
# ================================================================

import numpy as np # type: ignore
import streamlit as st # type: ignore
import plotly.graph_objects as go # type: ignore

# -------------------- НАСТРОЙКИ --------------------

st.set_page_config(
    page_title="Цифровой двойник редуктора МПС",
    page_icon="⚙️",
    layout="wide"
)

# Параметры зубчатой передачи
Z_SUN = 24
Z_PLANET = 24
Z_RING = 72

MODULE = 0.10

R_SUN = MODULE * Z_SUN / 2
R_PLANET = MODULE * Z_PLANET / 2
R_RING = MODULE * Z_RING / 2

PLANET_DISTANCE = R_SUN + R_PLANET

PLANET_COUNT = 3

# Условные диагностические пределы
TEMP_WARNING = 75.0
TEMP_CRITICAL = 85.0

LOAD_WARNING = 80.0
LOAD_CRITICAL = 90.0

WEAR_WARNING = 25.0
WEAR_CRITICAL = 50.0


# -------------------- ЗАГОЛОВОК --------------------

st.title("⚙️ Цифровой двойник планетарного редуктора МПС")

st.markdown(
    """
    Демонстрационная система инженерной визуализации и диагностики ТОиР

    Модель показывает устройство планетарной передачи,
    кинематику вращения, влияние нагрузки, перегрева и
    повреждения зубчатого зацепления.
    """
)

st.divider()


# -------------------- ПАНЕЛЬ УПРАВЛЕНИЯ --------------------

st.sidebar.title("Панель управления")

st.sidebar.subheader("1. Режим работы")

rpm = st.sidebar.slider(
    "Частота вращения входного вала, RPM",
    min_value=100,
    max_value=1500,
    value=600,
    step=50
)

load = st.sidebar.slider(
    "Нагрузка, %",
    min_value=0,
    max_value=120,
    value=65,
    step=5
)

temperature = st.sidebar.slider(
    "Температура подшипника, °C",
    min_value=20,
    max_value=120,
    value=65,
    step=1
)

st.sidebar.divider()

st.sidebar.subheader("2. Режим износа")

damage_enabled = st.sidebar.checkbox(
    "Активировать повреждение зуба",
    value=False
)

if damage_enabled:
    wear = st.sidebar.slider(
        "Степень повреждения зуба, %",
        min_value=0,
        max_value=100,
        value=65,
        step=5
    )
else:
    wear = 0

st.sidebar.divider()

st.sidebar.subheader("3. Анимация")

animation_speed = st.sidebar.select_slider(
    "Скорость анимации",
    options=["Медленно", "Нормально", "Быстро"],
    value="Нормально"
)

animation_duration = {
    "Медленно": 350,
    "Нормально": 150,
    "Быстро": 60
}[animation_speed]


# -------------------- КИНЕМАТИКА --------------------

# Неподвижный внутренний венец:
# n_carrier = n_sun * Z_sun / (Z_sun + Z_ring)

carrier_rpm = rpm * Z_SUN / (Z_SUN + Z_RING)

# Скорость вращения сателлита относительно корпуса.
# Для данной схемы она равна -0.5 скорости солнечной шестерни.

planet_rpm = -0.5 * rpm

# Передаточное отношение

transmission_ratio = rpm / carrier_rpm

# Условный входной крутящий момент.
# Это демонстрационная зависимость, а не паспортная характеристика.

input_torque = 100000 * load / 100

# Выходной момент без учета потерь

output_torque = input_torque * transmission_ratio


# -------------------- ГЕОМЕТРИЯ ШЕСТЕРЕН --------------------

def create_gear_geometry(radius, teeth, damage=0):
    """
    Создает приближенную 3D-геометрию зубчатого колеса.

    Зубья представлены упрощенным профильным контуром.
    Это визуальная аппроксимация, а не эвольвентный профиль.
    """

    points_per_tooth = 8

    count = teeth * points_per_tooth

    angles = np.linspace(
        0,
        2 * np.pi,
        count,
        endpoint=False
    )

    # Упрощенный профиль зуба
    profile = np.array([
        0.94, 0.94, 0.94, 1.06,
        1.06, 1.06, 0.94, 0.94
    ])

    radial_profile = np.tile(profile, teeth)
    radii = radius * radial_profile

    # Искусственное повреждение одного зуба.
    # Радиальное уменьшение используется только
    # для демонстрации видимого дефекта.

    if damage > 0:
        damaged_tooth = 0

        start = damaged_tooth * points_per_tooth
        end = start + points_per_tooth

        severity = damage / 100

        radii[start:end] *= (1 - 0.65 * severity)

    x = radii * np.cos(angles)
    y = radii * np.sin(angles)

    z_top = np.full(count, 0.35)
    z_bottom = np.full(count, -0.35)

    vertices = np.column_stack([
        np.concatenate([x, x, [0], [0]]),
        np.concatenate([y, y, [0], [0]]),
        np.concatenate([z_top, z_bottom, [0.35], [-0.35]])
    ])

    top_center = 2 * count
    bottom_center = 2 * count + 1

    i, j, k = [], [], []

    for p in range(count):
        q = (p + 1) % count

        # Верхняя поверхность
        i.append(top_center)
        j.append(p)
        k.append(q)

        # Нижняя поверхность
        i.append(bottom_center)
        j.append(count + q)
        k.append(count + p)

        # Боковые стенки
        i.extend([p, q])
        j.extend([count + p, count + q])
        k.extend([q, p])

        i.extend([q, q])
        j.extend([count + p, count + p])
        k.extend([count + q, count + q])

    return vertices, i, j, k


def rotate_vertices(vertices, angle, offset_x=0, offset_y=0):
    """Поворачивает геометрию вокруг оси Z."""

    c = np.cos(angle)
    s = np.sin(angle)

    x = vertices[:, 0] * c - vertices[:, 1] * s
    y = vertices[:, 0] * s + vertices[:, 1] * c

    return (
        x + offset_x,
        y + offset_y,
        vertices[:, 2]
    )


def make_gear_trace(
    geometry,
    angle,
    offset_x,
    offset_y,
    color,
    name
):
    """Создает 3D-объект зубчатого колеса."""

    vertices, i, j, k = geometry

    x, y, z = rotate_vertices(
        vertices,
        angle,
        offset_x,
        offset_y
    )

    return go.Mesh3d(
        x=x,
        y=y,
        z=z,
        i=i,
        j=j,
        k=k,
        color=color,
        opacity=0.98,
        flatshading=True,
        name=name,
        hovertemplate=name + "<extra></extra>"
    )


# -------------------- ВНУТРЕННИЙ ВЕНЕЦ --------------------

def create_ring_geometry():
    """
    Создает условный внешний корпус венца.
    Внутренние зубья не являются точной эвольвентной геометрией.
    """

    count = 120

    angles = np.linspace(
        0,
        2 * np.pi,
        count,
        endpoint=False
    )

    outer_radius = R_RING * 1.23

    x = outer_radius * np.cos(angles)
    y = outer_radius * np.sin(angles)

    z1 = np.full(count, 0.4)
    z2 = np.full(count, -0.4)

    vertices = np.column_stack([
        np.concatenate([x, x]),
        np.concatenate([y, y]),
        np.concatenate([z1, z2])
    ])

    i, j, k = [], [], []

    for p in range(count):
        q = (p + 1) % count

        i.extend([p, p])
        j.extend([q, count + p])
        k.extend([count + q, count + q])

    return vertices, i, j, k


# -------------------- ГЕОМЕТРИЯ МОДЕЛИ --------------------

sun_geometry = create_gear_geometry(
    R_SUN,
    Z_SUN,
    wear
)

planet_geometry = create_gear_geometry(
    R_PLANET,
    Z_PLANET
)

ring_geometry = create_ring_geometry()


# -------------------- ЦВЕТОВАЯ ДИАГНОСТИКА --------------------

if temperature >= TEMP_CRITICAL:
    bearing_color = "red"
elif temperature >= TEMP_WARNING:
    bearing_color = "orange"
else:
    bearing_color = "royalblue"

if wear >= WEAR_CRITICAL:
    gear_color = "red"
elif wear >= WEAR_WARNING:
    gear_color = "orange"
else:
    gear_color = "goldenrod"


# -------------------- ПОСТРОЕНИЕ 3D-МОДЕЛИ --------------------

def create_3d_model():

    fig = go.Figure()

    # Начальная фаза вращения
    sun_angle = 0

    carrier_angle = 0

    planet_angles = [
        0,
        2 * np.pi / 3,
        4 * np.pi / 3
    ]

    # 0. Солнечная шестерня
    fig.add_trace(
        make_gear_trace(
            sun_geometry,
            sun_angle,
            0,
            0,
            gear_color,
            "Солнечная шестерня"
        )
    )

    # 1-3. Сателлиты

    for index, position in enumerate(planet_angles):

        px = PLANET_DISTANCE * np.cos(position)
        py = PLANET_DISTANCE * np.sin(position)

        fig.add_trace(
            make_gear_trace(
                planet_geometry,
                0,
                px,
                py,
                "darkcyan",
                f"Сателлит №{index + 1}"
            )
        )

    # 4. Внутренний венец

    vertices, i, j, k = ring_geometry

    fig.add_trace(
        go.Mesh3d(
            x=vertices[:, 0],
            y=vertices[:, 1],
            z=vertices[:, 2],
            i=i,
            j=j,
            k=k,
            color="gray",
            opacity=0.25,
            name="Корпус внутреннего венца"
        )
    )

    # 5. Водило: три соединительных плеча

    carrier_x = []
    carrier_y = []
    carrier_z = []

    for position in planet_angles:

        px = PLANET_DISTANCE * np.cos(position)
        py = PLANET_DISTANCE * np.sin(position)

        carrier_x.extend([0, px, None])
        carrier_y.extend([0, py, None])
        carrier_z.extend([0.48, 0.48, None])

    fig.add_trace(
        go.Scatter3d(
            x=carrier_x,
            y=carrier_y,
            z=carrier_z,
            mode="lines",
            line=dict(
                color="silver",
                width=10
            ),
            name="Водило"
        )
    )

    # 6. Условное обозначение подшипникового узла

    fig.add_trace(
        go.Scatter3d(
            x=[0],
            y=[0],
            z=[0.65],
            mode="markers",
            marker=dict(
                size=10,
                color=bearing_color,
                line=dict(color="white", width=2)
            ),
            name="Контроль температуры"
        )
    )

    # 7. Центральная ось

    fig.add_trace(
        go.Scatter3d(
            x=[0, 0],
            y=[0, 0],
            z=[-0.8, 0.8],
            mode="lines",
            line=dict(
                color="white",
                width=5
            ),
            name="Входной вал"
        )
    )

    # -------------------- АНИМАЦИЯ --------------------

    frames = []

    frame_count = 24

    for frame_number in range(frame_count):

        # Полный оборот солнечной шестерни

        sun_phase = (
            2 * np.pi * frame_number / frame_count
        )

        # Формула Уиллиса для неподвижного венца

        carrier_phase = (
            sun_phase * Z_SUN / (Z_SUN + Z_RING)
        )

        # Абсолютная скорость сателлита:
        # omega_planet = -0.5 * omega_sun

        planet_spin = -0.5 * sun_phase

        frame_data = []

        # Солнечная шестерня

        vertices, i, j, k = sun_geometry

        x, y, z = rotate_vertices(
            vertices,
            sun_phase
        )

        frame_data.append(
            go.Mesh3d(
                x=x, y=y, z=z,
                i=i, j=j, k=k,
                color=gear_color,
                opacity=0.98,
                flatshading=True,
                name="Солнечная шестерня"
            )
        )

        # Сателлиты

        carrier_positions = [
            0,
            2 * np.pi / 3,
            4 * np.pi / 3
        ]

        for position in carrier_positions:

            orbital_angle = position + carrier_phase

            px = PLANET_DISTANCE * np.cos(orbital_angle)
            py = PLANET_DISTANCE * np.sin(orbital_angle)

            planet_data = make_gear_trace(
                planet_geometry,
                planet_spin,
                px,
                py,
                "darkcyan",
                "Сателлит"
            )

            frame_data.append(planet_data)

        # Водило

        arm_x = []
        arm_y = []
        arm_z = []

        for position in carrier_positions:

            orbital_angle = position + carrier_phase
            px = PLANET_DISTANCE * np.cos(orbital_angle)
            py = PLANET_DISTANCE * np.sin(orbital_angle)

            arm_x.extend([0, px, None])
            arm_y.extend([0, py, None])
            arm_z.extend([0.48, 0.48, None])

        frame_data.append(
            go.Scatter3d(
                x=arm_x,
                y=arm_y,
                z=arm_z,
                mode="lines",
                line=dict(color="silver", width=10),
                name="Водило"
            )
        )

        frames.append(
            go.Frame(
                data=frame_data,
                traces=[0, 1, 2, 3, 5],
                name=str(frame_number)
            )
        )

    fig.frames = frames

    # -------------------- ВИД СЦЕНЫ --------------------

    fig.update_layout(
        title="3D-модель редуктора",
        width=500,        # Жесткая базовая ширина
        height=500,       # Жесткая базовая высота (делаем квадрат, чтобы не сплющивало)
        autosize=True,
        template="plotly_dark",
        margin=dict(l=10, r=10, b=10, t=50), # Небольшие отступы
        scene=dict(
            xaxis=dict(title="X", showbackground=True, backgroundcolor="#151b26"),
            yaxis=dict(title="Y", showbackground=True, backgroundcolor="#151b26"),
            zaxis=dict(title="Z", showbackground=True, backgroundcolor="#151b26"),
            aspectmode="cube", # Заставляем оси быть одинакового размера (куб), чтобы модель не вытягивало
            camera=dict(
                eye=dict(x=2.0, y=2.0, z=1.5), # Отодвинули камеру еще дальше, чтобы модель точно влезла
                up=dict(x=0, y=0, z=1)
            )
        ),
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                x=0.0,
                y=1.15,
                buttons=[
                    dict(
                        label="▶ ЗАПУСТИТЬ",
                        method="animate",
                        args=[None, {"frame": {"duration": animation_duration, "redraw": True}, "fromcurrent": True}]
                    ),
                    dict(
                        label="⏸ ПАУЗА",
                        method="animate",
                        args=[[None], {"mode": "immediate", "frame": {"duration": 0, "redraw": False}}]
                    )
                ]
            )
        ]
    )


# -------------------- ДИАГНОСТИКА --------------------

# Условный интегральный показатель риска.
# Он предназначен исключительно для демонстрации логики
# предиктивной аналитики, а не для принятия решений о ремонте.

temperature_score = np.clip(
    (temperature - 50) / 40 * 100,
    0,
    100
)

load_score = np.clip(
    load / 100 * 100,
    0,
    100
)

wear_score = wear

risk_score = (
    0.35 * temperature_score
    + 0.30 * load_score
    + 0.35 * wear_score
)

critical_state = (
    temperature >= TEMP_CRITICAL
    or load >= LOAD_CRITICAL
    or wear >= WEAR_CRITICAL
)

warning_state = (
    temperature >= TEMP_WARNING
    or load >= LOAD_WARNING
    or wear >= WEAR_WARNING
)

# -------------------- ВЫВОД ДАННЫХ --------------------

st.subheader("📊 Основные параметры оборудования")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Входная скорость",
    f"{rpm} RPM"
)
col2.metric(
    "Скорость водила",
    f"{carrier_rpm:.1f} RPM"
)

col3.metric(
    "Температура",
    f"{temperature} °C"
)

col4.metric(
    "Нагрузка",
    f"{load}%"
)

st.divider()

# -------------------- 3D-МОДЕЛЬ --------------------

st.subheader("🧩 Интерактивная 3D-визуализация")

fig = create_3d_model()

st.plotly_chart(
    fig,
    use_container_width=True,
    key="planetary_gearbox_3d"
)

st.caption(
    "Используйте мышь или касание для вращения камеры, "
    "масштабирования и исследования конструкции. "
    "Кнопка запуска включает анимацию механизма."
)

st.divider()

# -------------------- ТОиР --------------------

st.subheader("🔧 Диагностика технического состояния")

left, right = st.columns(2)

with left:

    st.markdown("### Состояние узлов")

    if temperature >= TEMP_CRITICAL:
        st.error("🔴 КРИТИЧЕСКАЯ ТЕМПЕРАТУРА ПОДШИПНИКА")
    elif temperature >= TEMP_WARNING:
        st.warning("🟠 Повышенная температура подшипника")
    else:
        st.success("🟢 Температурный режим в пределах модели")

    if load >= LOAD_CRITICAL:
        st.error("🔴 Критическая нагрузка")
    elif load >= LOAD_WARNING:
        st.warning("🟠 Повышенная нагрузка")
    else:
        st.success("🟢 Нагрузка в пределах модели")

    if wear >= WEAR_CRITICAL:
        st.error("🔴 Критическое моделируемое повреждение зуба")
    elif wear >= WEAR_WARNING:
        st.warning("🟠 Обнаружено значительное повреждение")
    elif wear > 0:
        st.info("🔵 Смоделировано начальное повреждение")
    else:
        st.success("🟢 Искусственный дефект не активирован")

with right:

    st.markdown("### Индикатор предиктивной аналитики")

    st.metric(
        "Условный индекс риска",
        f"{risk_score:.1f} / 100"
    )

    st.progress(
        float(risk_score / 100)
    )

    if critical_state:
        st.error(
            "ОПАСНАЯ ЗОНА: модель выявила критическое "
            "отклонение. Требуется инженерная проверка."
        )
    elif warning_state:
        st.warning(
            "ЗОНА ПРЕДУПРЕЖДЕНИЯ: рекомендуется "
            "дополнительный контроль параметров."
        )
    else:
        st.success(
            "НОРМАЛЬНОЕ СОСТОЯНИЕ: критические "
            "отклонения по заданным порогам не выявлены."
        )

st.divider()

# -------------------- ИНЖЕНЕРНЫЕ РАСЧЕТЫ --------------------

st.subheader("📐 Кинематические расчеты")

calculation_col1, calculation_col2 = st.columns(2)

with calculation_col1:

    st.markdown("Параметры зубчатой передачи")

    st.write(f"Солнечная шестерня: {Z_SUN} зубьев")
    st.write(f"Сателлит: {Z_PLANET} зубьев")
    st.write(f"Внутренний венец: {Z_RING} зубьев")

    st.write(f"Модуль модели: {MODULE:.2f} м")

    st.write(
        f"Межосевое расстояние: "
        f"{PLANET_DISTANCE:.2f} м"
    )

    st.write(
        f"Передаточное отношение: "
        f"{transmission_ratio:.2f}"
    )

with calculation_col2:

    st.markdown("Расчетные параметры привода")

    st.write(
        f"Частота вращения входа: {rpm} RPM"
    )

    st.write(
        f"Частота вращения водила: "
        f"{carrier_rpm:.2f} RPM"
    )

    st.write(
        f"Частота вращения сателлита: "
        f"{planet_rpm:.2f} RPM"
    )

    st.write(
        f"Условный входной момент: "
        f"{input_torque:.0f} Н·м"
    )

    st.write(
        f"Условный выходной момент без потерь: "
        f"{output_torque:.0f} Н·м"
    )

st.divider()

# -------------------- ЗАКЛЮЧЕНИЕ --------------------

st.subheader("📋 Инженерное заключение")

if critical_state:

    st.error(
        f"""
        МОДЕЛЬ ОБНАРУЖИЛА КРИТИЧЕСКОЕ ОТКЛОНЕНИЕ

        Необходимо проверить исходные данные, состояние
        подшипников, режим нагрузки и качество зубчатого
        зацепления. Это демонстрационный сигнал, а не
        автоматическое предписание остановки
        """
    )
