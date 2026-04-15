import streamlit as st
import pandas as pd
import io

# Configuración ancha de página
st.set_page_config(page_title="Conversor Total Getel", layout="wide")

st.title("📊 Matriz de Stock Completa")
st.markdown("Subí el archivo y descargá el Excel con todos los inventarios en columnas.")

# 1. Subida de archivo
archivo_subido = st.file_uploader("Subir Cloud_Report.txt", type=['txt'])

if archivo_subido:
    try:
        # 2. Procesamiento
        df = pd.read_csv(archivo_subido, sep=';', encoding='latin-1')
        df.columns = [c.strip() for c in df.columns]
        df['STOCK'] = pd.to_numeric(df['STOCK'], errors='coerce').fillna(0)

        # 3. Crear Matriz Horizontal (Pivot)
        # Esto genera una columna por cada sub-inventario automáticamente
        matriz = df.pivot_table(
            index=['ITEM', 'DESCRIPCION_ITEM'], 
            columns='LOC_DESCRIPTION', 
            values='STOCK', 
            aggfunc='sum'
        ).fillna(0).reset_index()

        st.success(f"✅ Procesados {len(matriz.columns) - 2} inventarios correctamente.")
        
        # 4. Vista previa
        st.dataframe(matriz, use_container_width=True, hide_index=True)

        # 5. Generar Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            matriz.to_excel(writer, index=False, sheet_name='Stock_General')
        
        # 6. Botón de descarga
        st.download_button(
            label="📥 DESCARGAR EXCEL COMPLETO",
            data=output.getvalue(),
            file_name="Reporte_General_Stock.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error: {e}")
