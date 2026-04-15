import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Control de Stock Crítico", layout="wide")

st.title("📊 Control de Stock con Alerta de Mínimos")
st.markdown("Los valores que estén por debajo del **Stock Ideal** se marcarán en rojo en el Excel.")

# 1. Diccionario de Stock Mínimo (Tus datos fijos)
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
        df['ITEM'] = df['ITEM'].astype(str).str.strip()

        # 3. Crear Matriz
        matriz = df.pivot_table(
            index=['ITEM', 'DESCRIPCION_ITEM'], 
            columns='LOC_DESCRIPTION', 
            values='STOCK', 
            aggfunc='sum'
        ).fillna(0).reset_index()

        # 4. Insertar columna de "Stock Ideal" al principio para comparar
        # Convertimos las llaves del diccionario a strings para comparar bien
        matriz.insert(2, 'STOCK_IDEAL', matriz['ITEM'].map(STOCK_IDEAL).fillna(0))

        st.success("✅ Matriz generada. Los técnicos con stock bajo se marcarán en el Excel.")
        st.dataframe(matriz, use_container_width=True)

        # 5. Generar Excel con Formato Condicional
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            matriz.to_excel(writer, index=False, sheet_name='Control_Stock')
            
            workbook  = writer.book
            worksheet = writer.sheets['Control_Stock']

            # Definir el formato rojo
            format_rojo = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})

            # Aplicar formato condicional a todas las columnas de técnicos
            # Empezamos desde la columna D (índice 3) hasta el final
            num_filas = len(matriz)
            num_cols = len(matriz.columns)
            
            for col_num in range(3, num_cols):
                # La regla es: SI el valor de la celda es MENOR que el valor en STOCK_IDEAL (Columna C)
                # Excel usa notación A1, así que Columna C es $C2
                worksheet.conditional_format(1, col_num, num_filas, col_num, {
                    'type':     'formula',
                    'criteria': f'={pd.io.formats.excel.get_column_letter(col_num + 1)}2 < $C2',
                    'format':   format_rojo
                })

        st.download_button(
            label="📥 DESCARGAR EXCEL CON ALERTAS ROJAS",
            data=output.getvalue(),
            file_name="Stock_Alertas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error: {e}")
