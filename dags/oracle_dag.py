import pandas as pd
import os
import cx_Oracle
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.oracle.hooks.oracle import OracleHook
from openpyxl import load_workbook

# Đảm bảo cx_Oracle sử dụng đúng mã hóa UTF-8
os.environ['NLS_LANG'] = 'AMERICAN_AMERICA.AL32UTF8'

# Hàm đảm bảo các chuỗi được chuyển đúng mã hóa Unicode
def ensure_unicode(df):
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(lambda x: str(x).encode('utf-8').decode('utf-8') if pd.notnull(x) else x)
    return df

# Hàm chuẩn hóa tên cột
def clean_column_name(col_name):
    cleaned_name = col_name.strip().replace(" ", "_")
    cleaned_name = ''.join(e for e in cleaned_name if e.isalnum() or e == '_')
    return cleaned_name.upper()

# Hàm xác định kiểu dữ liệu
def determine_column_type(col, df):
    numeric_cols = ['doanh_thu', 'don_gia', 'gia_von_hang_hoa']
    cleaned_col = clean_column_name(col)

    if pd.api.types.is_integer_dtype(df[col]):
        column_type = 'NUMBER(18, 0)'
    elif pd.api.types.is_float_dtype(df[col]):
        column_type = 'NUMBER(18, 2)'
    elif pd.api.types.is_datetime64_any_dtype(df[col]):
        column_type = 'DATE'
    elif cleaned_col.lower() in numeric_cols:
        column_type = 'NUMBER(18, 2)'
    elif df[col].apply(lambda x: isinstance(x, str) and any(ord(char) > 127 for char in str(x))).any():
        column_type = 'NVARCHAR2(500)'
    else:
        column_type = 'NVARCHAR2(255)'
    return column_type

# Hàm tạo bảng trong Oracle
def create_table(cursor, table_name, df):
    column_defs = []
    for col in df.columns:
        column_type = determine_column_type(col, df)
        cleaned_col = clean_column_name(col)
        column_defs.append(f"{cleaned_col} {column_type}")
    
    create_table_sql = f"CREATE TABLE {table_name} ({', '.join(column_defs)})"
    try:
        cursor.execute(create_table_sql)
        print(f"Bảng {table_name} đã được tạo thành công!")
    except cx_Oracle.DatabaseError as e:
        print(f"Lỗi khi tạo bảng {table_name}: {e}")

# Hàm chuyển đổi giá trị Pandas datetime sang Oracle datetime format
def convert_date_for_oracle(date_value):
    if pd.notnull(date_value):
        return date_value.strftime('%Y-%m-%d')
    return None

# Hàm escape dấu nháy đơn
def escape_quotes(value):
    if isinstance(value, str):
        return value.replace("'", "''")
    return value

# Hàm nhập dữ liệu vào bảng Oracle
def load_data_to_oracle(df, table_name, oracle_conn_id):
    oracle_hook = OracleHook(oracle_conn_id=oracle_conn_id)
    connection = oracle_hook.get_conn()
    cursor = connection.cursor()

    # Tạo bảng nếu chưa có
    create_table(cursor, table_name, df)

    for index, row in df.iterrows():
        cleaned_columns = ', '.join([clean_column_name(col) for col in row.index])
        values = []
        for col, value in row.items():
            column_type = determine_column_type(col, df)
            if pd.isnull(value):
                values.append('NULL')
            elif column_type == 'DATE':
                values.append(f"TO_DATE('{convert_date_for_oracle(value)}', 'YYYY-MM-DD')")
            elif column_type.startswith('NUMBER'):
                values.append(str(value))
            else:
                value = escape_quotes(str(value))
                values.append(f"N'{value}'")
        values_str = ', '.join(values)
        sql = f"INSERT INTO {table_name} ({cleaned_columns}) VALUES ({values_str})"

        try:
            cursor.execute(sql)
        except cx_Oracle.DatabaseError as e:
            print(f"Lỗi khi chèn dòng {index} vào {table_name}: {e}")

    connection.commit()
    cursor.close()
    connection.close()

# Hàm để xử lý từng file Excel
def process_kpi_template():
    file_path = 'dags/data/KPI Template.xlsx'  
    kpi_template_df = pd.read_excel(file_path, engine='openpyxl')
    kpi_template_df = ensure_unicode(kpi_template_df)
    load_data_to_oracle(kpi_template_df, 'KPI_TEMPLATE', 'oracle_conn_id')

def process_modeling_dax():
    file_path = 'dags/data/Modeling and DAX.xlsx'  
    modeling_dax_sheets = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
    for sheet_name, df in modeling_dax_sheets.items():
        if isinstance(df, pd.Series):
            df = df.to_frame()
        df = ensure_unicode(df)
        table_name = clean_column_name(sheet_name)
        load_data_to_oracle(df, table_name, 'oracle_conn_id')

# Thiết lập DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'start_date': datetime(2024, 10, 10),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'import_excel_to_oracle',
    default_args=default_args,
    description='Import dữ liệu từ Excel vào Oracle',
    schedule_interval=None,  # Chạy thủ công
    catchup=False,
)

# Task để xử lý từng file Excel
task_process_kpi_template = PythonOperator(
    task_id='process_kpi_template',
    python_callable=process_kpi_template,
    dag=dag,
)

task_process_modeling_dax = PythonOperator(
    task_id='process_modeling_dax',
    python_callable=process_modeling_dax,
    dag=dag,
)

# Thiết lập trình tự chạy
task_process_kpi_template >> task_process_modeling_dax
