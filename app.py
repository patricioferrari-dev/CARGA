import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Matriz Total de Stock", layout="wide")

st.title("📊 Reporte Consolidado de Stock")
st.markdown("Esta herramienta procesa el archivo completo y genera una columna por cada técnico automáticamente.")

# Subida del archivo TXT original
archivo_subido = st.file_uploader("Subí el reporte Cloud_Report (TXT)", type=['txt'])

if archivo_subido:
    try:
        # 1. Leer el archivo con el separador de Getel
        df = pd.read_csv(archivo_subido, sep=';', encoding='latin-1')
        
        # Limpiar espacios en los encabezados
        df.columns = [c.strip() for c in df.columns]
        
        # Asegurar que STOCK sea número
        df['STOCK'] = pd.to_numeric(df['STOCK'], errors='coerce').fillna(0)

        # 2. CREAR LA MATRIZ (Pivoteo)
        # Aquí es donde ocurre la magia: 
        # index: lo que va para abajo (Código y Descripción)
        # columns: lo que va para el costado (CADA técnico/depósito diferente)
        # values: la cantidad de stock
        matriz = df.pivot_table(
            index=['ITEM', 'DESCRIPCION_ITEM'], 
            columns='LOC_DESCRIPTION', 
            values='STOCK', 
            aggfunc='sum'
        ).fillna(0)

        # Reseteamos el índice para que ITEM y DESCRIPCION sean columnas
        matriz_final = matriz.reset_index()

        st.success(f"✅ ¡Éxito! Se encontraron {len(matriz_final.columns) - 2} sub-inventarios diferentes.")
        
        # 3. Vista previa en la web
        st.dataframe(matriz_final, use_container_width=True)

        # 4. Preparar la descarga del Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            matriz_final.to_excel(writer, index=False, sheet_name='Stock_General_Matriz')
            
            # Ajustar ancho de columnas automáticamente en el archivo Excel
            worksheet = writer.sheets['Stock_General_Matriz']
            for i, col in enumerate(matriz_final.columns):
                # Calculamos el largo del texto más largo en esa columna
                max_len = max(matriz_final[col].astype(str).map(len).max(), len(str(col))) + 2
                # Convertimos el índice de columna a letra (A, B, C...)
                col_letter = pd.io.formats.excel.get_column_letter(i + 1)
                worksheet.column_dimensions[col_letter].width = min(max_len, 50)

        # 5. Botón de descarga único
        st.download_button(
            label="📥 DESCARGAR MATRIZ COMPLETA (EXCEL)",
            data=output.getvalue(),
            file_name="Matriz_Stock_Getel.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error al procesar: {e}")
        st.info("Verificá que el archivo subido sea el .txt separado por ';'")
else:
    st.info("Esperando el archivo Cloud_Report para procesar todos los inventarios...")
