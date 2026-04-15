import streamlit as st
import pandas as pd
import io

# Configuración ancha para ver mejor la tabla grande
st.set_page_config(page_title="Procesador Total Getel", page_icon="📈", layout="wide")

st.title("📈 Conversor Automático de Stock")
st.markdown("Subí tu archivo `.txt` y obtené el Excel con **todos** los sub-inventarios organizados por columnas.")

# 1. Zona de subida
archivo_subido = st.file_uploader("Arrastrá aquí el archivo Cloud_Report.txt", type=['txt'])

if archivo_subido:
    try:
        with st.spinner("Procesando matriz completa..."):
            # 2. Leer archivo con codificación correcta
            df = pd.read_csv(archivo_subido, sep=';', encoding='latin-1')
            df.columns = [c.strip() for c in df.columns]

            # 3. Limpiar datos de stock
            df['STOCK'] = pd.to_numeric(df['STOCK'], errors='coerce').fillna(0)

            # 4. CREAR LA MATRIZ TOTAL (PIVOT)
            # Esto pone los códigos a la izquierda y CADA técnico en una columna nueva
            matriz = df.pivot_table(
                index=['ITEM', 'DESCRIPCION_ITEM'], 
                columns='LOC_DESCRIPTION', 
                values='STOCK', 
                aggfunc='sum'
            ).fillna(0)

            # Convertimos el índice en columnas normales
            matriz_final = matriz.reset_index()

            # 5. Mostrar éxito y vista previa
            st.success(f"✅ Se procesaron {len(matriz_final.columns) - 2} técnicos/depósitos.")
            st.dataframe(matriz_final, use_container_width=True, hide_index=True)

            # 6. Crear el Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                matriz_final.to_excel(writer, index=False, sheet_name='Stock_General')
                
                # Ajuste de columnas para que no queden apretadas
                worksheet = writer.sheets['Stock_General']
                for i, col in enumerate(matriz_final.columns):
                    column_width = max(len(str(col)), 12) + 2
                    # Usamos una forma segura de obtener la letra de la columna (A, B, C...)
                    col_letter = pd.io.formats.excel.get_column_letter(i + 1)
                    worksheet.column_dimensions[col_letter].width = column_width

            # 7. BOTÓN ÚNICO DE DESCARGA
            st.download_button(
                label="📥 DESCARGAR EXCEL CON TODOS LOS TÉCNICOS",
                data=output.getvalue(),
                file_name="Reporte_General_Stock.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    except Exception as e:
        st.error(f"Error al procesar: {e}")
else:
    st.info("Esperando archivo TXT...")
