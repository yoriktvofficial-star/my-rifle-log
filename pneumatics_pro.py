import streamlit as st
import pandas as pd
import datetime
import os
from fpdf import FPDF

# Обновленные константы по вашему указу
PLAN_CLEAN = 500    # Плановая чистка
GEN_CLEAN = 1500    # Генеральная (освинцовка)
LUBE_INT = 1500     # Смазка механизмов (ТЕПЕРЬ ТОЖЕ 1500!)
DATA_FILE = "arsenal_data.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["Дата", "Выстрелы", "Пуля", "Масса_г", "Скорость_v0", "Энергия_Дж"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Pneumatic Arsenal: Master Report 2026', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, 'Ballistics Formula: E = (m * v0^2) / 2', 0, 1, 'C')
        self.ln(10)

def create_pdf(df):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    cols = ["Date", "Shots", "Ammo", "v0 (m/s)", "Energy (J)"]
    for col in cols:
        pdf.cell(38, 10, col, 1)
    pdf.ln()
    for _, row in df.tail(20).iterrows():
        pdf.cell(38, 10, str(row['Дата']), 1), pdf.cell(38, 10, str(row['Выстрелы']), 1)
        pdf.cell(38, 10, str(row['Пуля']), 1), pdf.cell(38, 10, str(row['Скорость_v0']), 1)
        pdf.cell(38, 10, str(row['Энергия_Дж']), 1), pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- ИНТЕРФЕЙС ---
st.set_page_config(page_title="Pneumo Master 2026", layout="wide")
st.title("Оружейный журналъ.")

df = load_data()
total_shots = df["Выстрелы"].sum() if not df.empty else 0

# Боковая панель с вашей формулой
st.sidebar.header("📜 Формула с чертежа")
st.sidebar.latex(r"E = \frac{m \cdot v_0^2}{2}")
m_g = st.sidebar.number_input("Масса m (г)", value=0.67, step=0.01)
v0 = st.sidebar.number_input("Скорость v₀ (м/с)", value=280.0, step=1.0)
energy = round(((m_g / 1000) * (v0**2)) / 2, 2)
st.sidebar.metric("Дульная энергия E", f"{energy} Дж")

# Состояние ТО
st.subheader("🛠 График обслуживания")
c1, c2, c3 = st.columns(3)

def draw_gauge(col, label, limit, current, color):
    rem = limit - (current % limit)
    col.metric(label, f"{rem} выстр.")
    col.progress(min((limit - rem) / limit, 1.0))
    if rem < 50: col.error(f"⚠️ СРОЧНО ТО!")

draw_gauge(c1, "Плановая (500)", PLAN_CLEAN, total_shots, "blue")
draw_gauge(c2, "Генеральная (1500)", GEN_CLEAN, total_shots, "orange")
draw_gauge(c3, "Смазка (1500)", LUBE_INT, total_shots, "red")

# Форма записи
with st.form("entry"):
    st.write("### ✒️ Внести данные о стрельбе")
    f1, f2, f3 = st.columns(3)
    shots_val = f1.number_input("Количество выстрелов", min_value=1, value=30)
    v0_val = f2.number_input("Скорость v₀ в сессии", value=v0)
    ammo_val = f3.text_input("Тип снаряда", "JSB Exact")
    
    if st.form_submit_button("Засвидетельствовать"):
        e_val = round(((m_g / 1000) * (v0_val**2)) / 2, 2)
        new_row = pd.DataFrame({
            "Дата": [datetime.date.today()], "Выстрелы": [shots_val],
            "Пуля": [ammo_val], "Масса_г": [m_g],
            "Скорость_v0": [v0_val], "Энергия_Дж": [e_val]
        })
        df = pd.concat([df, new_row], ignore_index=True)
        save_data(df)
        st.success("Данные внесены в анналы истории!")
        st.info("💡 Дружеское напоминание: Очистите корпус маслом, дабы блестел аки новый!")
        st.rerun()

# Таблица и экспорт
if not df.empty:
    st.write("---")
    st.subheader("📊 История настрела")
    st.dataframe(df.tail(15), use_container_width=True)
    
    pdf_bytes = create_pdf(df)
    st.download_button("📄 Сформировать PDF для заморских друзей", 
                       data=pdf_bytes, file_name="pneumo_log.pdf", mime="application/pdf")
