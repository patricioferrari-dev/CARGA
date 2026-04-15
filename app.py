import streamlit as st
import pandas as pd
import io

# Configuración básica
st.set_page_config(page_title="Consolidador Getel", layout="wide")

st.title("📊 Matriz de Stock Consolidada")

# Subida de archivo
archivo_subido = st.file_uploader("Subí el archivo TXT aquí", type=['txt'])

if archivo_subido:
    try:
        # 1. Leer el archivo con codificación para evitar errores de acentos
        df = pd.read_csv(archivo_subido, sep=';', encoding='latin-1')
        
        # Limpiar espacios en los nombres de las columnas
        df.columns = df.columns.str.strip()
        
        # 2. Asegurar que los datos sean procesables
        df['STOCK'] = pd.to_numeric(df['STOCK'], errors='coerce').fillna(0)
        df['LOC_DESCRIPTION'] = df['LOC_DESCRIPTION'].astype(str).str.strip()
        df['ITEM'] = df['ITEM'].astype(str).str.strip()

        # 3. CREAR LA MATRIZ TOTAL (Horizontal)
        # Esto pone ITEM y DESCRIPCION_ITEM a la izquierda
        # Y crea una columna por cada valor diferente en LOC_DESCRIPTION
        matriz = df.pivot_table(
            index=['ITEM', 'DESCRIPCION_ITEM'], 
            columns='LOC_DESCRIPTION', 
            values='STOCK', 
            aggfunc='sum'
        ).fillna(0).reset_index()

        st.success(f"✅ Se detectaron {len(matriz.columns) - 2} sub-inventarios.")
        
        # 4. Mostrar tabla en la web
        st.dataframe(matriz, use_container_width=True)

        # 5. Generar Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            matriz.to_excel(writer, index=False)
        
        st.download_button(
            label="📥 DESCARGAR EXCEL CON TODOS LOS TÉCNICOS",
            data=output.getvalue(),
            file_name="Stock_Consolidado_Getel.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Hubo un problema al procesar: {e}")
else:
    st.info("Por favor, cargá el archivo .txt para ver la matriz.")
