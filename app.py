import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Procesador Matrix Getel", page_icon="📊", layout="wide")

st.title("📊 Reporte de Stock por Sub-Inventario")
st.markdown("Este procesador organiza los códigos verticalmente y los sub-inventarios horizontalmente.")

archivo_subido = st.file_uploader("Subir Cloud_Report (TXT)", type=['txt'])

if archivo_subido:
    try:
        # 1. Leer el archivo
        df = pd.read_csv(archivo_subido, sep=';', encoding='latin-1')
        df.columns = [c.strip() for c in df.columns]

        # 2. Crear la Matriz (Pivot Table)
        # Filas: Código y Descripción
        # Columnas: LOC_DESCRIPTION (Técnicos/Sub-inventarios)
        # Valores: STOCK
        
        # Primero limpiamos los datos para evitar errores
        df['STOCK'] = pd.to_numeric(df['STOCK'], errors='coerce').fillna(0)
        
        matriz_stock = df.pivot_table(
            index=['ITEM', 'DESCRIPCION_ITEM'], 
            columns='LOC_DESCRIPTION', 
            values='STOCK', 
            aggfunc='sum'
        ).fillna(0) # Rellenamos con 0 donde un técnico no tiene ese material

        # Resetear el índice para que ITEM y DESCRIPCION sean columnas normales
        matriz_final = matriz_stock.reset_index()

        # 3. Mostrar Vista Previa
        st.write("### Vista previa del Excel:")
        st.dataframe(matriz_final, use_container_width=True)

        # 4. Generar el Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            matriz_final.to_excel(writer, index=False, sheet_name='Reporte_General')
            
            # Auto-ajuste de columnas básico
            worksheet = writer.sheets['Reporte_General']
            for i, col in enumerate(matriz_final.columns):
                column_len = max(matriz_final[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.column_dimensions[chr(65 + i)].width = column_len

        # 5. Descarga
        st.download_button(
            label="📥 Descargar Excel Matriz de Stock",
            data=output.getvalue(),
            file_name="Reporte_General_Stock.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Hubo un error al procesar la matriz: {e}")
else:
    st.info("Subí el archivo para generar la tabla comparativa.")
