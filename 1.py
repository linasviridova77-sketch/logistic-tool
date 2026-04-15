import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Логистический инструмент", layout="wide")
st.title("📦 Формирование логистической стратегии снабжения")

# ---------------------- ИНИЦИАЛИЗАЦИЯ ДАННЫХ ----------------------
if 'nodes_df' not in st.session_state:
    st.session_state.nodes_df = pd.DataFrame({
        "Узел": ["Коротчаево", "Лабытнанги", "Приобье", "Новый Уренгой"],
        "Расстояние до объекта (км)": [395, 560, 243, 1030],
        "CAPEX склада (млн руб)": [500, 500, 500, 1000]
    })

if 'storage_df' not in st.session_state:
    st.session_state.storage_df = pd.DataFrame({
        "Узел": ["Новый Уренгой", "Коротчаево", "Лабытнанги", "Приобье"],
        "Вместимость (м2)": [300000, 350000, 160000, 120000]
    })

if 'delivery_days_df' not in st.session_state:
    st.session_state.delivery_days_df = pd.DataFrame({
        "Вид транспорта": ["river", "air", "rail", "auto"],
        "Доступные сутки": [148, 365, 365, 365]
    })

if 'extra_capex_df' not in st.session_state:
    st.session_state.extra_capex_df = pd.DataFrame({
        "Код варианта": ["Kor_auto_50", "NY_auto_50", "Kor_auto_100", "NY_auto_100", "rail"],
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
        "Разгрузка (руб/т)": [1019,1017,965,1393,244,1225,535,1685],
        "Погрузка (руб/т)": [1019,1016,408,484,431,1280,460,1039],
        "Хранение (тыс.руб/т)": [0.24,0.24,0.11,0.11,0.47,0.47,1.12,1.12]
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
        "Вид транспорта": ["auto", "river", "rail", "air"],
        "Тариф (ед. изм)": ["руб/ткм", "руб/т", "руб/ваг.км", "руб/час"],
        "Базовый тариф": [8.5, 1160, 1541.88, 185000],
        "Скорость (км/ч)": [40, 15, 50, 83.3],
        "Грузоподъемность (т)": [20, 500, 70, 2.2]
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

# Коэффициенты дисконтирования (12 лет, 2027-2038)
disc_factors = [0.936585811581694, 0.8215665013874507, 0.7206723696381145,
                0.6321687452965916, 0.5545339871022733, 0.48643332201953804,
                0.42669589650836653, 0.3742946460599707, 0.3283286368947111,
                0.28800757622343076, 0.25263822475739534, 0.2215]

# ---------------------- ФУНКЦИИ РАСЧЁТА ----------------------
def calc_transport_cost(transport_row, inert_tonnes, gen_tonnes, distance_km):
    t_type = transport_row['Вид транспорта']
    base_rate = transport_row['Базовый тариф']
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

def compute_option(option_desc, node, transport_type, internal_km, forecast_inert, forecast_gen, disc_factors):
    node_row = st.session_state.nodes_df[st.session_state.nodes_df['Узел'] == node].iloc[0]
    dist_to_obj = node_row['Расстояние до объекта (км)']
    capex_node = node_row['CAPEX склада (млн руб)']
    
    transport_row = st.session_state.transport_types_df[st.session_state.transport_types_df['Вид транспорта'] == transport_type].iloc[0]
    
    internal_capex = 0
    internal_row = None
    if internal_km > 0:
        internal_row = st.session_state.internal_options_df[st.session_state.internal_options_df['Плечо (км)'] == internal_km].iloc[0]
        internal_capex = internal_row['CAPEX доп. (млн руб)']
    
    total_capex = capex_node + internal_capex
    total_disc_cost = 0
    max_vehicles = 0
    
    available_days = transport_row['Доступные сутки']
    speed = transport_row['Скорость (км/ч)']
    capacity = transport_row['Грузоподъемность (т)']
    main_dist = dist_to_obj - internal_km if internal_km > 0 else dist_to_obj
    if main_dist <= 0:
        main_dist = dist_to_obj
    
    trips_per_day = 24 / (2 * main_dist / speed) if speed > 0 else 0
    annual_capacity_per_vehicle = available_days * trips_per_day * capacity
    
    for i, (inert, gen) in enumerate(zip(forecast_inert, forecast_gen)):
        trans_inert, trans_gen = calc_transport_cost(transport_row, inert, gen, main_dist)
        prr_inert, prr_gen = calc_prr_cost(node, inert, gen)
        int_inert, int_gen = calc_internal_cost(internal_row, inert, gen, internal_km) if internal_km > 0 else (0,0)
        
        year_opex = trans_inert + trans_gen + prr_inert + prr_gen + int_inert + int_gen
        total_disc_cost += year_opex * disc_factors[i]
        
        total_tonnes = (inert + gen) * 1000
        if annual_capacity_per_vehicle > 0 and total_tonnes > 0:
            vehicles = np.ceil(total_tonnes / annual_capacity_per_vehicle)
            if vehicles > max_vehicles:
                max_vehicles = vehicles
    
    total_disc_cost += total_capex * disc_factors[0]
    
    return {
        "Вариант": option_desc,
        "Узел": node,
        "Транспорт": transport_type,
        "Внутреннее плечо (км)": internal_km,
        "Дисконтированные затраты (млрд руб)": round(total_disc_cost / 1000, 2),
        "CAPEX (млрд руб)": round(total_capex / 1000, 2),
        "Макс. потребность в ТС": int(max_vehicles)
    }

def generate_all_variants(selected_nodes, selected_transports, include_50, include_100):
    forecast = st.session_state.forecast_df
    forecast_inert = forecast['Инертные (тыс.т)'].tolist()
    forecast_gen = forecast['Генеральные (тыс.т)'].tolist()
    
    variants = []
    for node in selected_nodes:
        for t_type in selected_transports:
            # Прямой маршрут
            variants.append(compute_option(f"{node} - {t_type} (прямая)", node, t_type, 0, forecast_inert, forecast_gen, disc_factors))
            # Маршруты с промежуточными складами (только для auto и river)
            if t_type in ['auto', 'river']:
                if include_50:
                    variants.append(compute_option(f"{node} - {t_type} +50км", node, t_type, 50, forecast_inert, forecast_gen, disc_factors))
                if include_100:
                    variants.append(compute_option(f"{node} - {t_type} +100км", node, t_type, 100, forecast_inert, forecast_gen, disc_factors))
    return pd.DataFrame(variants)

# ---------------------- ИНТЕРФЕЙС: ТРИ ВКЛАДКИ ----------------------
tab1, tab2, tab3 = st.tabs(["📋 Исходные данные", "⚙️ Генерация вариантов", "📊 Дашборд"])

with tab1:
    st.header("Редактируемые исходные данные")
    st.info("Изменяйте любые значения и добавляйте новые строки. После изменений перейдите на вкладку 'Генерация' и нажмите кнопку.")
    
    with st.expander("📍 Точки отправления (узлы)", expanded=False):
        edited_nodes = st.data_editor(st.session_state.nodes_df, num_rows="dynamic", key="nodes_edit")
        st.session_state.nodes_df = edited_nodes
    
    with st.expander("🏢 Вместимость складов", expanded=False):
        edited_storage = st.data_editor(st.session_state.storage_df, num_rows="dynamic", key="storage_edit")
        st.session_state.storage_df = edited_storage
    
    with st.expander("📅 Период доставки (суток в году)", expanded=False):
        edited_days = st.data_editor(st.session_state.delivery_days_df, num_rows="dynamic", key="days_edit")
        # синхронизация с transport_types_df
        for _, row in edited_days.iterrows():
            st.session_state.transport_types_df.loc[st.session_state.transport_types_df['Вид транспорта'] == row['Вид транспорта'], 'Доступные сутки'] = row['Доступные сутки']
        st.session_state.delivery_days_df = edited_days
    
    with st.expander("💰 Дополнительные капитальные затраты", expanded=False):
        edited_extra = st.data_editor(st.session_state.extra_capex_df, num_rows="dynamic", key="extra_edit")
        st.session_state.extra_capex_df = edited_extra
    
    with st.expander("📈 Прогноз потребности МТР", expanded=False):
        edited_forecast = st.data_editor(st.session_state.forecast_df, num_rows="dynamic", key="forecast_edit")
        st.session_state.forecast_df = edited_forecast
    
    with st.expander("🏭 Тарифы складов (погрузка/разгрузка/хранение)", expanded=False):
        edited_warehouse = st.data_editor(st.session_state.warehouse_rates_df, num_rows="dynamic", key="warehouse_edit")
        st.session_state.warehouse_rates_df = edited_warehouse
    
    with st.expander("🚚 Тарифы (руб/маш*час) и характеристики", expanded=False):
        edited_tariff = st.data_editor(st.session_state.tariff_characteristics_df, num_rows="dynamic", key="tariff_edit")
        st.session_state.tariff_characteristics_df = edited_tariff
    
    with st.expander("🚛 Виды транспорта (тарифы, скорость, грузоподъемность)", expanded=False):
        edited_transport = st.data_editor(st.session_state.transport_types_df, num_rows="dynamic", key="transport_edit")
        st.session_state.transport_types_df = edited_transport
    
    with st.expander("🛣️ Внутренние плечи (ПС/БКЦ)", expanded=False):
        edited_internal = st.data_editor(st.session_state.internal_options_df, num_rows="dynamic", key="internal_edit")
        st.session_state.internal_options_df = edited_internal

with tab2:
    st.header("Настройка генерации вариантов")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Выберите узлы")
        all_nodes = st.session_state.nodes_df['Узел'].tolist()
        selected_nodes = []
        for node in all_nodes:
            if st.checkbox(node, value=True, key=f"node_{node}"):
                selected_nodes.append(node)
    with col2:
        st.subheader("Выберите виды транспорта")
        all_transports = st.session_state.transport_types_df['Вид транспорта'].tolist()
        selected_transports = []
        for t in all_transports:
            if st.checkbox(t, value=True, key=f"trans_{t}"):
                selected_transports.append(t)
    
    st.subheader("Внутренние плечи")
    inc50 = st.checkbox("50 км (ПС/БКЦ)", value=True)
    inc100 = st.checkbox("100 км", value=True)
    
    if st.button("🚀 Сгенерировать все варианты", type="primary"):
        if not selected_nodes or not selected_transports:
            st.error("Выберите хотя бы один узел и один вид транспорта")
        else:
            with st.spinner("Генерация и расчёт..."):
                results_df = generate_all_variants(selected_nodes, selected_transports, inc50, inc100)
                st.session_state.results_df = results_df
                st.success(f"Сгенерировано {len(results_df)} вариантов")
                st.dataframe(results_df, use_container_width=True)

with tab3:
    st.header("Дашборд результатов")
    if 'results_df' in st.session_state and st.session_state.results_df is not None:
        df = st.session_state.results_df
        df_sorted = df.sort_values('Дисконтированные затраты (млрд руб)')
        best = df_sorted.iloc[0]
        st.success(f"🏆 **Рекомендуемый вариант:** {best['Вариант']} с затратами {best['Дисконтированные затраты (млрд руб)']} млрд руб.")
        
        # График
        fig = px.bar(df_sorted, x="Вариант", y="Дисконтированные затраты (млрд руб)",
                     title="Сравнение вариантов", text_auto=True, height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Таблица
        st.subheader("Детальная таблица")
        st.dataframe(df_sorted, use_container_width=True)
        
        # Динамика прогноза
        st.subheader("Прогноз грузопотока")
        forecast_long = st.session_state.forecast_df.melt(id_vars=["Год"], var_name="Тип", value_name="Тыс. тн")
        fig2 = px.line(forecast_long, x="Год", y="Тыс. тн", color="Тип", title="Грузопоток по годам", markers=True)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Сначала выполните генерацию на вкладке 'Генерация вариантов'.")
