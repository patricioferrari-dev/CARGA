import streamlit as st
import pandas as pd
import io
from openpyxl.utils import get_column_letter # Importación correcta

st.set_page_config(page_title="Control de Stock Crítico", layout="wide")

st.title("📊 Control de Stock con Alerta de Mínimos")

# 1. Diccionario de Stock Mínimo (Datos Fijos)
# Nota: He normalizado los códigos para que coincidan con el formato del TXT
STOCK_IDEAL = {
    '13008': 18, '30032': 350, '31025': 150, '31026': 30, '31027': 30,
    '31154': 10, '32085': 20, '32098': 2, '35042': 20, '51044': 18,
    '51051': 18, '70016': 7, '70098': 12, '70220': 8, '87025': 150,
    '87026': 30, '87031': 12, '90002': 40, '90071': 2, '90072': 150,
    '90090': 30, '90091': 3, '90106': 30
}

archivo_subido = st.file_uploader("Subir Cloud_Report.txt", type=['txt'])

if archivo_subido:
    try:
        # 2. Procesar el archivo
        df = pd.read_csv(archivo_subido, sep=';', encoding='latin-1')
        df.columns = df.columns.str.strip()
        df['STOCK'] = pd.to_numeric(df['STOCK'], errors='coerce').fillna(0)
        
        # Limpieza profunda de la columna ITEM para que coincida con el diccionario
        df['ITEM'] = df['ITEM'].astype(str).str.strip().str.lstrip('0')

        # 3. Crear Matriz
        matriz = df.pivot_table(
            index=['ITEM', 'DESCRIPCION_ITEM'], 
            columns='LOC_DESCRIPTION', 
            values='STOCK', 
            aggfunc='sum'
        ).fillna(0).reset_index()

        # 4. Insertar columna de "STOCK OBJETIVO" en la posición 2
        # Buscamos cada ITEM en nuestro diccionario de Stock Ideal
        matriz.insert(2, 'STOCK_OBJETIVO', matriz['ITEM'].map(STOCK_IDEAL).fillna(0))

        st.success("✅ Matriz generada con alertas de stock bajo.")
        st.dataframe(matriz, use_container_width=True, hide_index=True)

        # 5. Generar Excel con Formato Condicional (usando XlsxWriter)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            matriz.to_excel(writer, index=False, sheet_name='Control_Stock')
            
            workbook  = writer.book
            worksheet = writer.sheets['Control_Stock']

            # Formato para las celdas en rojo
            format_rojo = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})

            num_filas = len(matriz)
            num_cols = len(matriz.columns)
            
            # Aplicamos la regla desde la 4ta columna (donde empiezan los técnicos)
            for col_num in range(3, num_cols):
                letra_col_tecnico = get_column_letter(col_num + 1)
                # Comparación: SI Celda Técnico < Celda STOCK_OBJETIVO (Columna C)
                # La fila empieza en 2 en Excel
                criterio = f'={letra_col_tecnico}2 < $C2'
                
                worksheet.conditional_format(1, col_num, num_filas, col_num, {
                    'type':     'formula',
                    'criteria': criterio,
                    'format':   format_rojo
                })
            
            # Ajuste de ancho de columnas
            for i, col in enumerate(matriz.columns):
                worksheet.set_column(i, i, max(len(str(col)), 12))

        st.download_button(
            label="📥 DESCARGAR EXCEL CON ALERTAS",
            data=output.getvalue(),
            file_name="Stock_Alertas_Getel.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error: {e}")
