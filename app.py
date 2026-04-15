import streamlit as st
import pandas as pd
import io
from openpyxl.utils import get_column_letter

st.set_page_config(page_title="Control de Stock Getel", layout="wide")

st.title("📊 Reporte de Stock con Reglas de Grupo")

# --- CONFIGURACIÓN ---

STOCK_OBJETIVO = {
    '13008': 20, '30032': 350, '31025': 150, '31026': 30, '31027': 30,
    '31154': 12, '32085': 20, '32098': 2, '35042': 20, '51044': 20,
    '51051': 20, '70016': 6, '70098': 12, '70220': 6, '87025': 150,
    '87026': 30, '87031': 12, '90002': 40, '90071': 2, '90072': 150,
    '90090': 30, '90106': 30
}

# Grupos Hoja 2 (Añadimos 51066 para la suma)
GRUPOS = [
    ['50018', '50019', '13014', '51046'],
    ['51079', '51080', '45139'],
    ['51300r', '12009U'],
    ['50016', '13013', '51075'],
    ['51066', '51066r', '45207', '45169', '51041'], # El grupo 5 ahora incluye ambos 51066
    ['50015', '13012']
]

DEPOSITOS_A_EXCLUIR = ['REC SERVICE', 'DEVOLUCIONES FIELD SERVICES', 'SERVICE']

archivo_subido = st.file_uploader("Subir Cloud_Report.txt", type=['txt'])

if archivo_subido:
    try:
        # --- PROCESAMIENTO ---
        df_raw = pd.read_csv(archivo_subido, sep=';', encoding='latin-1')
        df_raw.columns = df_raw.columns.str.strip()
        df_raw['ITEM'] = df_raw['ITEM'].astype(str).str.strip().str.lstrip('0')
        df_raw['LOC_DESCRIPTION'] = df_raw['LOC_DESCRIPTION'].astype(str).str.strip()
        df_raw['STOCK'] = pd.to_numeric(df_raw['STOCK'], errors='coerce').fillna(0)
        df_base = df_raw[~df_raw['LOC_DESCRIPTION'].isin(DEPOSITOS_A_EXCLUIR)]

        # --- MATRIZ 1 ---
        df1 = df_base[df_base['ITEM'].isin(STOCK_OBJETIVO.keys())]
        matriz_1 = df1.pivot_table(index=['ITEM', 'DESCRIPCION_ITEM'], columns='LOC_DESCRIPTION', values='STOCK', aggfunc='sum').fillna(0).reset_index()
        matriz_1.insert(2, 'STOCK_OBJETIVO', matriz_1['ITEM'].map(STOCK_OBJETIVO))

        # --- MATRIZ 2 ---
        all_codes = [c for grupo in GRUPOS for c in grupo]
        df2 = df_base[df_base['ITEM'].isin(all_codes)]
        pivot_2 = df2.pivot_table(index=['ITEM', 'DESCRIPCION_ITEM'], columns='LOC_DESCRIPTION', values='STOCK', aggfunc='sum').fillna(0).reset_index()
        
        filas_finales = []
        for grupo in GRUPOS:
            for cod in grupo:
                fila = pivot_2[pivot_2['ITEM'] == cod]
                if not fila.empty:
                    filas_finales.append(fila.iloc[0].to_dict())
            filas_finales.append({}) # Celda vacía entre grupos

        matriz_2 = pd.DataFrame(filas_finales)

        # --- GENERAR EXCEL ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            matriz_1.to_excel(writer, index=False, sheet_name='Stock_Critico')
            matriz_2.to_excel(writer, index=False, sheet_name='Equipos_Agrupados')
            
            wb = writer.book
            fmt_rojo = wb.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
            
            # Formato Hoja 1
            ws1 = writer.sheets['Stock_Critico']
            for col in range(3, len(matriz_1.columns)):
                L = get_column_letter(col + 1)
                ws1.conditional_format(1, col, len(matriz_1), col, {'type': 'formula', 'criteria': f'={L}2 < $C2', 'format': fmt_rojo})

            # Formato Hoja 2 (Reglas de Grupo)
            ws2 = writer.sheets['Equipos_Agrupados']
            for col in range(2, len(matriz_2.columns)):
                L = get_column_letter(col + 1)
                # G1: 13014 y 51046 (filas 4,5) < suma 50018+50019 (filas 2,3)
                ws2.conditional_format(f'{L}4:{L}5', {'type': 'formula', 'criteria': f'={L}4 < ({L}$2+{L}$3)', 'format': fmt_rojo})
                # G2: 51080 y 45139 (filas 8,9) < 51079 (fila 7)
                ws2.conditional_format(f'{L}8:{L}9', {'type': 'formula', 'criteria': f'={L}8 < {L}$7', 'format': fmt_rojo})
                # G3: 51300r != 12009U (filas 11,12)
                ws2.conditional_format(f'{L}11:{L}12', {'type': 'formula', 'criteria': f'={L}11 <> {L}12', 'format': fmt_rojo})
                # G4: 13013 y 51075 (filas 15,16) < 50016 (fila 14)
                ws2.conditional_format(f'{L}15:{L}16', {'type': 'formula', 'criteria': f'={L}15 < {L}$14', 'format': fmt_rojo})
                # G5: 45207, 45169, 51041 (filas 20,21,22) < suma 51066+51066r (filas 18,19)
                ws2.conditional_format(f'{L}20:{L}22', {'type': 'formula', 'criteria': f'={L}20 < ({L}$18+{L}$19)', 'format': fmt_rojo})

            ws1.set_column(0, 50, 15)
            ws2.set_column(0, 50, 15)

        # Botón de descarga corregido
        st.success("✅ Archivo listo para descargar.")
        st.download_button(
            label="📥 DESCARGAR REPORTE FINAL",
            data=output.getvalue(),
            file_name="Reporte_Stock_Getel.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error: {e}")
