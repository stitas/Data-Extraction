from xlsxwriter import Workbook
import pandas as pd
import json
import io
import base64

# data = [{'text': [{'key': 'sender', 'value': 'From:\nDEMO - Sliced Invoices\nSuite 5A-1204\n123 Somewhere Street\nYour City AZ 12345\nadmin@slicedinvoices.com\n'}, {'key': 'receiver', 'value': 'To:\nTest Business\n123 Somewhere St\nMelbourne, VIC 3000\ntest@test.com\n'}, {'key': 'sender_email', 'value': 'admin@slicedinvoices.com\n'}], 'form': [{'key': 'Total\n', 'value': '$93.50\n'}, {'key': 'Order Number\n', 'value': '12345\n'}, {'key': 'Total Due\n', 'value': '$93.50\n'}], 'table': [{'table_as_json': {"(\'Invoice Number\',)":{"0":"Order Number","1":"Invoice Date","2":"Due Date","3":"Total Due"},"(\'INV-3337\',)":{"0":"12345","1":"January 25, 2016","2":"January 31, 2016","3":"$93.50"}}}, {'table_as_json': {"(\'Hrs\\/QtyServiceRate\\/Price\',)":{"0":"1.00Web DesignThis is a sample description...$85.00"},"(\'Adjust\',)":{"0":"0.00%"},"(\'Sub Total\',)":{"0":"$85.00"}}}, {'table_as_json': {"(\'1.00Web DesignThis is a sample description...$85.000.00%\',)":{"0":"Sub Total","1":"TaxPax","2":"Total"},"(\'$85.00\',)":{"0":"$85.00","1":"$8.50","2":"$93.50"}}}], 'filename': 'invoice_example.pdf'}]

def get_keys_text(data):
    keys = []
    for kvp in data['text']:
        keys.append(kvp['key'])
        
    return keys

def get_values_text(data):
    values = []
    for kvp in data['text']:
        values.append(kvp['value'])
        
    return values

def get_keys_form(data):
    keys = []
    for kvp in data['form']:
        if type(kvp) is list:
            for key in kvp:
                keys.append(key['key'])
        else:
            keys.append(kvp['key'])
            
    return keys

def get_values_form(data):
    values = []
    for kvp in data['form']:
        if type(kvp) is list:
            for value in kvp:
                values.append(value['value'])
        else:
            values.append(kvp['value'])

    return values

def get_tables(data):
    tables = []
    for table in data['table']:
        tables.append(table['table_as_df'])
        
    return tables

def get_text_df(data):
    keys = get_keys_text(data)
    values = get_values_text(data)
    df = pd.DataFrame()
    
    if len(keys) != 0 and len(values) != 0:
        d = {'KEYS': keys, 'VALUES':values}
        df = pd.DataFrame(data=d)

    return df

def get_form_df(data):
    keys = get_keys_form(data)
    values = get_values_form(data)
    df = pd.DataFrame()
    
    if len(keys) != 0 and len(values) != 0:
        d = {'KEYS': keys, 'VALUES':values}
        df = pd.DataFrame(data=d)
    
    return df
        
def create_excel_file(data):
    excel_buffer = io.BytesIO()
    writer = pd.ExcelWriter(excel_buffer, engine='xlsxwriter')
    
    row = 0
    last_col = 0
    
    if data['filename'] not in writer.book.sheetnames:
        ws = writer.book.add_worksheet(data['filename'])
        
    TITLE_STYLE = writer.book.add_format()
    text_df = get_text_df(data)
    form_df = get_form_df(data)
    table_dfs = get_tables(data)
    
    TITLE_STYLE.set_bold()
    TITLE_STYLE.set_font_size(20)
    
    ws.write_string(row,0,'TEXT FIELDS',TITLE_STYLE)
    row += 1
    
    text_df.to_excel(writer, sheet_name=data['filename'], startrow=row, index=False)
    row += text_df.shape[0] + 2
    
    ws.write_string(row,0,'FORM FIELDS',TITLE_STYLE)
    row += 1
    
    form_df.to_excel(writer, sheet_name=data['filename'], startrow=row, index=False)
    row += form_df.shape[0] + 2
    
    ws.write_string(row,0,'TABLE FIELDS',TITLE_STYLE)
    row += 1
    
    for table_df in table_dfs:
        table_df.to_excel(writer, sheet_name=data['filename'], startrow=row, index=False)
        if table_df.shape[1] > last_col:
            last_col = table_df.shape[1]
        row += table_df.shape[0] + 2
        
    writer.sheets[data['filename']].set_column(0, last_col, 25)
            
    writer.close() 
    
    excel_buffer.seek(0)
    
    return excel_buffer
    