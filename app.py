import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Procesador de Stock", layout="wide")

st.title("📊 Procesador de Inventario")
st.markdown("Subí el archivo `.txt` para generar el formato Excel personalizado.")

# 1. Subida de archivo
archivo_subido = st.file_uploader("Seleccioná el archivo TXT", type=['txt'])

if archivo_subido is not None:
    try:
        # 2. Lectura del archivo (usando ; como separador según tu ejemplo)
        df = pd.read_csv(archivo_subido, sep=';', encoding='latin-1')
        
        # Limpieza básica de nombres de columnas
        df.columns = [c.strip() for c in df.columns]

        st.success("Archivo cargado correctamente")

        # 3. Reglas de Negocio / Filtros
        st.subheader("Configuración del Reporte")
        
        # Filtro por Técnico (Columna LOC_DESCRIPTION en tu archivo)
        tecnicos = df['LOC_DESCRIPTION'].unique().tolist()
        tecnico_sel = st.selectbox("Seleccioná el Técnico para el reporte:", tecnicos)

        # Aplicar filtro
        df_filtrado = df[df['LOC_DESCRIPTION'] == tecnico_sel].copy()

        # Seleccionamos y ordenamos las columnas como en tu imagen
        # (Ajusté los nombres según el encabezado de tu .txt)
        columnas_finales = {
            'ITEM': 'Código',
            'DESCRIPCION_ITEM': 'Descripción del Artículo',
            'STOCK': 'Cantidad Stock',
            'DISPO': 'Disponible'
        }
        
        df_final = df_filtrado[list(columnas_finales.keys())].rename(columns=columnas_finales)

        # 4. Mostrar vista previa
        st.write(f"Vista previa para: **{tecnico_sel}**")
        st.dataframe(df_final, use_container_width=True)

        # 5. Generar Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Stock_Tecnico')
        
        st.download_button(
            label="📥 Descargar Excel Ordenado",
            data=buffer.getvalue(),
            file_name=f"Stock_{tecnico_sel.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        st.info("Asegurate de que el archivo use ';' como separador.")

else:
    st.info("Esperando archivo... Por favor, subí el reporte Cloud_Report.")