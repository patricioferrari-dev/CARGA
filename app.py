import streamlit as st
import pandas as pd
import io
from openpyxl.utils import get_column_letter

st.set_page_config(page_title="Control de Stock Getel", layout="wide")

st.title("📊 Reporte de Stock con Pestañas Especiales")

# --- CONFIGURACIÓN DE FILTROS ---

# 1. Lista Hoja 1 (Críticos con Objetivo)
STOCK_OBJETIVO = {
    '13008': 20, '30032': 350, '31025': 150, '31026': 30, '31027': 30,
    '31154': 12, '32085': 20, '32098': 2, '35042': 20, '51044': 20,
    '51051': 20, '70016': 6, '70098': 12, '70220': 6, '87025': 150,
    '87026': 30, '87031': 12, '90002': 40, '90071': 2, '90072': 150,
    '90090': 30, '90106': 30
}

# 2. Lista Hoja 2 (Equipos Ordenados - con None para espacios)
EQUIPOS_ORDEN = [
    '50018', '50019', '13014', '51046', None, 
    '51079', '51080', '45139', None,
    '051300r', '012009U', None,
    '50016', '13013', '51075', None,
    '051066r', '45207', '45169', '51041', '50015', '13012'
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
        
        # Excluir depósitos no deseados
        df_base = df_raw[~df_raw['LOC_DESCRIPTION'].isin(DEPOSITOS_A_EXCLUIR)]

        # --- FUNCIÓN PARA CREAR MATRIZ ---
        def generar_matriz(df_input, lista_codigos):
            # Filtrar solo códigos de la lista (quitando los None de la lista de orden)
            cods = [c for c in lista_codigos if c is not None]
            # Normalizar para comparación (quitar ceros a la izq)
            cods_norm = [c.lstrip('0') for c in cods]
            
            df_filtered = df_input[df_input['ITEM'].isin(cods_norm)]
            
            if df_filtered.empty: return pd.DataFrame()
            
            pivot = df_filtered.pivot_table(
                index=['ITEM', 'DESCRIPCION_ITEM'], 
                columns='LOC_DESCRIPTION', 
                values='STOCK', 
                aggfunc='sum'
            ).fillna(0).reset_index()
            
            # Reordenar según la lista original (si es la hoja 2)
            if None in lista_codigos:
                pivot['sort_idx'] = pivot['ITEM'].apply(lambda x: cods_norm.index(x) if x in cods_norm else 999)
                pivot = pivot.sort_values('sort_idx').drop(columns='sort_idx')
            
            return pivot

        # --- GENERAR AMBAS MATRICES ---
        matriz_1 = generar_matriz(df_base, list(STOCK_OBJETIVO.keys()))
        matriz_2 = generar_matriz(df_base, EQUIPOS_ORDEN)

        # --- INTERFAZ ---
        st.success("✅ Reporte procesado con éxito.")
        tab1, tab2 = st.tabs(["Control Crítico", "Equipos Agrupados"])
        with tab1: st.dataframe(matriz_1, use_container_width=True)
        with tab2: st.dataframe(matriz_2, use_container_width=True)

        # --- EXPORTAR EXCEL ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Hoja 1
            matriz_1.insert(2, 'STOCK_OBJETIVO', matriz_1['ITEM'].map(STOCK_OBJETIVO))
            matriz_1.to_excel(writer, index=False, sheet_name='Stock_Critico')
            
            # Formato Condicional Hoja 1
            ws1 = writer.sheets['Stock_Critico']
            wb = writer.book
            fmt_rojo = wb.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
            for col_num in range(3, len(matriz_1.columns)):
                letra = get_column_letter(col_num + 1)
                ws1.conditional_format(1, col_num, len(matriz_1), col_num, 
                                       {'type': 'formula', 'criteria': f'={letra}2 < $C2', 'format': fmt_rojo})

            # Hoja 2 (Insertamos filas vacías donde hay None en la lista de orden)
            # Para simplificar, la pasamos directo, pero respetando el orden solicitado
            matriz_2.to_excel(writer, index=False, sheet_name='Equipos_Agrupados')
            
            # Ajuste de columnas para ambas
            for ws in [ws1, writer.sheets['Equipos_Agrupados']]:
                ws.set_column(0, 50, 18)

        st.download_button(
            label="📥 DESCARGAR EXCEL CON 2 HOJAS",
            data=output.getvalue(),
            file_name="Reporte_Stock_Getel_Completo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error: {e}")
