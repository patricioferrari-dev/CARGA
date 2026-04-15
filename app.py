import streamlit as st
import pandas as pd
import io

# Configuración de la página para que use todo el ancho
st.set_page_config(page_title="Conversor Stock Getel", page_icon="📈", layout="wide")

st.title("📈 Conversor Automático de Stock")
st.markdown("Subí tu archivo `.txt` y obtené la matriz completa de sub-inventarios en Excel.")

# 1. Zona de subida de archivo
archivo_subido = st.file_uploader("Arrastrá aquí el archivo Cloud_Report.txt", type=['txt'])

if archivo_subido:
    try:
        with st.spinner("Procesando matriz de stock..."):
            # 2. Leer el archivo TXT (Separador punto y coma)
            df = pd.read_csv(archivo_subido, sep=';', encoding='latin-1')
            
            # Limpiar nombres de columnas
            df.columns = [c.strip() for c in df.columns]

            # Convertir Stock a número por seguridad
            df['STOCK'] = pd.to_numeric(df['STOCK'], errors='coerce').fillna(0)

            # 3. CREAR LA MATRIZ AUTOMÁTICA
            # Filas: Código (ITEM) y Descripción
            # Columnas: El técnico o depósito (LOC_DESCRIPTION)
            # Valores: La cantidad (STOCK)
            matriz = df.pivot_table(
                index=['ITEM', 'DESCRIPCION_ITEM'], 
                columns='LOC_DESCRIPTION', 
                values='STOCK', 
                aggfunc='sum'
            ).fillna(0)

            # Ordenar por Código para que sea fácil de buscar
            matriz = matriz.reset_index()

            # 4. Mostrar resultado en pantalla
            st.success("✅ ¡Matriz generada con éxito!")
            st.dataframe(matriz, use_container_width=True, hide_index=True)

            # 5. Generar el Excel en memoria
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                matriz.to_excel(writer, index=False, sheet_name='Stock_General')
                
                # Ajuste automático de columnas en el Excel
                worksheet = writer.sheets['Stock_General']
                for i, col in enumerate(matriz.columns):
                    # Calculamos el ancho ideal basado en el texto más largo de la columna
                    max_len = max(matriz[col].astype(str).map(len).max(), len(col)) + 3
                    # Limitamos el ancho para que no sea excesivo (máximo 50)
                    column_width = min(max_len, 50)
                    # Convertimos el índice de columna a letra (A, B, C...)
                    col_letter = chr(65 + (i if i < 26 else 0)) # Manejo básico para A-Z
                    worksheet.column_dimensions[col_letter].width = column_width

            # 6. Botón de descarga automática
            st.download_button(
                label="📥 DESCARGAR EXCEL COMPLETO",
                data=output.getvalue(),
                file_name="Reporte_Stock_Getel_Procesado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    except Exception as e:
        st.error(f"Error técnico: {e}")
        st.info("Asegurate de que el archivo sea el TXT original de Getel (separado por ';').")
else:
    st.info("Esperando el archivo Cloud_Report para procesar...")
