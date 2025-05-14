import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
import re
import io
import base64
import datetime

def convert_time_format(time_str):
    try:
        dt = datetime.datetime.strptime(time_str, "%Y%m%dT%H%M%S")
        return dt.strftime("%Y/%m/%d %H:%M:%S")
    except Exception:
        return time_str
import os
from typing import Dict, List, Any, Optional, Tuple

# Configuración de la página
st.set_page_config(page_title="DU XML Metrics Analyzer", layout="wide")

# Título y descripción
st.title("DU XML Metrics Analyzer")
st.write("Upload XML files to extract and align metrics per cell.")

@st.cache_data
def parse_xml_file(xml_file) -> Tuple[ET.Element, str]:
    """
    Parsea un archivo XML y devuelve el elemento raíz y el nombre del archivo.
    Utiliza caché para mejorar el rendimiento.
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        nombre_archivo = xml_file.name
        return root, nombre_archivo
    except Exception as e:
        st.error(f"Error al parsear el archivo {xml_file.name}: {str(e)}")
        return None, ""

def extract_meas_types(root: ET.Element) -> Dict[str, Dict[str, str]]:
    """
    Extrae los tipos de medición (measTypes) del XML y los organiza por su atributo 'p'.
    
    Args:
        root: Elemento raíz del XML
        
    Returns:
        Diccionario con los tipos de medición organizados por measInfo y atributo 'p'
    """
    meas_types_by_info = {}
    all_metrics = []
    
    # Buscar todos los elementos measInfo
    for i, meas_info in enumerate(root.findall(".//{*}measInfo")):
        meas_info_id = f"measInfo_{i+1}"
        meas_types_by_info[meas_info_id] = {}
        
        # Buscar todos los measTypes dentro de este measInfo
        for mtype in meas_info.findall(".//{*}measType"):
            if 'p' in mtype.attrib:
                meas_types_by_info[meas_info_id][mtype.attrib['p']] = mtype.text
                all_metrics.append(mtype.text)
        
        # Imprimir los tipos de medición encontrados para depuración
        st.write(f"Metrics found in {meas_info_id}: {list(meas_types_by_info[meas_info_id].values())}")
    
    # Mostrar todas las métricas encontradas
    st.write(f"Total de métricas encontradas: {len(all_metrics)}")
    st.write(f"Lista de métricas: {all_metrics}")
    
    return meas_types_by_info

def extract_gran_period(root: ET.Element) -> Dict[str, str]:
    """
    Extrae información del período de granularidad del XML.
    
    Args:
        root: Elemento raíz del XML
        
    Returns:
        Diccionario con información del período de granularidad
    """
    gran_period = {
        "duration": "900",  # Valor por defecto
        "endTime": ""       # Valor por defecto
    }
    
    # Buscar elementos de tiempo
    for elem in root.findall(".//{*}granPeriod"):
        if 'duration' in elem.attrib:
            gran_period["duration"] = elem.attrib['duration']
        if 'endTime' in elem.attrib:
            gran_period["endTime"] = elem.attrib['endTime']
    
    return gran_period

def extract_cell_data(root: ET.Element, meas_types_by_info: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
    """
    Extrae datos por celda del XML.
    
    Args:
        root: Elemento raíz del XML
        meas_types_by_info: Diccionario con los tipos de medición
        
    Returns:
        Diccionario con datos por celda
    """
    cell_data = {}
    
    # Crear un conjunto de todas las métricas disponibles
    all_metrics = set()
    for meas_info_id, metrics in meas_types_by_info.items():
        for p, metric_name in metrics.items():
            all_metrics.add(metric_name)
    
    # Buscar todos los elementos measInfo
    for i, meas_info in enumerate(root.findall(".//{*}measInfo")):
        meas_info_id = f"measInfo_{i+1}"
        meas_types = meas_types_by_info.get(meas_info_id, {})
        
        # Buscar todos los measValues dentro de este measInfo
import re
import xml.etree.ElementTree as ET

def parse_measdata(xml_file):
    ns = {'ns': 'http://www.3gpp.org/ftp/specs/archive/28_series/28.550#measData'}
    tree = ET.parse(xml_file)
    root = tree.getroot()
    data = []
    source_name = ""
    # Obtener el nombre del archivo XML
    xml_filename = getattr(xml_file, 'name', '')
    # Buscar SourceName si existe en el header
    file_header = root.find('.//ns:fileHeader', ns)
    if file_header is not None:
        sender = file_header.find('.//ns:senderName', ns)
        if sender is not None:
            source_name = sender.text
    for measInfo in root.findall('.//ns:measInfo', ns):
        # Extraer métricas
        measTypes_elem = measInfo.find('ns:measTypes', ns)
        if measTypes_elem is None or not measTypes_elem.text:
            continue
        metrics = measTypes_elem.text.strip().split()
        # Extraer periodo
        granPeriod = measInfo.find('ns:granPeriod', ns)
        duration = granPeriod.find('ns:duration', ns).text if granPeriod is not None else ''
        endTime = granPeriod.find('ns:endTime', ns).text if granPeriod is not None else ''
        # Extraer resultados por celda
        for measValue in measInfo.findall('ns:measValue', ns):
            measObjLdn = measValue.attrib.get('measObjLdn', '')
            # Solo incluir si el ME-Id es exactamente uno de los dos permitidos
            allowed_me_ids = [
                'ME-Id=DU-at2200-eab86b009f5d-1,Cell=1',
                'ME-Id=DU-at2200-eab86b009f5d-1,Cell=2'
            ]
            if measObjLdn not in allowed_me_ids:
                continue
            cell_match = re.search(r'Cell=([^,]+)', measObjLdn)
            cell_id = f"Cell{cell_match.group(1)}" if cell_match else measObjLdn
            measResults_elem = measValue.find('ns:measResults', ns)
            if measResults_elem is None or not measResults_elem.text:
                continue
            results = measResults_elem.text.strip().split()
            # Extraer serial del measObjLdn (lo que sigue a '-eab85c' y termina en '-')
            serial_match = re.search(r'-eab85c([0-9a-fA-F]+)-', measObjLdn)
            serial = f'-eab85c{serial_match.group(1)}-' if serial_match else ''
            row = {
                'xml_filename': xml_filename,
                'serial': serial,
                'SourceName': source_name,
                'granPeriodDuration': duration,
                'granPeriodEndTime': endTime,
                # Manejo robusto de formatos de fecha/hora
                'granPeriodEndTime_fmt': (
                    datetime.datetime.strptime(endTime, '%Y%m%dT%H%M%S')
                    if len(endTime) == 15 else (
                        datetime.datetime.strptime(endTime, '%Y-%m-%dT%H:%M:%S.%fZ')
                        if 'T' in endTime and '-' in endTime else endTime
                    )
                ),
                'granPeriodEndTime_fmt_str': convert_time_format(endTime),
                'Cell': cell_id
            }
            for metric, value in zip(metrics, results):
                try:
                    value = float(value)
                    if value.is_integer():
                        value = int(value)
                except Exception:
                    pass
                row[metric] = value
            data.append(row)
    return data

def analyze_xml_file(xml_file):
    """
    Analiza un archivo XML y extrae los datos relevantes y todas las métricas alineadas.
    Args:
        xml_file: Archivo XML a analizar
    Returns:
        Lista de diccionarios con los datos extraídos (uno por celda)
    """
    return parse_measdata(xml_file)

def get_csv_download_link(df: pd.DataFrame, filename: str = "datos_extraidos.csv") -> str:
    """
    Genera un enlace para descargar el DataFrame como CSV.
    
    Args:
        df: DataFrame a descargar
        filename: Nombre del archivo CSV
        
    Returns:
        Enlace HTML para descargar el CSV
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}">Descargar CSV</a>'

def convert_time_format(time_str):
    try:
        dt = datetime.datetime.strptime(time_str, "%Y%m%dT%H%M%S")
        return dt.strftime("%Y/%m/%d %H:%M:%S")
    except Exception:
        return time_str

def main():
    archivos = st.file_uploader("Upload XML files", type=['xml'], accept_multiple_files=True)
    debug_mode = st.sidebar.checkbox("Debug mode", value=False)
    cell_options = ['cell1', 'cell2']
    selected_cells = st.sidebar.multiselect(
        "Select cells to include:", options=cell_options, default=cell_options
    )
    if archivos:
        df_resultados = pd.concat([pd.DataFrame(analyze_xml_file(archivo)) for archivo in archivos], ignore_index=True)

        # Apply cell filter if user selected any
        if selected_cells and 'Cell' in df_resultados.columns:
            df_resultados = df_resultados[df_resultados['Cell'].str.lower().str.contains('|'.join(selected_cells))]
        if not df_resultados.empty and 'Cell' in df_resultados.columns:
            # Exclude metadata and derived KPI columns
            metadata_cols = ['Cell', 'Time', 'Fecha', 'Hora', 'datetime']
            derived_kpis = [
                "DL R-BLER", "UL R-BLER",
                "RAR Success Rate (%)", "RACH CBRA Success Rate (%)", "RACH CFRA Success Rate (%)", "RACH Success Rate (%)",
                "DRB Cell Throughput Uplink (kbps)", "DRB Cell Throughput Downlink (kbps)",
                "DRB UE Throughput Uplink (kbps)", "DRB UE Throughput Downlink (kbps)"
            ]
        if all(c in df_resultados.columns for c in ["DRB.CellVolDl", "DRB.CellTimeDl"]):
            df_resultados["DRB Cell Throughput Downlink (kbps)"] = (
                df_resultados["DRB.CellVolDl"].astype(float) / df_resultados["DRB.CellTimeDl"].astype(float) * 1000
            ).replace([float('inf'), -float('inf')], 0).fillna(0)
        else:
            df_resultados["DRB Cell Throughput Downlink (kbps)"] = None

        # 7. DRB UE Throughput Uplink (kbps) = 1000.0 * (DRB.UEVolUl / DRB.UETimeUl)
        if all(c in df_resultados.columns for c in ["DRB.UEVolUl", "DRB.UETimeUl"]):
            df_resultados["DRB UE Throughput Uplink (kbps)"] = (
                1000.0 * (df_resultados["DRB.UEVolUl"].astype(float) / df_resultados["DRB.UETimeUl"].astype(float))
            ).replace([float('inf'), -float('inf')], 0).fillna(0)
        else:
            df_resultados["DRB UE Throughput Uplink (kbps)"] = None

        # 8. DRB UE Throughput Downlink (kbps) = 1000.0 * (DRB.UEVolDl / DRB.UETimeDl)
        if all(c in df_resultados.columns for c in ["DRB.UEVolDl", "DRB.UETimeDl"]):
            df_resultados["DRB UE Throughput Downlink (kbps)"] = (
                1000.0 * (df_resultados["DRB.UEVolDl"].astype(float) / df_resultados["DRB.UETimeDl"].astype(float))
            ).replace([float('inf'), -float('inf')], 0).fillna(0)
        else:
            df_resultados["DRB UE Throughput Downlink (kbps)"] = None

        if not df_resultados.empty:
            # Mostrar tabla en formato similar al ejemplo
            st.subheader("Extracted Results:")
            
            # Mostrar columnas disponibles en modo depuración
            if debug_mode:
                st.write("Available columns:", df_resultados.columns.tolist())
            
            # Aplicar estilos a la tabla para que se vea similar al ejemplo
            def highlight_cells(val):
                return 'background-color: #f0f0f0'
            
            # Mostrar la tabla con todos los contadores/columnas, rellenando NaN con cero para visualización
            st.dataframe(df_resultados.fillna(0))
            # If you want to show highlighting as a static table, uncomment the next line:
            # st.table(df_resultados.style.applymap(highlight_cells, subset=pd.IndexSlice[:, ['Cell']]))
            
            # Botón de descarga
            st.markdown("### Download results")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"extracted_metrics_{timestamp}.csv"
            st.markdown(get_csv_download_link(df_resultados, filename), unsafe_allow_html=True)

            # Mostrar estadísticas
            st.subheader("Statistics:")
            st.write(f"Total files processed: {len(archivos)}")
            st.write(f"Total cells found: {df_resultados['Cell'].nunique()}")

            # Gráficos de KPIs
            st.subheader("KPI Charts")
            # Generar dinámicamente la lista de KPIs a partir de las columnas del DataFrame
            exclude_cols = [
                'Cell', 'granPeriodEndTime_fmt_str', 'granPeriodEndTime', 'granPeriodDuration',
                'xml_filename', 'serial', 'SourceName', 'Time', 'Fecha', 'Hora', 'datetime'
            ]
            available_kpis = [col for col in df_resultados.columns if col not in exclude_cols]
            if available_kpis:
                selected_kpis = st.multiselect(
                    "Select KPIs to plot:",
                    options=available_kpis,
                    default=available_kpis[:min(5, len(available_kpis))]  # Default: primeros 5
                )
                if selected_kpis:
                    import altair as alt
                    kpi_data = df_resultados[['granPeriodEndTime_fmt_str', 'Cell'] + selected_kpis].copy()
                    kpi_data = kpi_data.reset_index(drop=True)
                    kpi_data['granPeriodEndTime_fmt_str'] = pd.to_datetime(kpi_data['granPeriodEndTime_fmt_str'], errors='coerce')
                    long_kpi_df = kpi_data.melt(id_vars=['granPeriodEndTime_fmt_str', 'Cell'], value_vars=selected_kpis,
                                                var_name='KPI', value_name='Value')
                    base_colors = [
                        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
                    ]
                    color_list = (base_colors * ((len(selected_kpis) // len(base_colors)) + 1))[:len(selected_kpis)]
                    kpi_chart = alt.Chart(long_kpi_df).mark_line(point=alt.OverlayMarkDef()).encode(
                        x=alt.X('granPeriodEndTime_fmt_str:T', title='Date/Time', axis=alt.Axis(labelAngle=-45, format='%Y-%m-%d %H:%M:%S')),
                        y=alt.Y('Value:Q', title='Value'),
                        color=alt.Color('KPI:N', scale=alt.Scale(domain=selected_kpis, range=color_list), legend=alt.Legend(title='KPI', orient='right')),
                        tooltip=['Cell', 'KPI', 'Value', 'granPeriodEndTime_fmt_str']
                    ).properties(width=900, height=420, title='Time evolution of selected KPIs')
                    st.altair_chart(kpi_chart, use_container_width=True)
                else:
                    st.info("Select at least one KPI to display the chart.")
            else:
                st.warning("No KPIs available to plot.")
                st.warning("No se encontraron datos en los archivos XML subidos.")
        else:
            st.warning("No se pudieron procesar los archivos XML subidos.")

if __name__ == "__main__":
    main()
