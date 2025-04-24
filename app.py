import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
import re
import io
import base64
import datetime
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
        st.write(f"Métricas encontradas en {meas_info_id}: {list(meas_types_by_info[meas_info_id].values())}")
    
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
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" class="btn btn-primary">Descargar CSV</a>'
    return href

def main():
    # Configuración de la aplicación
    st.sidebar.header("Configuración")
    debug_mode = st.sidebar.checkbox("Modo de depuración", value=False)
    
    # Uploader de archivos
    archivos = st.file_uploader("Select one or more XML files", type=["xml"], accept_multiple_files=True)
    
    # Lista para almacenar todos los resultados
    todos_resultados = []
    
    # Procesar los archivos cuando se suban
    if archivos:
        # Barra de progreso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, archivo in enumerate(archivos):
            try:
                status_text.text(f"Procesando: {archivo.name} ({i+1}/{len(archivos)})")
                
                # Analizar el archivo
                resultado = analyze_xml_file(archivo)
                todos_resultados.extend(resultado)
                
                # Actualizar barra de progreso
                progress_bar.progress((i + 1) / len(archivos))
                
            except Exception as e:
                st.error(f"Error al procesar {archivo.name}: {str(e)}")
                if debug_mode:
                    import traceback
                    st.error(traceback.format_exc())
        
        # Limpiar barra de progreso y texto de estado
        progress_bar.empty()
        status_text.empty()
        
        # Mostrar resultados en formato tabular
        if todos_resultados:
            # Crear DataFrame con todos los resultados
            df_resultados = pd.DataFrame(todos_resultados)
            # Filtrar solo filas donde 'Cell' contenga 'Cell' (ej: Cell1, Cell2)
            if not df_resultados.empty and 'Cell' in df_resultados.columns:
                df_resultados = df_resultados[df_resultados['Cell'].str.contains('Cell', na=False)]

            # Agregar columnas de KPIs DL R-BLER y UL R-BLER
            for col, num, den in [
                ("DL R-BLER", "TB.ResidualErrNbrDl", "TB.TotNbrDlInitial"),
                ("UL R-BLER", "TB.ResidualErrNbrUl", "TB.TotNbrUlInit")
            ]:
                if num in df_resultados.columns and den in df_resultados.columns:
                    df_resultados[col] = df_resultados.apply(
                        lambda row: (row[num]/row[den]*100) if row[den] not in [0, None, "", float("nan")] else 0,
                        axis=1
                    )
                else:
                    df_resultados[col] = None

            # Eliminar columnas que comiencen por 'TraceDU.'
            trace_cols = [col for col in df_resultados.columns if col.startswith('TraceDU.')]
            if trace_cols:
                df_resultados.drop(columns=trace_cols, inplace=True)

            # --- SOLO LOS KPIs SOLICITADOS ---
            # 1. RAR Success Rate (%) = (RACH.NumMsg2Att / RACH.NumMsg1Rcvd) * 100
            if all(c in df_resultados.columns for c in ["RACH.NumMsg2Att", "RACH.NumMsg1Rcvd"]):
                df_resultados["RAR Success Rate (%)"] = (
                    df_resultados["RACH.NumMsg2Att"].astype(float) / df_resultados["RACH.NumMsg1Rcvd"].astype(float) * 100
                ).replace([float('inf'), -float('inf')], 0).fillna(0)
            else:
                df_resultados["RAR Success Rate (%)"] = None

            # 2. RACH CBRA Success Rate (%) = ((RACH.NumMsg2SuccGrpA + RACH.NumMsg2SuccGrpB) / (RACH.NumMsg1RcvdGrpA + RACH.NumMsg1RcvdGrpB)) * 100
            if all(c in df_resultados.columns for c in ["RACH.NumMsg2SuccGrpA", "RACH.NumMsg2SuccGrpB", "RACH.NumMsg1RcvdGrpA", "RACH.NumMsg1RcvdGrpB"]):
                df_resultados["RACH CBRA Success Rate (%)"] = (
                    (df_resultados["RACH.NumMsg2SuccGrpA"].astype(float) + df_resultados["RACH.NumMsg2SuccGrpB"].astype(float)) /
                    (df_resultados["RACH.NumMsg1RcvdGrpA"].astype(float) + df_resultados["RACH.NumMsg1RcvdGrpB"].astype(float)) * 100
                ).replace([float('inf'), -float('inf')], 0).fillna(0)
            else:
                df_resultados["RACH CBRA Success Rate (%)"] = None

            # 3. RACH CFRA Success Rate (%) = (RACH.NumMsg2SuccDed / RACH.NumMsg1RcvdDed) * 100
            if all(c in df_resultados.columns for c in ["RACH.NumMsg2SuccDed", "RACH.NumMsg1RcvdDed"]):
                df_resultados["RACH CFRA Success Rate (%)"] = (
                    df_resultados["RACH.NumMsg2SuccDed"].astype(float) / df_resultados["RACH.NumMsg1RcvdDed"].astype(float) * 100
                ).replace([float('inf'), -float('inf')], 0).fillna(0)
            else:
                df_resultados["RACH CFRA Success Rate (%)"] = None

            # 4. RACH Success Rate (%) = (RACH.NumMsg2Succ / RACH.NumMsg1Rcvd) * 100
            if all(c in df_resultados.columns for c in ["RACH.NumMsg2Succ", "RACH.NumMsg1Rcvd"]):
                df_resultados["RACH Success Rate (%)"] = (
                    df_resultados["RACH.NumMsg2Succ"].astype(float) / df_resultados["RACH.NumMsg1Rcvd"].astype(float) * 100
                ).replace([float('inf'), -float('inf')], 0).fillna(0)
            else:
                df_resultados["RACH Success Rate (%)"] = None

            # 5. DRB Cell Throughput Uplink (kbps) = (DRB.CellVolUl / DRB.CellTimeUl) * 1000
            if all(c in df_resultados.columns for c in ["DRB.CellVolUl", "DRB.CellTimeUl"]):
                df_resultados["DRB Cell Throughput Uplink (kbps)"] = (
                    df_resultados["DRB.CellVolUl"].astype(float) / df_resultados["DRB.CellTimeUl"].astype(float) * 1000
                ).replace([float('inf'), -float('inf')], 0).fillna(0)
            else:
                df_resultados["DRB Cell Throughput Uplink (kbps)"] = None

            # 6. DRB Cell Throughput Downlink (kbps) = (DRB.CellVolDl / DRB.CellTimeDl) * 1000
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
                st.subheader("Resultados Extraídos:")
                
                # Mostrar columnas disponibles en modo depuración
                if debug_mode:
                    st.write("Columnas disponibles:", df_resultados.columns.tolist())
                
                # Aplicar estilos a la tabla para que se vea similar al ejemplo
                def highlight_cells(val):
                    return 'background-color: #f0f0f0'
                
                # Mostrar la tabla con estilos
                st.dataframe(df_resultados.style.applymap(highlight_cells, subset=pd.IndexSlice[:, ['Cell']]))
                
                # Botón de descarga
                st.markdown("### Descargar resultados")
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"metricas_extraidas_{timestamp}.csv"
                st.markdown(get_csv_download_link(df_resultados, filename), unsafe_allow_html=True)

                # Mostrar estadísticas
                st.subheader("Estadísticas:")
                st.write(f"Total de archivos procesados: {len(archivos)}")
                st.write(f"Total de celdas encontradas: {df_resultados['Cell'].nunique()}")
                st.write(f"Total de filas de datos: {len(df_resultados)}")

                # Gráficos de KPIs
                st.subheader("Gráficos de KPIs")
                kpi_cols = [
                    "RAR Success Rate (%)",
                    "RACH CBRA Success Rate (%)",
                    "RACH CFRA Success Rate (%)",
                    "RACH Success Rate (%)",
                    "DRB Cell Throughput Uplink (kbps)",
                    "DRB Cell Throughput Downlink (kbps)",
                    "DRB UE Throughput Uplink (kbps)",
                    "DRB UE Throughput Downlink (kbps)"
                ]
                available_kpis = [col for col in kpi_cols if col in df_resultados.columns]
                if available_kpis:
                    selected_kpis = st.multiselect(
                        "Selecciona los KPIs a graficar:",
                        options=available_kpis,
                        default=available_kpis[:2]  # Por defecto los dos primeros
                    )
                    if selected_kpis:
                        st.line_chart(df_resultados[selected_kpis])
                    else:
                        st.info("Selecciona al menos un KPI para visualizar el gráfico.")
                else:
                    st.warning("No hay KPIs disponibles para graficar.")
            else:
                st.warning("No se encontraron datos en los archivos XML subidos.")
        else:
            st.warning("No se pudieron procesar los archivos XML subidos.")

if __name__ == "__main__":
    main()
