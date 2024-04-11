from api import upload_blob, get_kvp, get_mime_type, upload_table, get_dataframes, delete_blob, get_file_name_from_gcs_uri, stream_pdf_page_as_image, get_pdf_page_count_gcs, process_document_binary, get_file_bytes, get_table_from_vertices, get_kvp_from_key, get_text_from_verticies, get_pdf_page_count
from models import db, User, Extractor, FormField, TableField, TextField, KeyValuePairs, Table, Text
from flask_login import login_user, logout_user, login_required, LoginManager, current_user
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from dotenv import load_dotenv, find_dotenv
from werkzeug.utils import secure_filename
from forms import LoginForm, RegisterForm
from export_data import create_excel_file
from flask_bcrypt import Bcrypt
import pandas as pd
import base64
import json
import os
import re
import io

load_dotenv(find_dotenv())

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

bcrypt = Bcrypt(app)

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

ALLOWED_EXTENSIONS = {'pdf','png','jpg'}
BUCKET_NAME = os.environ.get('BUCKET_NAME')
PROJECT_ID = os.environ.get('PROJECT_ID')
LOCATION = os.environ.get('LOCATION')
FORM_PARSER_PROCESSOR_ID = os.environ.get('FORM_PARSER_PROCESSOR_ID')
TEXT_PARSER_PROCESSOR_ID = os.environ.get('TEXT_PARSER_PROCESSOR_ID')
EXTRACTED_TABLES_BUCKET_NAME = os.environ.get('EXTRACTED_TABLES_BUCKET_NAME')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id_=user_id).first()

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('index')) #tikriuasiai pakeist reiks index
    return render_template('login.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@ app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/', methods=['GET','POST'])
@login_required
def index():
    if request.method == 'POST':
        if 'redirect_create_extractor' in request.form:
            return redirect(url_for('create_extractor'))
        if 'delete_extractor' in request.form:
            extractor_id = request.form.get('delete_extractor')
            Extractor.query.filter_by(id_=extractor_id).delete()
            db.session.commit()
        if 'upload_file' in request.form:
            file = request.files['sample_file']
                
            if file and allowed_file(file.filename):
                file.filename = secure_filename(file.filename)
                name = request.form['extractor_name']
                upload_blob(BUCKET_NAME, file, file.filename) # Upload file to gcs bucket
                sample_file_path = 'gs://' + BUCKET_NAME + '/' + file.filename
                extractor = Extractor(name, sample_file_path, current_user.get_id()) # Create extractor object 
                db.session.add(extractor) # Add extractor to db
                db.session.commit()
                
                return redirect(url_for('index'))
        
    data = Extractor.query.filter_by(user_id=current_user.get_id()).all()
    
    return render_template('index.html', data=data)

@app.route('/fields/<id_>', methods=['GET','POST'])
@login_required
def fields(id_):
    extractor = Extractor.query.filter_by(id_=id_).first()
    if current_user.get_id() == str(extractor.user_id):
        if request.method == 'POST':
            if 'delete_text' in request.form:
                text_field_id = request.form.get('delete_text')
                TextField.query.filter_by(id_=text_field_id).delete()
                Text.query.filter_by(text_field_id=text_field_id).delete()
                db.session.commit()
            if 'delete_form' in request.form:
                form_field_id = request.form.get('delete_form')
                FormField.query.filter_by(id_=request.form.get('delete_form')).delete()
                KeyValuePairs.query.filter_by(form_field_id=form_field_id).delete()
                db.session.commit()
            if 'delete_table' in request.form:
                table_field_id = request.form.get('delete_table')
                TableField.query.filter_by(id_=table_field_id).delete()
                Table.query.filter_by(table_field_id=table_field_id).delete()
                db.session.commit()
            if 'redirect_create_text_field' in request.form:
                return redirect(url_for('create_text_field', id_ = id_))
            if 'redirect_create_form_field' in request.form:
                return redirect(url_for('create_form_field', id_ = id_))
            if 'redirect_create_table_field' in request.form:
                return redirect(url_for('create_table_field', id_ = id_))
        form_fields = FormField.query.filter_by(extractor_id=id_).all()
        table_fields = TableField.query.filter_by(extractor_id=id_).all()
        text_fields = TextField.query.filter_by(extractor_id=id_).all()
        return render_template('fields.html', form_fields=form_fields, table_fields=table_fields, text_fields=text_fields, extractor=extractor)
    else:
        return render_template('error.html')
# -----------------------------------------------------------------------------------------------------------------------------------------
# CREATE && EDIT FORM FIELD
# -----------------------------------------------------------------------------------------------------------------------------------------
@app.route('/fields/create-form-field/<id_>', methods=['GET','POST'])
@login_required
def create_form_field(id_):
    extractor = Extractor.query.filter_by(id_=id_).first()
    if current_user.get_id() == str(extractor.user_id):
        if request.method == 'POST':
            if 'field_name_submit' in request.form:
                name = request.form['field_name']
                form_field = FormField(name, id_)
                print(form_field.id_)
                db.session.add(form_field)
                db.session.commit()
                
                gcs_uri = extractor.sample_file_path
                mime_type = get_mime_type(gcs_uri)
                data = get_kvp(PROJECT_ID,LOCATION,FORM_PARSER_PROCESSOR_ID,gcs_uri,mime_type)
        
                for kvp in data:
                    key_value_pair = KeyValuePairs(kvp['key'],kvp['key_confidence'],kvp['value'],kvp['value_confidence'],form_field.id_)
                    db.session.add(key_value_pair)
                    db.session.commit()
                
                return redirect(url_for('edit_kvp', id_ = id_, form_field_id = form_field.id_))
    else:
        return render_template('error.html')
    return render_template('create_form_field.html')

@app.route('/fields/form-field/edit-kvp/<id_>/<form_field_id>', methods=['GET','POST'])
@login_required
def edit_kvp(id_, form_field_id):
    extractor = Extractor.query.filter_by(id_=id_).first()
    if current_user.get_id() == str(extractor.user_id):
        if request.method == 'POST':
            if 'save_kvp' in request.form:
                return redirect(url_for('fields', id_=id_))
            if 'delete' in request.form:
                for i in request.form:
                    if i != 'delete':
                        KeyValuePairs.query.filter_by(id_=i).delete()
                        db.session.commit()
                    
                return redirect(url_for('edit_kvp', id_=id_, form_field_id=form_field_id))
            
        data = KeyValuePairs.query.filter_by(form_field_id=form_field_id).all()

        return render_template('edit_kvp.html', data=data)
    else:
        return render_template('error.html')

# -----------------------------------------------------------------------------------------------------------------------------------------
# CREATE && EDIT TABLE FIELD
# -----------------------------------------------------------------------------------------------------------------------------------------
@app.route('/fields/create-table-field/<id_>', methods=['GET','POST'])
@login_required
def create_table_field(id_):
    extractor = Extractor.query.filter_by(id_=id_).first()
    if current_user.get_id() == str(extractor.user_id):
        if request.method == 'POST':
            if 'field_name_submit' in request.form:
                name = request.form['field_name']
                table_field = TableField(name, id_)
                db.session.add(table_field)
                db.session.commit()
                
                gcs_uri = extractor.sample_file_path
                mime_type = get_mime_type(gcs_uri)
                paths, vertices = upload_table(PROJECT_ID,LOCATION,FORM_PARSER_PROCESSOR_ID,gcs_uri,mime_type,EXTRACTED_TABLES_BUCKET_NAME)
        
                for i in range(len(paths)):
                    table = Table('Table ' + str(i), paths[i], table_field.id_, vertices[i]['x1'], vertices[i]['y1'], vertices[i]['x2'], vertices[i]['y2'])
                    db.session.add(table)
                    db.session.commit()
                
                return redirect(url_for('edit_table', id_=id_, table_field_id = table_field.id_))
        
        return render_template('create_table_field.html')
    else:
        return render_template('error.html')


@app.route('/fields/table-field/edit_table/<id_>/<table_field_id>', methods=['GET','POST'])
@login_required
def edit_table(id_, table_field_id):
    extractor = Extractor.query.filter_by(id_=id_).first()
    if current_user.get_id() == str(extractor.user_id):
        if request.method == 'POST':
            if 'save_table' in request.form:
                return redirect(url_for('fields', id_=id_))
            if 'delete' in request.form:
                for i in request.form:
                    if i != 'delete':
                        table_id = i.replace('delete','')
                        table = Table.query.filter_by(id_=table_id).first()
                        path = table.path
                        name = get_file_name_from_gcs_uri(path)
                        delete_blob(EXTRACTED_TABLES_BUCKET_NAME,name)
                        Table.query.filter_by(id_=table_id).delete()
                        db.session.commit()
                        return redirect(url_for('edit_table', id_=id_, table_field_id=table_field_id))
        
        tables = Table.query.filter_by(table_field_id=table_field_id).all()
        paths = []
        
        for table in tables:
            paths.append(table.path)
        
        dataframes = get_dataframes(paths)
        
        return render_template('edit_table.html', dataframes=[re.sub(r'<tr.*>', '<tr>', df.to_html(classes='table')) for df in dataframes], tables=tables)
    else:
        return render_template('error.html')

# -----------------------------------------------------------------------------------------------------------------------------------------    
# CREATE && EDIT TEXT FIELD
# -----------------------------------------------------------------------------------------------------------------------------------------

@app.route('/fields/create-text-field/<id_>', methods=['GET','POST'])
@login_required
def create_text_field(id_):
    extractor = Extractor.query.filter_by(id_=id_).first()
    if current_user.get_id() == str(extractor.user_id):
        page = 0
        errors = ''
        if request.method == 'POST':
            if 'change_page' in request.form:
                page = int(request.form.get('page'))
            if 'image' in request.form:
                image_bytes = request.form.get('image')
                x1 = request.form.get('x1')
                y1 = request.form.get('y1')
                x2 = request.form.get('x2')
                y2 = request.form.get('y2')
                page = int(request.form.get('current_page'))
                if image_bytes != '':
                    image_bytes = get_file_bytes(image_bytes)
                    key = request.form.get('key')
                    text_field = TextField(key,id_)
                    db.session.add(text_field)
                    db.session.commit()
                    document = process_document_binary(PROJECT_ID,LOCATION,FORM_PARSER_PROCESSOR_ID,image_bytes,'image/png')
                    text = Text(document.text, text_field.id_ , x1, y1, x2, y2, page)
                    db.session.add(text)
                    db.session.commit()
                    return redirect(url_for('edit_text_field', id_=id_, text_field_id=text_field.id_))
                else:
                    errors = 'Select area'
        
        gcs_uri = extractor.sample_file_path
        filename = get_file_name_from_gcs_uri(gcs_uri)
        page_count = get_pdf_page_count_gcs(BUCKET_NAME, filename)
        image = stream_pdf_page_as_image(BUCKET_NAME, filename, page)
        
        return render_template('create_text_field.html', page_count=page_count, image=image, errors=errors, page=page)
    else:
        return render_template('error.html')
   
@app.route('/fields/create-text-field/<id_>/<text_field_id>', methods=['GET','POST']) 
@login_required
def edit_text_field(id_, text_field_id):
    extractor = Extractor.query.filter_by(id_=id_).first()
    if current_user.get_id() == str(extractor.user_id):
        if request.method == 'POST':
            if 'save' in request.form:
                return redirect(url_for('fields', id_=id_))
            if 'delete' in request.form:
                TextField.query.filter_by(id_=text_field_id).delete()
                Text.query.filter_by(text_field_id=text_field_id).delete()
                db.session.commit()
                return redirect(url_for('fields', id_=id_))
                
        
        text_field = TextField.query.filter_by(id_=text_field_id).first()
        text = Text.query.filter_by(text_field_id=text_field.id_).all()
        
        return render_template('edit_text_field.html', text=text)
    else:
        return render_template('error.html')

# -----------------------------------------------------------------------------------------------------------------------------------------    
# EXTRACT DATA
# -----------------------------------------------------------------------------------------------------------------------------------------
@app.route('/extract', methods=['GET','POST'])
@login_required
def extract():
    if request.method == 'POST':
        data = []
        extractor_id = int(request.form.get('extractors'))
        text_fields = TextField.query.filter_by(extractor_id=extractor_id).all()
        form_fields = FormField.query.filter_by(extractor_id=extractor_id).all()
        table_fields = TableField.query.filter_by(extractor_id=extractor_id).all()
        uploaded_files = request.files.getlist('files')
        for file in uploaded_files:
            if file and allowed_file(file.filename):
                file_data = file.read() 
                if get_pdf_page_count(file_data) > 15:
                    return render_template('error.html',error='PDF file pages can not exceed 15')
                text_data = []
                kvp_data = []
                table_data = []
                file.filename = secure_filename(file.filename)
                document = process_document_binary(PROJECT_ID,LOCATION,FORM_PARSER_PROCESSOR_ID,file_data,'application/pdf')
                for text_field in text_fields:
                    texts = Text.query.filter_by(text_field_id=text_field.id_).all()
                    for text in texts:
                        text_data.append(get_text_from_verticies(file_data,text_field.key,text.x1,text.y1,text.x2,text.y2,PROJECT_ID,LOCATION,TEXT_PARSER_PROCESSOR_ID,'image/jpeg',text.page)) 
                for form_field in form_fields:
                    kvps = KeyValuePairs.query.filter_by(form_field_id=form_field.id_).all()
                    for kvp in kvps:
                        kvp_list = get_kvp_from_key(document, kvp.key)
                        if(len(get_kvp_from_key(document, kvp.key)) == 1):
                            kvp_data.append(kvp_list[0])
                        else:
                            kvp_data.append(kvp_list)
                for table_field in table_fields:
                    tables = Table.query.filter_by(table_field_id=table_field.id_).all()
                    for table in tables:
                        table_data.append(get_table_from_vertices(document, table.x1, table.y1, table.x2, table.y2)) 
                data.append({'text':text_data, 'form':kvp_data, 'table':table_data, 'filename':file.filename})
                    
        session['extracted_data'] = data
        return redirect(url_for('export_data'))
    
    extractors = Extractor.query.filter_by(user_id=current_user.get_id())
    
    
    return render_template('extract.html', extractors=extractors)

@app.route('/extract/export', methods=['GET','POST'])
@login_required
def export_data():
    data = session['extracted_data']
    dataframes = []
    filenames = []
    # make df normal again
    for d in data:
        for df in d['table']:
            df = pd.read_json(io.StringIO(df['table_as_json']), dtype=False)
            col_list = []
            for col in df:
                col_list.append(col[2:-3])
            df.columns = col_list
            dataframes.append({'table_as_df':df})
        d['table'] = dataframes
    
    
    if request.method == 'POST':
        for filename in request.form:
            for file in data:
                if file['filename'].rsplit('.',1)[0] == filename:
                    excel_buffer = create_excel_file(file)
                    return send_file(excel_buffer, as_attachment=True, download_name=filename+'.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    for file in data:
        filenames.append(file['filename'].rsplit('.',1)[0])
    
    return render_template('export_data.html', filenames=filenames)
    
    

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        db.session.commit()
    app.run(debug=True, host='192.168.1.166')