import streamlit as st
import pandas as pd
import datetime
import os
from fpdf import FPDF

# --- НАСТРОЙКИ ТО ---
PLAN_CLEAN = 500    # Плановая
GEN_CLEAN = 1500    # Генеральная
LUBE_INT = 1500     # Смазка
DATA_FILE = "arsenal_data.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["Дата", "Выстрелы", "Пуля", "Масса_г", "Скорость_v0", "Энергия_Дж"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# --- ГЕНЕРАТОР PDF БЕЗ ОШИБОК ---
def create_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    # Используем стандартный шрифт Helvetica (он же Arial)
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, 'Pneumatic Arsenal Report 2026', 0, 1, 'C')
    pdf.ln(10)
    
    pdf.set_font("Helvetica", size=10)
    # Заголовки на латинице для стабильности
    headers = ["Date", "Shots", "Ammo", "v0 (m/s)", "Energy (J)"]
    for h in headers:
        pdf.cell(38, 10, h, 1)
    pdf.ln()
    
    # Данные
    for _, row in df.tail(20).iterrows():
        pdf.cell(38, 10, str(row['Дата']), 1)
        pdf.cell(38, 10, str(row['Выстрелы']), 1)
        # Очистка от кириллицы только для PDF, чтобы не было UnicodeEncodeError
        ammo_name = str(row['Пуля']).encode('ascii', 'ignore').decode('ascii')
        if not ammo_name: ammo_name = "Custom Pellet"
        pdf.cell(38, 10, ammo_name, 1)
        pdf.cell(38, 10, str(row['Скорость_v0']), 1)
        pdf.cell(38, 10, str(row['Энергия_Дж']), 1)
        pdf.ln()
    
    return pdf.output()

# --- ИНТЕРФЕЙС STREAMLIT ---
st.set_page_config(page_title="Pneumo Master 2026", layout="wide")
st.title("🎯 Оружейный журналъ")

df = load_data()
total_shots = df["Выстрелы"].sum() if not df.empty else 0

# Боковая панель с твоей формулой
st.sidebar.header("📜 Формула с чертежа")
st.sidebar.latex(r"E = \frac{m \cdot v_0^2}{2}")
m_g = st.sidebar.number_input("Масса пули m (г)", value=0.67, step=0.01)
v0_calc = st.sidebar.number_input("Скорость v0 (м/с)", value=280.0, step=1.0)
e_calc = round(((m_g / 1000) * (v0_calc**2)) / 2, 2)
st.sidebar.metric("Дульная энергия E", f"{e_calc} Дж")

# Блок ТО
st.subheader("🛠 График обслуживания")
c1, c2, c3 = st.columns(3)
def draw_stat(col, label, limit, current):
    rem = limit - (current % limit)
    col.metric(label, f"{rem} ост.")
    col.progress(min((limit - rem) / limit, 1.0))
    if rem < 50: col.error("⚠️ ПОРА ТО!")

draw_stat(c1, "Плановая (500)", PLAN_CLEAN, total_shots)
draw_stat(c2, "Генеральная (1500)", GEN_CLEAN, total_shots)
draw_stat(c3, "Смазка (1500)", LUBE_INT, total_shots)

# Форма ввода
with st.form("add_session"):
    st.write("### 🖋 Записать отстрел")
    f1, f2, f3 = st.columns(3)
    s_val = f1.number_input("Выстрелов", min_value=1, value=30)
    v_val = f2.number_input("Замер v0 (м/с)", value=v0_calc)
    a_val = f3.text_input("Пули (в базе - латиницей)", "JSB Exact")
    
    if st.form_submit_button("Внести в реестр"):
        e_val = round(((m_g / 1000) * (v_val**2)) / 2, 2)
        new_data = pd.DataFrame({
            "Дата": [datetime.date.today()], "Выстрелы": [s_val],
            "Пуля": [a_val], "Масса_г": [m_g],
            "Скорость_v0": [v_val], "Энергия_Дж": [e_val]
        })
        df = pd.concat([df, new_data], ignore_index=True)
        save_data(df)
        st.success("Записано!")
        st.info("💡 Не забудь протереть железо маслом!")
        st.rerun()

# Таблица и PDF
if not df.empty:
    st.write("---")
    st.dataframe(df.tail(10), use_container_width=True)
    
    # Кнопка скачивания
    try:
        pdf_out = create_pdf(df)
        st.download_button("📄 Скачать PDF-отчет", data=pdf_out, 
                           file_name="report.pdf", mime="application/pdf")
    except Exception as e:
        st.error(f"Ошибка PDF: {e}")
