import streamlit as st
import pandas as pd
import io
from openpyxl.utils import get_column_letter

st.set_page_config(page_title="Control de Stock Getel", layout="wide")

st.title("📊 Reporte de Stock con Reglas de Grupo")

# --- CONFIGURACIÓN ---

# Hoja 1: Críticos
STOCK_OBJETIVO = {
    '13008': 20, '30032': 350, '31025': 150, '31026': 30, '31027': 30,
    '31154': 12, '32085': 20, '32098': 2, '35042': 20, '51044': 20,
    '51051': 20, '70016': 6, '70098': 12, '70220': 6, '87025': 150,
    '87026': 30, '87031': 12, '90002': 40, '90071': 2, '90072': 150,
    '90090': 30, '90106': 30
}

# Hoja 2: Grupos y sus códigos (para filtrado y orden)
GRUPOS = [
    ['50018', '50019', '13014', '51046'],
    ['51079', '51080', '45139'],
    ['51300r', '12009U'], # Normalizados sin '0' inicial
    ['50016', '13013', '51075'],
    ['51066r', '45207', '45169', '51041'],
    ['50015', '13012']
]

DEPOSITOS_A_EXCLUIR = ['REC SERVICE', 'DEVOLUCIONES FIELD SERVICES', 'SERVICE']

archivo_subido = st.file_uploader("Subir Cloud_Report.txt", type=['txt'])

if archivo_subido:
    try:
        # --- PROCESAMIENTO BASE ---
        df_raw = pd.read_csv(archivo_subido, sep=';', encoding='latin-1')
        df_raw.columns = df_raw.columns.str.strip()
        df_raw['ITEM'] = df_raw['ITEM'].astype(str).str.strip().str.lstrip('0')
        df_raw['LOC_DESCRIPTION'] = df_raw['LOC_DESCRIPTION'].astype(str).str.strip()
        df_raw['STOCK'] = pd.to_numeric(df_raw['STOCK'], errors='coerce').fillna(0)
        df_base = df_raw[~df_raw['LOC_DESCRIPTION'].isin(DEPOSITOS_A_EXCLUIR)]

        # --- GENERAR MATRIZ HOJA 1 ---
        df1 = df_base[df_base['ITEM'].isin(STOCK_OBJETIVO.keys())]
        matriz_1 = df1.pivot_table(index=['ITEM', 'DESCRIPCION_ITEM'], columns='LOC_DESCRIPTION', values='STOCK', aggfunc='sum').fillna(0).reset_index()
        matriz_1.insert(2, 'STOCK_OBJETIVO', matriz_1['ITEM'].map(STOCK_OBJETIVO))

        # --- GENERAR MATRIZ HOJA 2 CON ESPACIOS ---
        all_codes = [c for grupo in GRUPOS for c in grupo]
        df2 = df_base[df_base['ITEM'].isin(all_codes)]
        pivot_2 = df2.pivot_table(index=['ITEM', 'DESCRIPCION_ITEM'], columns='LOC_DESCRIPTION', values='STOCK', aggfunc='sum').fillna(0).reset_index()
        
        # Crear la lista final con filas vacías
        filas_finales = []
        indices_reglas = [] # Guardaremos dónde empieza cada grupo para las fórmulas de Excel
        current_row = 1 # Excel empieza en 1, pero pandas en 0 + encabezado
        
        for grupo in GRUPOS:
            inicio_grupo = len(filas_finales) + 2 # +2 por encabezado y base 1
            for cod in grupo:
                fila = pivot_2[pivot_2['ITEM'] == cod]
                if not fila.empty:
                    filas_finales.append(fila.iloc[0].to_dict())
            indices_reglas.append((inicio_grupo, len(filas_finales) + 1))
            filas_finales.append({}) # Fila vacía entre grupos

        matriz_2 = pd.DataFrame(filas_finales)

        # --- INTERFAZ ---
        st.success("✅ Reporte generado con reglas de validación entre equipos.")
        st.download_button(label="📥 DESCARGAR EXCEL CON REGLAS DE GRUPO", 
                           data=None, # Se genera abajo
                           file_name="Reporte_Getel_Inteligente.xlsx")

        # --- EXCEL ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            matriz_1.to_excel(writer, index=False, sheet_name='Stock_Critico')
            matriz_2.to_excel(writer, index=False, sheet_name='Equipos_Agrupados')
            
            wb = writer.book
            ws2 = writer.sheets['Equipos_Agrupados']
            fmt_rojo = wb.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
            
            num_cols = len(matriz_2.columns)
            
            # APLICAR REGLAS ESPECÍFICAS POR GRUPO (HOJA 2)
            for col_idx in range(2, num_cols):
                L = get_column_letter(col_idx + 1)
                
                # Grupo 1 (Filas 2-5): Si (50018+50019) > 13014 o 51046
                # Regla: Suma filas 2 y 3 vs fila 4 y 5
                ws2.conditional_format(f'{L}4:{L}5', {'type': 'formula', 'criteria': f'={L}4 < ({L}$2+{L}$3)', 'format': fmt_rojo})
                
                # Grupo 2 (Filas 7-9): Si tecnico < 51079 (Fila 7)
                ws2.conditional_format(f'{L}8:{L}9', {'type': 'formula', 'criteria': f'={L}8 < {L}$7', 'format': fmt_rojo})
                
                # Grupo 3 (Filas 11-12): Igualdad entre 051300r y 012009U
                ws2.conditional_format(f'{L}11:{L}12', {'type': 'formula', 'criteria': f'={L}11 <> {L}12', 'format': fmt_rojo})
                
                # Grupo 4 (Filas 14-16): Si 13013 o 51075 < 50016
                ws2.conditional_format(f'{L}15:{L}16', {'type': 'formula', 'criteria': f'={L}15 < {L}$14', 'format': fmt_rojo})
                
                # Grupo 5 (Filas 18-21): Si 45207, 45169, 51041 < 51066r
                ws2.conditional_format(f'{L}19:{L}21', {'type': 'formula', 'criteria': f'={L}19 < {L}$18', 'format': fmt_rojo})

            # Ajuste de columnas
            ws2.set_column(0, 1, 15)
            ws2.set_column(2, num_cols, 12)

        st.download_button(label="📥 DESCARGAR EXCEL", data=output.getvalue(), file_name="Reporte_Getel_Grupos.xlsx", use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
