import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import io
from itertools import combinations, product

st.set_page_config(page_title="Логистический инструмент", layout="wide")
st.title("📦 Формирование логистической стратегии снабжения")

# ---------------------- ИНИЦИАЛИЗАЦИЯ ДАННЫХ ----------------------
if 'nodes_df' not in st.session_state:
    st.session_state.nodes_df = pd.DataFrame({
        "Узел": ["Коротчаево", "Лабытнанги", "Приобье", "Новый Уренгой"],
        "Расстояние до объекта (км)": [345, 460, 930, 293]
    })

if 'storage_df' not in st.session_state:
    st.session_state.storage_df = pd.DataFrame({
        "Узел": ["Новый Уренгой", "Коротчаево", "Лабытнанги", "Приобье"],
        "Вместимость (м2)": [300000, 350000, 160000, 120000]
    })

if 'delivery_days_df' not in st.session_state:
    st.session_state.delivery_days_df = pd.DataFrame({
        "Вид транспорта": ["река", "авиа", "жд", "авто"],
        "Доступные сутки": [148, 365, 365, 365]
    })

if 'extra_capex_df' not in st.session_state:
    st.session_state.extra_capex_df = pd.DataFrame({
        "Код варианта": ["Коротчаево_авто_50", "Новый Уренгой_авто_50", 
                         "Лабытнанги_река_100", "Приобье_река_100", "жд"],
        "КапКс (млн руб)": [500, 500, 1000, 1000, 16000]
    })

if 'forecast_df' not in st.session_state:
    st.session_state.forecast_df = pd.DataFrame({
        "Год": list(range(2027, 2039)),
        "Инертные (тыс.т)": [30,25,31,84,113,30,45,31,35,34,28,23],
        "Генеральные (тыс.т)": [24,20,26,69,93,24,37,25,28,27,23,19]
    })

if 'warehouse_rates_df' not in st.session_state:
    st.session_state.warehouse_rates_df = pd.DataFrame({
        "Узел": ["Коротчаево","Коротчаево","Новый Уренгой","Новый Уренгой","Приобье","Приобье","Лабытнанги","Лабытнанги"],
        "Группа МТР": ["инертные","Генеральные","инертные","Генеральные","инертные","Генеральные","инертные","Генеральные"],
        "Разгрузка (руб/т)": [965,1393,1019,1017,244,1225,535,1685],
        "Погрузка (руб/т)": [408,484,1019,1016,431,1280,460,1039],
        "Хранение (тыс.руб/т)": [0.11,0.11,0.24,0.24,0.47,0.47,1.12,1.12]
    })

if 'tariff_characteristics_df' not in st.session_state:
    st.session_state.tariff_characteristics_df = pd.DataFrame({
        "Узел": ["Коротчаево","Коротчаево","Новый Уренгой","Новый Уренгой","Приобье","Приобье","Лабытнанги","Лабытнанги"],
        "Группа МТР": ["инертные","Генеральные","инертные","Генеральные","инертные","Генеральные","инертные","Генеральные"],
        "Тариф (руб/маш*час)": [1488,2153,1488,2153,1488,2153,1488,2153],
        "Скорость (км/ч)": [20,20,20,20,20,20,20,20],
        "Грузоподъемность (т)": [13,13,13,13,13,13,13,13]
    })

if 'transport_types_df' not in st.session_state:
    st.session_state.transport_types_df = pd.DataFrame({
        "Вид транспорта": ["авто", "река", "жд", "авиа"],
        "Тариф (ед. изм)": ["руб/ткм", "руб/т", "руб/ваг.км", "руб/час"],
        "Скорость (км/ч)": [40, 15, 50, 83.3],
        "Грузоподъемность (т)": [20, 1000, 1400, 2.2]
    })

if 'transport_rates_by_node' not in st.session_state:
    st.session_state.transport_rates_by_node = pd.DataFrame({
        "Узел": ["Коротчаево", "Новый Уренгой", "Лабытнанги", "Приобье", "Любой", "Любой"],
        "Вид транспорта": ["авто", "авто", "река", "река", "жд", "авиа"],
        "Базовый тариф": [8.5, 9.9, 1160, 2020, 1541.88, 185000]
    })

if 'internal_options_df' not in st.session_state:
    st.session_state.internal_options_df = pd.DataFrame({
        "Плечо (км)": [50, 100],
        "CAPEX доп. (млн руб)": [500, 1000],
        "Тариф инертные (руб/маш*час)": [1488, 1488],
        "Тариф генеральные (руб/маш*час)": [2153, 2153],
        "Грузоподъемность (т)": [20, 20],
        "Скорость (км/ч)": [20, 20]
    })

# Данные для рисков
if 'risks_df' not in st.session_state:
    st.session_state.risks_df = pd.DataFrame({
        "Риск": ["Задержка поставки", "Курсовые колебания"],
        "Ущерб (млн руб)": [100, 50],
        "Вероятность (%)": [20, 30]
    })
if 'consider_risks' not in st.session_state:
    st.session_state.consider_risks = False

if 'uploaded_image' not in st.session_state:
    st.session_state.uploaded_image = None

if 'distribution_method' not in st.session_state:
    st.session_state.distribution_method = "Равномерно"

disc_factors = [0.936585811581694, 0.8215665013874507, 0.7206723696381145,
                0.6321687452965916, 0.5545339871022733, 0.48643332201953804,
                0.42669589650836653, 0.3742946460599707, 0.3283286368947111,
                0.28800757622343076, 0.25263822475739534, 0.2215]

# ---------------------- ФУНКЦИИ РАСЧЁТА ----------------------
def get_transport_rate(node, transport_type):
    rates = st.session_state.transport_rates_by_node
    row = rates[(rates["Узел"] == node) & (rates["Вид транспорта"] == transport_type)]
    if not row.empty:
        return row.iloc[0]["Базовый тариф"]
    row = rates[(rates["Узел"] == "Любой") & (rates["Вид транспорта"] == transport_type)]
    if not row.empty:
        return row.iloc[0]["Базовый тариф"]
    return 0

def calc_transport_cost(transport_row, inert_tonnes, gen_tonnes, distance_km, node, transport_type):
    base_rate = get_transport_rate(node, transport_type)
    unit = transport_row['Тариф (ед. изм)']
    capacity = transport_row['Грузоподъемность (т)']
    speed = transport_row['Скорость (км/ч)']
    
    if unit == 'руб/ткм':
        cost_inert = inert_tonnes * 1000 * base_rate * distance_km / 1e6
        cost_gen = gen_tonnes * 1000 * base_rate * distance_km / 1e6
    elif unit == 'руб/т':
        cost_inert = inert_tonnes * 1000 * base_rate / 1e6
        cost_gen = gen_tonnes * 1000 * base_rate / 1e6
    elif unit == 'руб/ваг.км':
        cost_per_ton_km = base_rate / capacity
        cost_inert = inert_tonnes * 1000 * cost_per_ton_km * distance_km / 1e6
        cost_gen = gen_tonnes * 1000 * cost_per_ton_km * distance_km / 1e6
    elif unit == 'руб/час':
        time_hours = 2 * distance_km / speed
        cost_per_ton = base_rate * time_hours / capacity
        cost_inert = inert_tonnes * 1000 * cost_per_ton / 1e6
        cost_gen = gen_tonnes * 1000 * cost_per_ton / 1e6
    else:
        cost_inert = cost_gen = 0
    return cost_inert, cost_gen

def calc_prr_cost(node, inert_tonnes, gen_tonnes):
    rates = st.session_state.warehouse_rates_df
    inert_row = rates[(rates['Узел'] == node) & (rates['Группа МТР'] == 'инертные')]
    gen_row = rates[(rates['Узел'] == node) & (rates['Группа МТР'] == 'Генеральные')]
    if inert_row.empty or gen_row.empty:
        return 0, 0
    inert = inert_row.iloc[0]
    gen = gen_row.iloc[0]
    cost_inert = inert_tonnes * 1000 * (inert['Разгрузка (руб/т)']*2 + inert['Погрузка (руб/т)']*2 + inert['Хранение (тыс.руб/т)']*1000) / 1e6
    cost_gen = gen_tonnes * 1000 * (gen['Разгрузка (руб/т)']*2 + gen['Погрузка (руб/т)']*2 + gen['Хранение (тыс.руб/т)']*1000) / 1e6
    return cost_inert, cost_gen

def calc_internal_cost(internal_row, inert_tonnes, gen_tonnes, distance_km):
    if internal_row is None:
        return 0, 0
    speed = internal_row['Скорость (км/ч)']
    time_hours = distance_km / speed
    capacity = internal_row['Грузоподъемность (т)']
    inert_rate = internal_row['Тариф инертные (руб/маш*час)']
    gen_rate = internal_row['Тариф генеральные (руб/маш*час)']
    cost_inert = (inert_tonnes * 1000 / capacity) * time_hours * inert_rate / 1e6
    cost_gen = (gen_tonnes * 1000 / capacity) * time_hours * gen_rate / 1e6
    return cost_inert, cost_gen

def get_capex_for_variant(code_name, transport_type):
    extra = st.session_state.extra_capex_df
    if code_name and code_name in extra['Код варианта'].values:
        return extra[extra['Код варианта'] == code_name].iloc[0]['КапКс (млн руб)']
    if transport_type == 'жд':
        rail_match = extra[extra['Код варианта'] == 'жд']
        if not rail_match.empty:
            return rail_match.iloc[0]['КапКс (млн руб)']
    return 0

def compute_option_detailed(nodes_list, transports_list, internal_kms_list, forecast_inert, forecast_gen, disc_factors):
    num_nodes = len(nodes_list)
    forecast_inert_per_node = [x / num_nodes for x in forecast_inert]
    forecast_gen_per_node = [x / num_nodes for x in forecast_gen]
    
    total_disc_cost = 0
    max_vehicles = 0
    yearly_data_all = []
    total_capex = 0
    node_details = []
    
    for idx in range(num_nodes):
        node = nodes_list[idx]
        transport_type = transports_list[idx]
        internal_km = internal_kms_list[idx]
        
        node_row = st.session_state.nodes_df[st.session_state.nodes_df['Узел'] == node].iloc[0]
        dist_to_obj = node_row['Расстояние до объекта (км)']
        transport_row = st.session_state.transport_types_df[st.session_state.transport_types_df['Вид транспорта'] == transport_type].iloc[0]
        available_days = st.session_state.delivery_days_df[st.session_state.delivery_days_df['Вид транспорта'] == transport_type]['Доступные сутки'].values[0]
        transport_row['Доступные сутки'] = available_days
        
        internal_row = None
        if internal_km > 0:
            internal_row = st.session_state.internal_options_df[st.session_state.internal_options_df['Плечо (км)'] == internal_km].iloc[0]
        
        if internal_km == 50:
            capex_code = f"{node}_авто_50"
        elif internal_km == 100:
            capex_code = f"{node}_река_100"
        else:
            capex_code = None
        capex_node = get_capex_for_variant(capex_code, transport_type)
        total_capex += capex_node
        
        # Транспорт – только по базовому расстоянию (без плеча)
        transport_dist = dist_to_obj
        internal_dist = internal_km
        
        speed = transport_row['Скорость (км/ч)']
        capacity = transport_row['Грузоподъемность (т)']
        trips_per_day = 24 / (2 * transport_dist / speed) if speed > 0 else 0
        annual_capacity_per_vehicle = available_days * trips_per_day * capacity
        
        node_details.append({
            "Узел": node,
            "Транспорт": transport_type,
            "Расстояние до объекта (км)": dist_to_obj,
            "Плечо (км)": internal_km,
            "Итоговое расстояние (км)": dist_to_obj + internal_km,
            "Расстояние для расчёта транспорта (км)": transport_dist
        })
        
        for i, (inert, gen) in enumerate(zip(forecast_inert_per_node, forecast_gen_per_node)):
            trans_inert, trans_gen = calc_transport_cost(transport_row, inert, gen, transport_dist, node, transport_type)
            prr_inert, prr_gen = calc_prr_cost(node, inert, gen)
            int_inert, int_gen = calc_internal_cost(internal_row, inert, gen, internal_dist) if internal_dist > 0 else (0,0)
            year_opex = trans_inert + trans_gen + prr_inert + prr_gen + int_inert + int_gen
            disc_opex = year_opex * disc_factors[i]
            total_disc_cost += disc_opex
            yearly_data_all.append({
                "Год": 2027 + i,
                "Узел": node,
                "Транспорт": transport_type,
                "Инертные (тыс.т)": inert,
                "Генеральные (тыс.т)": gen,
                "Транспорт (млн руб)": trans_inert + trans_gen,
                "ПРР (млн руб)": prr_inert + prr_gen,
                "Внутренняя доставка (млн руб)": int_inert + int_gen,
                "Итого OPEX (млн руб)": year_opex,
                "Коэффициент дисконтирования": disc_factors[i],
                "Дисконтированный OPEX (млн руб)": disc_opex
            })
            total_tonnes = (inert + gen) * 1000
            if annual_capacity_per_vehicle > 0 and total_tonnes > 0:
                vehicles = np.ceil(total_tonnes / annual_capacity_per_vehicle)
                if vehicles > max_vehicles:
                    max_vehicles = vehicles
    
    total_capex_disc = total_capex * disc_factors[0]
    total_disc_cost += total_capex_disc
    
    parts = []
    for node, t_type, ikm in zip(nodes_list, transports_list, internal_kms_list):
        if ikm == 50:
            parts.append(f"{node}_{t_type}_50км (авто+ПС)")
        elif ikm == 100:
            parts.append(f"{node}_{t_type}_100км (река+БКЦ)")
        else:
            parts.append(f"{node}_{t_type}")
    code_name = " + ".join(parts)
    
    years = sorted(set(d["Год"] for d in yearly_data_all))
    aggregated = []
    for y in years:
        ydata = [d for d in yearly_data_all if d["Год"] == y]
        aggregated.append({
            "Год": y,
            "Инертные (тыс.т)": sum(d["Инертные (тыс.т)"] for d in ydata),
            "Генеральные (тыс.т)": sum(d["Генеральные (тыс.т)"] for d in ydata),
            "Транспорт (млн руб)": sum(d["Транспорт (млн руб)"] for d in ydata),
            "ПРР (млн руб)": sum(d["ПРР (млн руб)"] for d in ydata),
            "Внутренняя доставка (млн руб)": sum(d["Внутренняя доставка (млн руб)"] for d in ydata),
            "Итого OPEX (млн руб)": sum(d["Итого OPEX (млн руб)"] for d in ydata),
            "Коэффициент дисконтирования": ydata[0]["Коэффициент дисконтирования"],
            "Дисконтированный OPEX (млн руб)": sum(d["Дисконтированный OPEX (млн руб)"] for d in ydata)
        })
    
    return {
        "Код варианта": code_name,
        "Количество узлов": len(nodes_list),
        "Узлы (перечисление)": " + ".join(nodes_list),
        "Транспорт (перечисление)": " + ".join(transports_list),
        "Внутреннее плечо (км)": internal_kms_list,
        "Дисконтированные затраты (млрд руб)": round(total_disc_cost / 1000, 2),
        "CAPEX (млрд руб)": round(total_capex / 1000, 2),
        "Макс. потребность в ТС": int(max_vehicles),
        "yearly_data": aggregated,
        "params": {
            "nodes": nodes_list,
            "transports": transports_list,
            "internal_kms": internal_kms_list,
            "total_capex": total_capex,
            "node_details": node_details
        }
    }

def generate_all_variants(selected_nodes_with_transports):
    forecast = st.session_state.forecast_df
    forecast_inert = forecast['Инертные (тыс.т)'].tolist()
    forecast_gen = forecast['Генеральные (тыс.т)'].tolist()
    available_nodes = [node for node in selected_nodes_with_transports if node["transports"]]
    if not available_nodes:
        return pd.DataFrame()
    variants = []
    
    # 1 узел
    for node_info in available_nodes:
        node = node_info["name"]
        for t_type in node_info["transports"]:
            if t_type == "авто":
                variants.append(compute_option_detailed([node], [t_type], [50], forecast_inert, forecast_gen, disc_factors))
            elif t_type == "река":
                variants.append(compute_option_detailed([node], [t_type], [100], forecast_inert, forecast_gen, disc_factors))
            else:
                variants.append(compute_option_detailed([node], [t_type], [0], forecast_inert, forecast_gen, disc_factors))
    
    # 2 узла
    for i, node1_info in enumerate(available_nodes):
        for node2_info in available_nodes[i+1:]:
            for t1 in node1_info["transports"]:
                for t2 in node2_info["transports"]:
                    ikm1 = 50 if t1 == "авто" else (100 if t1 == "река" else 0)
                    ikm2 = 50 if t2 == "авто" else (100 if t2 == "река" else 0)
                    variants.append(compute_option_detailed([node1_info["name"], node2_info["name"]], [t1, t2], [ikm1, ikm2], forecast_inert, forecast_gen, disc_factors))
    
    # 3 узла
    if len(available_nodes) >= 3:
        for i, node1_info in enumerate(available_nodes):
            for j, node2_info in enumerate(available_nodes[i+1:], i+1):
                for node3_info in available_nodes[j+1:]:
                    for t1 in node1_info["transports"]:
                        for t2 in node2_info["transports"]:
                            for t3 in node3_info["transports"]:
                                ikm1 = 50 if t1 == "авто" else (100 if t1 == "река" else 0)
                                ikm2 = 50 if t2 == "авто" else (100 if t2 == "река" else 0)
                                ikm3 = 50 if t3 == "авто" else (100 if t3 == "река" else 0)
                                variants.append(compute_option_detailed([node1_info["name"], node2_info["name"], node3_info["name"]], [t1, t2, t3], [ikm1, ikm2, ikm3], forecast_inert, forecast_gen, disc_factors))
    
    # 4 узла
    if len(available_nodes) >= 4:
        for t1 in available_nodes[0]["transports"]:
            for t2 in available_nodes[1]["transports"]:
                for t3 in available_nodes[2]["transports"]:
                    for t4 in available_nodes[3]["transports"]:
                        nodes = [n["name"] for n in available_nodes]
                        transports = [t1, t2, t3, t4]
                        ikm_list = [50 if t == "авто" else (100 if t == "река" else 0) for t in transports]
                        variants.append(compute_option_detailed(nodes, transports, ikm_list, forecast_inert, forecast_gen, disc_factors))
    
    return pd.DataFrame(variants)

# ---------------------- ИНТЕРФЕЙС ----------------------
tab1, tab2, tab3, tab4 = st.tabs(["📋 Исходные данные", "⚙️ Генерация вариантов", "📐 Экономика", "📊 Дашборд"])

with tab1:
    st.header("Редактируемые исходные данные")
    with st.expander("📊 Настройки распределения грузопотока", expanded=False):
        st.session_state.distribution_method = st.radio(
            "Метод распределения грузопотока между складами (применяется на дашборде):",
            ["Равномерно", "По вместимости склада", "По расстоянию (ближе → больше груза)"],
            index=["Равномерно", "По вместимости склада", "По расстоянию (ближе → больше груза)"].index(st.session_state.distribution_method)
        )
    with st.expander("📍 Точки отправления (узлы) – расстояния", expanded=False):
        st.session_state.nodes_df = st.data_editor(st.session_state.nodes_df, num_rows="dynamic", key="nodes_edit")
    with st.expander("🏢 Вместимость складов", expanded=False):
        st.session_state.storage_df = st.data_editor(st.session_state.storage_df, num_rows="dynamic", key="storage_edit")
    with st.expander("📅 Период доставки (суток в году)", expanded=False):
        st.session_state.delivery_days_df = st.data_editor(st.session_state.delivery_days_df, num_rows="dynamic", key="days_edit")
    with st.expander("💰 Дополнительные капитальные затраты", expanded=False):
        st.session_state.extra_capex_df = st.data_editor(st.session_state.extra_capex_df, num_rows="dynamic", key="extra_edit")
    with st.expander("📈 Прогноз потребности МТР", expanded=False):
        st.session_state.forecast_df = st.data_editor(st.session_state.forecast_df, num_rows="dynamic", key="forecast_edit")
    with st.expander("🏭 Тарифы складов (погрузка/разгрузка/хранение)", expanded=False):
        st.session_state.warehouse_rates_df = st.data_editor(st.session_state.warehouse_rates_df, num_rows="dynamic", key="warehouse_edit")
    with st.expander("🚚 Тарифы (руб/маш*час) и характеристики", expanded=False):
        st.session_state.tariff_characteristics_df = st.data_editor(st.session_state.tariff_characteristics_df, num_rows="dynamic", key="tariff_edit")
    with st.expander("🚛 Общие параметры транспорта (скорость, грузоподъемность)", expanded=False):
        st.session_state.transport_types_df = st.data_editor(st.session_state.transport_types_df, num_rows="dynamic", key="transport_edit")
    with st.expander("📊 Тарифы транспорта по узлам (руб/ткм, руб/т, руб/ваг.км, руб/час)", expanded=False):
        st.session_state.transport_rates_by_node = st.data_editor(st.session_state.transport_rates_by_node, num_rows="dynamic", key="rates_edit")
    with st.expander("🛣️ Внутренние плечи (ПС/БКЦ)", expanded=False):
        st.session_state.internal_options_df = st.data_editor(st.session_state.internal_options_df, num_rows="dynamic", key="internal_edit")
    with st.expander("⚠️ Учет рисков", expanded=False):
        st.session_state.consider_risks = st.checkbox("Учитывать риски", value=st.session_state.consider_risks)
        st.session_state.risks_df = st.data_editor(st.session_state.risks_df, num_rows="dynamic", key="risks_edit")
    with st.expander("🖼️ Загрузить фоновое изображение карты", expanded=False):
        uploaded_file = st.file_uploader("Выберите файл (PNG, JPG)", type=["png", "jpg", "jpeg"])
        if uploaded_file is not None:
            st.session_state.uploaded_image = uploaded_file.read()
            st.image(st.session_state.uploaded_image, caption="Загруженное изображение", width=300)
with tab2:
    st.header("Настройка генерации вариантов")
    st.markdown("""
    **Логика генерации:**
    - Выберите узлы. Для каждого узла отметьте нужные виды транспорта.
    - **Авто** всегда генерируется с плечом 50 км (авто+ПС).
    - **Река** всегда генерируется с плечом 100 км (река+БКЦ).
    - **Ж/Д** и **авиа** – без плеча.
    - Комбинации из 2–4 узлов перебираются автоматически.
    """)
    all_nodes = st.session_state.nodes_df['Узел'].tolist()
    node_transport_availability = {
        "Коротчаево": ["авто", "жд", "авиа"],
        "Новый Уренгой": ["авто", "жд", "авиа"],
        "Лабытнанги": ["река", "авиа"],
        "Приобье": ["река", "авиа"]
    }
    transport_labels = {"авто": "🚛 Авто+ПС", "река": "⛴️ Река+БКЦ", "жд": "🚂 ЖД", "авиа": "✈️ Авиа"}
    
    col_buttons = st.columns(2)
    with col_buttons[0]:
        if st.button("✅ Выбрать все узлы"):
            for node in all_nodes:
                st.session_state[f"select_node_{node}"] = True
            st.rerun()
    with col_buttons[1]:
        if st.button("🔄 Сбросить выбор узлов"):
            for node in all_nodes:
                st.session_state[f"select_node_{node}"] = False
            st.rerun()
    
    selected_nodes_names = []
    cols_nodes = st.columns(len(all_nodes))
    for idx, node in enumerate(all_nodes):
        with cols_nodes[idx]:
            key = f"select_node_{node}"
            if key not in st.session_state:
                st.session_state[key] = False
            if st.checkbox(node, value=st.session_state[key], key=key):
                selected_nodes_names.append(node)
    
    if selected_nodes_names:
        st.subheader("Для каждого узла выберите виды транспорта")
        col_trans_buttons = st.columns(2)
        with col_trans_buttons[0]:
            if st.button("✅ Выбрать все доступные транспорты для выбранных узлов"):
                for node in selected_nodes_names:
                    available = node_transport_availability.get(node, [])
                    for t in available:
                        st.session_state[f"trans_{node}_{t}"] = True
                st.rerun()
        with col_trans_buttons[1]:
            if st.button("🔄 Снять все транспорты"):
                for node in selected_nodes_names:
                    available = node_transport_availability.get(node, [])
                    for t in available:
                        st.session_state[f"trans_{node}_{t}"] = False
                st.rerun()
        
        selected_nodes_with_transports = []
        cols = st.columns(min(len(selected_nodes_names), 3))
        for idx, node in enumerate(selected_nodes_names):
            with cols[idx % 3]:
                st.markdown(f"**{node}**")
                node_transports = []
                available = node_transport_availability.get(node, [])
                for t in ["авто", "река", "жд", "авиа"]:
                    disabled = t not in available
                    label = transport_labels[t]
                    key = f"trans_{node}_{t}"
                    if key not in st.session_state:
                        st.session_state[key] = (t in available)
                    if st.checkbox(label, value=st.session_state[key], key=key, disabled=disabled):
                        node_transports.append(t)
                selected_nodes_with_transports.append({"name": node, "transports": node_transports})
        
        if st.button("🚀 Сгенерировать все варианты", type="primary"):
            if not any(node["transports"] for node in selected_nodes_with_transports):
                st.error("Для выбранных узлов не выбран ни один вид транспорта.")
            else:
                with st.spinner("Генерация и расчёт..."):
                    results_df = generate_all_variants(selected_nodes_with_transports)
                    total_cargo_tons = (st.session_state.forecast_df["Инертные (тыс.т)"].sum() + 
                                        st.session_state.forecast_df["Генеральные (тыс.т)"].sum()) * 1000
                    results_df["Удельная цена (руб/т)"] = results_df["Дисконтированные затраты (млрд руб)"] * 1e9 / total_cargo_tons
                    results_df["Удельная цена (руб/т)"] = results_df["Удельная цена (руб/т)"].round(0).astype(int)
                    st.session_state.results_df = results_df
                    st.session_state.variants_list = results_df.to_dict('records')
                    st.success(f"✅ Сгенерировано {len(results_df)} вариантов")
                    st.rerun()
        
        # Отображение таблицы результатов (вне кнопки)
        if 'results_df' in st.session_state and st.session_state.results_df is not None:
            results_df = st.session_state.results_df
            display_cols = ["Код варианта", "Количество узлов", "Узлы (перечисление)", "Транспорт (перечисление)", 
                            "Дисконтированные затраты (млрд руб)", "Удельная цена (руб/т)"]
            st.subheader("📋 Результаты генерации")
            st.dataframe(results_df[display_cols].style.format({"Удельная цена (руб/т)": "{:.0f}"}), use_container_width=True)
        else:
            st.info("Нажмите «Сгенерировать все варианты», чтобы получить результаты.")
    else:
        st.info("Сначала выберите хотя бы один узел.")
with tab3:
    st.header("📐 Экономика – детальный расчёт формул")
    if 'variants_list' in st.session_state and st.session_state.variants_list:
        variant_names = [v["Код варианта"] for v in st.session_state.variants_list]
        selected_variant_name = st.selectbox("Выберите вариант для анализа", variant_names)
        selected_variant = next(v for v in st.session_state.variants_list if v["Код варианта"] == selected_variant_name)
        st.subheader(f"📌 Анализ варианта: {selected_variant['Код варианта']}")
        params = selected_variant["params"]
        st.markdown("### 1. Исходные данные по узлам")
        dist_df = pd.DataFrame(params["node_details"])
        dist_df = dist_df.rename(columns={
            "Расстояние до объекта (км)": "Расстояние до объекта (км)",
            "Плечо (км)": "Внутреннее плечо (км)",
            "Итоговое расстояние (км)": "Итоговое расстояние (км) = расстояние + плечо",
            "Расстояние для расчёта транспорта (км)": "Расстояние для транспорта (база)"
        })
        st.dataframe(dist_df, use_container_width=True)
        st.markdown("### 2. Сводные параметры")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"- **Количество узлов:** {selected_variant['Количество узлов']}")
            st.write(f"- **Узлы:** {selected_variant['Узлы (перечисление)']}")
        with col2:
            st.write(f"- **Транспорт:** {selected_variant['Транспорт (перечисление)']}")
            st.write(f"- **CAPEX (суммарный):** {params['total_capex']} млн руб")
        st.markdown("### 3. Принцип расчёта")
        st.markdown("""
        - Грузопоток (инертные + генеральные) **равномерно распределяется** между узлами.
        - **Транспортные затраты** рассчитываются только по **базовому расстоянию** (без учёта внутреннего плеча).  
          Внутреннее плечо (50 км для авто, 100 км для реки) учитывается отдельно в столбце **«Внутренняя доставка»**.
        - ПРР – по ставкам из таблицы.
        - Внутренняя доставка – по тарифу маш·час.
        - CAPEX суммируется по узлам и дисконтируется в первый год.
        """)
        st.markdown("### 4. Расчёт по годам (агрегированный)")
        yearly_df = pd.DataFrame(selected_variant["yearly_data"])
        st.dataframe(yearly_df, use_container_width=True)
        # Итоговое значение дисконтированного OPEX (без рисков)
        total_disc_opex = selected_variant["Дисконтированные затраты (млрд руб)"]
        st.markdown(f"**Итоговое значение дисконтированного OPEX (без учёта рисков): {total_disc_opex} млрд руб**")
        # Учёт рисков
        if st.session_state.consider_risks:
            risks = st.session_state.risks_df
            # Сумма ущерба с учётом вероятности
            total_risk_loss = 0
            for _, row in risks.iterrows():
                damage = row.get("Ущерб (млн руб)", 0)
                prob = row.get("Вероятность (%)", 0)
                if pd.notna(damage) and pd.notna(prob):
                    total_risk_loss += damage * (prob / 100)
            total_risk_loss_mlrd = total_risk_loss / 1000
            total_with_risk = total_disc_opex + total_risk_loss_mlrd
            st.markdown(f"**Сумма возможного ущерба от рисков: {total_risk_loss:.2f} млн руб ({total_risk_loss_mlrd:.3f} млрд руб)**")
            st.markdown(f"**Значение дисконтированного OPEX с учетом рисков: {total_with_risk:.3f} млрд руб**")
        st.markdown("### 5. Структура затрат (дисконтированная)")
        total_transport = sum(yearly_df["Транспорт (млн руб)"] * yearly_df["Коэффициент дисконтирования"])
        total_prr = sum(yearly_df["ПРР (млн руб)"] * yearly_df["Коэффициент дисконтирования"])
        total_internal = sum(yearly_df["Внутренняя доставка (млн руб)"] * yearly_df["Коэффициент дисконтирования"])
        total_capex_disc = selected_variant["CAPEX (млрд руб)"] * 1000 * disc_factors[0]
        components = {"Транспорт": total_transport, "ПРР": total_prr, "Внутренняя доставка": total_internal, "CAPEX": total_capex_disc}
        comp_df = pd.DataFrame({"Статья": list(components.keys()), "Дисконтированные затраты (млн руб)": list(components.values())})
        fig_pie = px.pie(comp_df, values="Дисконтированные затраты (млн руб)", names="Статья", title="Структура дисконтированных затрат")
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown(f"**Итого дисконтированные затраты: {selected_variant['Дисконтированные затраты (млрд руб)']} млрд руб**")
    else:
        st.info("ℹ️ Сначала выполните генерацию на вкладке 'Генерация вариантов'.")
with tab4:
    st.header("📊 Дашборд результатов")
    if 'results_df' in st.session_state and st.session_state.results_df is not None:
        df = st.session_state.results_df
        if df.empty:
            st.info("Нет сгенерированных вариантов. Сначала выполните генерацию на вкладке 'Генерация вариантов'.")
        else:
            df_sorted = df.sort_values('Дисконтированные затраты (млрд руб)')
            best = df_sorted.iloc[0]
            worst = df_sorted.iloc[-1]

            best_price = f"{best['Удельная цена (руб/т)']}"
            worst_price = f"{worst['Удельная цена (руб/т)']}"

            col_best, col_worst = st.columns(2)
            with col_best:
                st.success(f"🏆 **ЛУЧШИЙ ВАРИАНТ**\n\n**Код:** {best['Код варианта']}\n\n**Узлы:** {best['Узлы (перечисление)']}\n\n**Транспорт:** {best['Транспорт (перечисление)']}\n\n**💰 Затраты:** {best['Дисконтированные затраты (млрд руб)']} млрд руб.\n\n**💸 Удельная цена:** {best_price} руб/т")
            with col_worst:
                st.error(f"⚠️ **ХУДШИЙ ВАРИАНТ**\n\n**Код:** {worst['Код варианта']}\n\n**Узлы:** {worst['Узлы (перечисление)']}\n\n**Транспорт:** {worst['Транспорт (перечисление)']}\n\n**💰 Затраты:** {worst['Дисконтированные затраты (млрд руб)']} млрд руб.\n\n**💸 Удельная цена:** {worst_price} руб/т")

            st.subheader("🔍 Выбор лучших/худших вариантов")
            col_top, col_bottom = st.columns(2)
            with col_top:
                top_n = st.selectbox("Показать топ лучших вариантов:", [1, 3, 5, 7, 10, 15, 20], index=1)
                if st.button(f"Показать {top_n} лучших вариантов"):
                    st.session_state.show_top_n = top_n
            with col_bottom:
                bottom_n = st.selectbox("Показать топ худших вариантов:", [1, 3, 5, 7, 10, 15, 20], index=1)
                if st.button(f"Показать {bottom_n} худших вариантов"):
                    st.session_state.show_bottom_n = bottom_n

            if 'show_top_n' in st.session_state:
                st.write(f"### 🟢 Топ-{st.session_state.show_top_n} лучших вариантов")
                top_df = df_sorted.head(st.session_state.show_top_n)[["Код варианта", "Дисконтированные затраты (млрд руб)", "Удельная цена (руб/т)", "Узлы (перечисление)"]]
                # ИСПРАВЛЕНО: было "{:..0f}", стало "{:.0f}"
                st.dataframe(top_df.style.format({"Удельная цена (руб/т)": "{:.0f}"}), use_container_width=True)
            if 'show_bottom_n' in st.session_state:
                st.write(f"### 🔴 Топ-{st.session_state.show_bottom_n} худших вариантов")
                bottom_df = df_sorted.tail(st.session_state.show_bottom_n)[["Код варианта", "Дисконтированные затраты (млрд руб)", "Удельная цена (руб/т)", "Узлы (перечисление)"]]
                st.dataframe(bottom_df.style.format({"Удельная цена (руб/т)": "{:.0f}"}), use_container_width=True)

            # ========== ГРАФИК 1: ДИСКОНТИРОВАННЫЕ ЗАТРАТЫ ==========
            st.subheader("📊 Сравнение вариантов по дисконтированным затратам")
            total_variants = len(df_sorted)
            compare_options = [3, 5, 7, 10, 15, 20, total_variants]
            compare_labels = [str(x) for x in compare_options[:-1]] + [f"Все ({total_variants})"]
            selected_index = st.selectbox("Количество вариантов для графика сравнения:", options=list(range(len(compare_options))), format_func=lambda i: compare_labels[i], index=1, key="compare_n")
            compare_n = compare_options[selected_index]
            if compare_n == total_variants:
                df_compare = df_sorted.copy()
                title_n = f"Все варианты ({total_variants})"
            else:
                df_compare = df_sorted.head(compare_n).copy()
                title_n = f"топ-{compare_n}"
            
            df_compare.reset_index(drop=True, inplace=True)
            df_compare["№"] = df_compare.index + 1
            
            fig_cost = px.bar(df_compare, x="№", y="Дисконтированные затраты (млрд руб)",
                              title=f"Сравнение вариантов по затратам ({title_n})", text_auto=True, height=500,
                              color="Дисконтированные затраты (млрд руб)", color_continuous_scale="RdYlGn_r",
                              hover_data={"Код варианта": True, "Дисконтированные затраты (млрд руб)": ":.2f"})
            fig_cost.update_layout(xaxis_title="№ варианта", xaxis=dict(tickmode='linear', tick0=1, dtick=1))
            st.plotly_chart(fig_cost, use_container_width=True)

            # ========== ГРАФИК 2: УДЕЛЬНАЯ ЦЕНА ДОСТАВКИ 1 Т ==========
            st.subheader("📊 Удельная средневзвешенная цена доставки 1 т МТР")
            fig_price = px.bar(df_compare, x="№", y="Удельная цена (руб/т)",
                               title=f"Удельная цена доставки ({title_n})", text_auto=True, height=500,
                               color="Удельная цена (руб/т)", color_continuous_scale="RdYlGn_r",
                               hover_data={"Код варианта": True, "Удельная цена (руб/т)": ":.0f"})
            fig_price.update_layout(xaxis_title="№ варианта", xaxis=dict(tickmode='linear', tick0=1, dtick=1),
                                    yaxis_title="руб./т")
            st.plotly_chart(fig_price, use_container_width=True)

            st.subheader("📋 Детальная таблица всех вариантов")
            st.dataframe(results_df[display_cols].style.format({"Удельная цена (руб/т)": "{:.0f}"}), use_container_width=True)

            st.subheader("📈 Прогноз операционных затрат (OPEX) для выбранного варианта")
            variant_for_forecast = st.selectbox("Выберите вариант для прогноза OPEX", df_sorted["Код варианта"].tolist())
            selected_variant = df_sorted[df_sorted["Код варианта"] == variant_for_forecast].iloc[0]
            variant_detail = next(v for v in st.session_state.variants_list if v["Код варианта"] == variant_for_forecast)
            yearly_forecast = pd.DataFrame(variant_detail["yearly_data"])
            fig_forecast = px.line(yearly_forecast, x="Год", y="Итого OPEX (млн руб)",
                                   title=f"Прогноз суммарных OPEX для варианта {variant_for_forecast}",
                                   markers=True)
            st.plotly_chart(fig_forecast, use_container_width=True)

            st.subheader("🥧 Структура дисконтированных затрат для выбранного варианта")
            total_transport = sum(yearly_forecast["Транспорт (млн руб)"] * yearly_forecast["Коэффициент дисконтирования"])
            total_prr = sum(yearly_forecast["ПРР (млн руб)"] * yearly_forecast["Коэффициент дисконтирования"])
            total_internal = sum(yearly_forecast["Внутренняя доставка (млн руб)"] * yearly_forecast["Коэффициент дисконтирования"])
            total_capex_disc = selected_variant["CAPEX (млрд руб)"] * 1000 * disc_factors[0]
            comp = {"Транспорт": total_transport, "ПРР": total_prr, "Внутренняя доставка": total_internal, "CAPEX": total_capex_disc}
            comp_df = pd.DataFrame({"Статья": list(comp.keys()), "млн руб": list(comp.values())})
            fig_pie_detail = px.pie(comp_df, values="млн руб", names="Статья", title=f"Структура затрат для {variant_for_forecast}")
            st.plotly_chart(fig_pie_detail, use_container_width=True)

            # ========== КАРТА И ДИНАМИКА ==========
            st.subheader("🗺️ Карта распределения грузопотока (с возможностью редактирования координат)")

            if st.session_state.uploaded_image is None:
                st.info("Сначала загрузите фоновое изображение карты на вкладке 'Исходные данные'.")
            else:
                st.subheader("Настройки отображения")
                col_period, _ = st.columns(2)
                with col_period:
                    period_type = st.radio("Период для карты:", ["Весь период (2027-2038)", "Один год", "Диапазон лет"], horizontal=True)
                    if period_type == "Один год":
                        selected_year = st.selectbox("Выберите год:", st.session_state.forecast_df["Год"].tolist(), index=0)
                        start_year = selected_year
                        end_year = selected_year
                    elif period_type == "Диапазон лет":
                        years = st.session_state.forecast_df["Год"].tolist()
                        start_year = st.selectbox("Начальный год:", years, index=0)
                        end_year = st.selectbox("Конечный год:", years, index=len(years)-1)
                    else:
                        start_year = 2027
                        end_year = 2038

                mask = (st.session_state.forecast_df["Год"] >= start_year) & (st.session_state.forecast_df["Год"] <= end_year)
                filtered_forecast = st.session_state.forecast_df[mask]
                total_cargo = filtered_forecast["Инертные (тыс.т)"].sum() + filtered_forecast["Генеральные (тыс.т)"].sum()
                st.caption(f"Общий объём груза за выбранный период: **{total_cargo:.1f} тыс. т**")

                st.subheader("Координаты складов (X, Y в пикселях)")
                if 'coords_df' not in st.session_state:
                    st.session_state.coords_df = pd.DataFrame({
                        "Узел": ["Коротчаево", "Лабытнанги", "Приобье", "Новый Уренгой"],
                        "X (пиксели)": [145, 80, 210, 410],
                        "Y (пиксели)": [115, 270, 350, 265]
                    })
                edited_coords = st.data_editor(st.session_state.coords_df, num_rows="dynamic", key="coords_editor_dashboard")
                st.session_state.coords_df = edited_coords

                nodes_in_variant = selected_variant["Узлы (перечисление)"].split(" + ")
                coords = st.session_state.coords_df
                plot_data = coords[coords["Узел"].isin(nodes_in_variant)].copy()
                if plot_data.empty:
                    st.warning("Для выбранного варианта нет координат. Проверьте таблицу координат.")
                else:
                    plot_data = plot_data.merge(st.session_state.storage_df[["Узел", "Вместимость (м2)"]], on="Узел", how="left")
                    plot_data = plot_data.merge(st.session_state.nodes_df[["Узел", "Расстояние до объекта (км)"]], on="Узел", how="left")
                    plot_data["Вместимость (м2)"].fillna(1, inplace=True)
                    plot_data["Расстояние до объекта (км)"].fillna(1000, inplace=True)

                    method = st.session_state.distribution_method
                    if method == "Равномерно":
                        weights = np.ones(len(plot_data))
                    elif method == "По вместимости склада":
                        weights = plot_data["Вместимость (м2)"].values
                    else:
                        weights = 1.0 / plot_data["Расстояние до объекта (км)"].values
                    percent = weights / weights.sum() * 100
                    plot_data["Доля грузопотока, %"] = np.round(percent, 1)
                    plot_data["Объём груза, тыс. т"] = np.round(total_cargo * percent / 100, 1)

                    st.write("**Распределение грузопотока по складам (за выбранный период):**")
                    st.dataframe(plot_data[["Узел", "Доля грузопотока, %", "Объём груза, тыс. т", "Вместимость (м2)", "Расстояние до объекта (км)"]])
                    st.caption(f"Метод распределения: {method}. Общий объём груза за {start_year}–{end_year}: {total_cargo:.1f} тыс. т.")

                    img = Image.open(io.BytesIO(st.session_state.uploaded_image))
                    fig_map = go.Figure()
                    fig_map.add_layout_image(
                        dict(source=img, xref="x", yref="y", x=0, y=0, sizex=img.width, sizey=img.height, sizing="stretch", layer="below")
                    )
                    fig_map.update_xaxes(range=[0, img.width], constrain="domain")
                    fig_map.update_yaxes(range=[img.height, 0], scaleanchor="x", scaleratio=1)

                    max_volume = plot_data["Объём груза, тыс. т"].max()
                    sizes = (plot_data["Объём груза, тыс. т"] / max_volume * 50) + 10 if max_volume > 0 else 20
                    fig_map.add_trace(go.Scatter(
                        x=plot_data["X (пиксели)"],
                        y=plot_data["Y (пиксели)"],
                        mode="markers+text",
                        marker=dict(
                            size=sizes,
                            color=plot_data["Доля грузопотока, %"],
                            colorscale="Viridis",
                            showscale=True,
                            colorbar=dict(title="Доля, %")
                        ),
                        text=[f"{v} тыс. т<br>{d}%" for v, d in zip(plot_data["Объём груза, тыс. т"], plot_data["Доля грузопотока, %"])],
                        textposition="top center",
                        textfont=dict(color="black", size=10),
                        hoverinfo="text",
                        hovertext=[f"{u}<br>Доля: {d}%<br>Объём: {v} тыс. т" for u, d, v in zip(plot_data["Узел"], plot_data["Доля грузопотока, %"], plot_data["Объём груза, тыс. т"])]
                    ))
                    fig_map.update_layout(title=f"Распределение грузопотока ({method}) за {start_year}–{end_year}", width=800, height=600)
                    st.plotly_chart(fig_map, use_container_width=True)

            st.subheader("📈 Динамика грузопотока по складам по годам")
            method = st.session_state.distribution_method
            st.caption(f"Метод распределения: **{method}** (можно изменить в исходных данных)")
            nodes_in_variant = selected_variant["Узлы (перечисление)"].split(" + ")
            node_data = []
            for node in nodes_in_variant:
                storage_row = st.session_state.storage_df[st.session_state.storage_df["Узел"] == node]
                capacity = storage_row["Вместимость (м2)"].values[0] if not storage_row.empty else 1
                dist_row = st.session_state.nodes_df[st.session_state.nodes_df["Узел"] == node]
                distance = dist_row["Расстояние до объекта (км)"].values[0] if not dist_row.empty else 1000
                node_data.append({"Узел": node, "Вместимость (м2)": capacity, "Расстояние (км)": distance})
            if node_data:
                node_df = pd.DataFrame(node_data)
                if method == "Равномерно":
                    weights = np.ones(len(node_df))
                elif method == "По вместимости склада":
                    weights = node_df["Вместимость (м2)"].values
                else:
                    weights = 1.0 / node_df["Расстояние (км)"].values
                weights = weights / weights.sum()
                node_df["Доля"] = weights
                forecast_total = st.session_state.forecast_df.copy()
                forecast_total["Всего"] = forecast_total["Инертные (тыс.т)"] + forecast_total["Генеральные (тыс.т)"]
                dyn_data = []
                for _, row in node_df.iterrows():
                    node = row["Узел"]
                    weight = row["Доля"]
                    for year, total in zip(forecast_total["Год"], forecast_total["Всего"]):
                        dyn_data.append({"Год": year, "Склад": node, "Объём (тыс. т)": total * weight})
                dyn_df = pd.DataFrame(dyn_data)
                fig_dyn = px.line(dyn_df, x="Год", y="Объём (тыс. т)", color="Склад",
                                  title=f"Динамика грузопотока по складам ({method})",
                                  markers=True)
                st.plotly_chart(fig_dyn, use_container_width=True)
                total_all = forecast_total["Всего"].sum()
                st.write(f"**Распределение общего объёма груза ({total_all:.1f} тыс. т) между складами:**")
                node_df["Объём (тыс. т)"] = total_all * node_df["Доля"]
                st.dataframe(node_df[["Узел", "Доля", "Объём (тыс. т)"]])
            else:
                st.warning("Не удалось получить данные для узлов.")

            st.subheader("📈 Исходный прогноз грузопотока по типам грузов (инертные / генеральные)")
            forecast_long = st.session_state.forecast_df.melt(id_vars=["Год"], var_name="Тип", value_name="Тыс. тн")
            fig_global = px.line(forecast_long, x="Год", y="Тыс. тн", color="Тип", title="Грузопоток по годам (исходные данные)", markers=True)
            st.plotly_chart(fig_global, use_container_width=True)

    else:
        st.info("ℹ️ Сначала выполните генерацию на вкладке 'Генерация вариантов'.")
