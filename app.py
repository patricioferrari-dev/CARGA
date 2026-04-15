import streamlit as st
import pandas as pd
import io
from openpyxl.utils import get_column_letter

st.set_page_config(page_title="Control de Stock Crítico", layout="wide")

st.title("📊 Reporte de Stock Crítico Filtrado")
st.markdown("Filtros aplicados: Solo códigos seleccionados y exclusión de depósitos no operativos.")

# 1. Diccionario de Stock Objetivo
STOCK_OBJETIVO = {
    '13008': 20, '30032': 350, '31025': 150, '31026': 30, '31027': 30,
    '31154': 12, '32085': 20, '32098': 2, '35042': 20, '51044': 20,
    '51051': 20, '70016': 6, '70098': 12, '70220': 6, '87025': 150,
    '87026': 30, '87031': 12, '90002': 40, '90071': 2, '90072': 150,
    '90090': 30, '90106': 30
}

# 2. Lista de depósitos a OMITIR
DEPOSITOS_A_EXCLUIR = ['REC SERVICE', 'DEVOLUCIONES FIELD SERVICES', 'SERVICE']

archivo_subido = st.file_uploader("Subir Cloud_Report.txt", type=['txt'])

if archivo_subido:
    try:
        # 3. Leer y limpiar el archivo
        df = pd.read_csv(archivo_subido, sep=';', encoding='latin-1')
        df.columns = df.columns.str.strip()
        
        # Limpieza de ITEM y LOC_DESCRIPTION
        df['ITEM'] = df['ITEM'].astype(str).str.strip().str.lstrip('0')
        df['LOC_DESCRIPTION'] = df['LOC_DESCRIPTION'].astype(str).str.strip()
        
        # --- FILTRO 1: Solo códigos de la lista ---
        df = df[df['ITEM'].isin(STOCK_OBJETIVO.keys())]
        
        # --- FILTRO 2: Omitir depósitos específicos ---
        df = df[~df['LOC_DESCRIPTION'].isin(DEPOSITOS_A_EXCLUIR)]
        
        if df.empty:
            st.error("❌ No se encontraron datos con los filtros aplicados.")
        else:
            df['STOCK'] = pd.to_numeric(df['STOCK'], errors='coerce').fillna(0)

            # 4. Crear Matriz
            matriz = df.pivot_table(
                index=['ITEM', 'DESCRIPCION_ITEM'], 
                columns='LOC_DESCRIPTION', 
                values='STOCK', 
                aggfunc='sum'
            ).fillna(0).reset_index()

            # 5. Insertar STOCK OBJETIVO
            matriz.insert(2, 'STOCK_OBJETIVO', matriz['ITEM'].map(STOCK_OBJETIVO))

            st.success(f"✅ Reporte listo: {len(matriz)} materiales y {len(matriz.columns) - 3} sub-inventarios.")
            st.dataframe(matriz, use_container_width=True, hide_index=True)

            # 6. Generar Excel con Formato Condicional
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                matriz.to_excel(writer, index=False, sheet_name='Stock_Critico')
                
                workbook  = writer.book
                worksheet = writer.sheets['Stock_Critico']
                format_rojo = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})

                num_filas = len(matriz)
                num_cols = len(matriz.columns)
                
                # Aplicar alerta roja (compara columnas de técnicos vs Columna C)
                for col_num in range(3, num_cols):
                    letra_col = get_column_letter(col_num + 1)
                    criterio = f'={letra_col}2 < $C2'
                    
                    worksheet.conditional_format(1, col_num, num_filas, col_num, {
                        'type':     'formula',
                        'criteria': criterio,
                        'format':   format_rojo
                    })
                
                # Ajuste de ancho de columnas
                for i, col in enumerate(matriz.columns):
                    worksheet.set_column(i, i, max(len(str(col)), 15))

            st.download_button(
                label="📥 DESCARGAR EXCEL FINAL",
                data=output.getvalue(),
                file_name="Reporte_Stock_Filtrado_Getel.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    except Exception as e:
        st.error(f"Error: {e}")
