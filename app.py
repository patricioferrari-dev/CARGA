import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Consolidador de Stock", layout="wide")

st.title("🚀 Generador de Matriz de Stock Total")
st.markdown("Subí el archivo TXT y descargá el Excel con todos los sub-inventarios juntos.")

archivo_subido = st.file_uploader("Subir Archivo TXT", type=['txt'])

if archivo_subido:
    try:
        # 1. Leer el archivo (usamos el separador ; del archivo original)
        df = pd.read_csv(archivo_subido, sep=';', encoding='latin-1')
        
        # 2. Limpieza de nombres de columnas (quita espacios invisibles)
        df.columns = [c.strip() for c in df.columns]
        
        # 3. Limpiar datos: Convertimos STOCK a número y quitamos espacios en los nombres de técnicos
        df['STOCK'] = pd.to_numeric(df['STOCK'], errors='coerce').fillna(0)
        df['LOC_DESCRIPTION'] = df['LOC_DESCRIPTION'].astype(str).str.strip()

        # 4. CREAR LA MATRIZ (La "Magia")
        # Filas: ITEM y DESCRIPCION_ITEM
        # Columnas: LOC_DESCRIPTION (Aquí aparecerán todos los técnicos: PEREZ, TOLEDO, etc.)
        matriz = df.pivot_table(
            index=['ITEM', 'DESCRIPCION_ITEM'], 
            columns='LOC_DESCRIPTION', 
            values='STOCK', 
            aggfunc='sum'
        ).fillna(0).reset_index()

        # 5. Mostrar resultado en la web
        st.success(f"✅ Se han procesado {len(matriz.columns) - 2} sub-inventarios correctamente.")
        st.dataframe(matriz, use_container_width=True)

        # 6. Crear el archivo Excel para descargar
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            matriz.to_excel(writer, index=False, sheet_name='MATRIZ_TOTAL')
            
            # Formatear el Excel (ancho de columnas)
            worksheet = writer.sheets['MATRIZ_TOTAL']
            for i, col in enumerate(matriz.columns):
                column_width = max(len(str(col)), 15)
                # Letra de la columna
                from openpyxl.utils import get_column_letter
                worksheet.column_dimensions[get_column_letter(i+1)].width = column_width

        # 7. Botón de descarga
        st.download_button(
            label="📥 DESCARGAR EXCEL CON TODOS LOS TÉCNICOS",
            data=output.getvalue(),
            file_name="Matriz_Stock_Consolidado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("Por favor, subí el archivo .txt para generar el reporte.")
