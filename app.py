import streamlit as st
import pandas as pd
import io

# Configuración de página ancha
st.set_page_config(page_title="Matriz de Stock", layout="wide")

st.title("📊 Procesador de Inventario Total")
st.markdown("Subí el archivo TXT para generar la matriz completa automáticamente.")

archivo_subido = st.file_uploader("Subir Cloud_Report.txt", type=['txt'])

if archivo_subido:
    try:
        # 1. Leer archivo
        df = pd.read_csv(archivo_subido, sep=';', encoding='latin-1')
        df.columns = [c.strip() for c in df.columns]
        df['STOCK'] = pd.to_numeric(df['STOCK'], errors='coerce').fillna(0)

        # 2. CREAR MATRIZ AUTOMÁTICA (Sin selectores)
        # Esto pone los Códigos a la izquierda y cada Técnico en una columna diferente de forma automática
        matriz = df.pivot_table(
            index=['ITEM', 'DESCRIPCION_ITEM'], 
            columns='LOC_DESCRIPTION', 
            values='STOCK', 
            aggfunc='sum'
        ).fillna(0).reset_index()

        st.success(f"✅ Se han organizado {len(matriz.columns) - 2} columnas de inventario.")
        
        # 3. Vista previa de la tabla
        st.dataframe(matriz, use_container_width=True, hide_index=True)

        # 4. Generar Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            matriz.to_excel(writer, index=False, sheet_name='Stock_General')
        
        # 5. Botón de descarga
        st.download_button(
            label="📥 DESCARGAR EXCEL COMPLETO",
            data=output.getvalue(),
            file_name="Matriz_Stock_Completa.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error al procesar: {e}")
else:
    st.info("Esperando archivo TXT...")
