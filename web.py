from flask import Flask, render_template, request, redirect, url_for, flash, session
from waitress import serve
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash, generate_password_hash
import os
from werkzeug.utils import secure_filename
from datetime import datetime


app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#koneksi
app.secret_key = 'bebasapasaja'
app.config['MYSQL_HOST'] ='localhost'
app.config['MYSQL_USER'] ='root'
app.config['MYSQL_PASSWORD'] =''
app.config['MYSQL_DB'] ='khazzanah x sahla syari'
mysql = MySQL(app)

@app.route('/')
def index():
    if 'loggedin' in session:
        return redirect(url_for('login'))
    else:
        flash('Harap Login terlebih dahulu', 'danger')
        return redirect(url_for('dashboard'))

#registrasi
@app.route('/registrasi', methods=('GET','POST'))
def registrasi():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        #cek username atau email
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM tb_users WHERE username=%s OR email=%s',(username, email, ))
        akun = cursor.fetchone()
        if akun is None:
            cursor.execute('INSERT INTO tb_users VALUES (NULL, %s, %s, %s)', (username, email, generate_password_hash(password)))
            mysql.connection.commit()
            flash('Registrasi Berhasil','success')
        else :
            flash('Username atau email sudah ada','danger')
    return render_template('registrasi.html')

#login
@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        #cek data username
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM tb_users WHERE email=%s',(email, ))
        akun = cursor.fetchone()
        if akun is None:
            flash('Login Gagal, Cek Username Anda','danger')
        elif not check_password_hash(akun[3], password):
            flash('Login gagal, Cek Password Anda', 'danger')
        else:
            session['loggedin'] = True
            session['username'] = akun[1]
            return redirect(url_for('dashboard'))
    return render_template('login.html')

#logout
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        # Tampilkan halaman dashboard
        return render_template('dashboard.html')

    else:
        flash('Harap Login terlebih dahulu', 'danger')
        return redirect(url_for('login'))




def hitung_jumlah_akhir(nama_barang):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT Jumlah_Akhir FROM perlegkapan WHERE Nama_Barang = %s ORDER BY Tanggal DESC LIMIT 1", (nama_barang,))
    data = cursor.fetchone()
    cursor.close()

    if data:
        return data[0]
    else:
        return 0

@app.route("/masterperlengkapan")
def masterperlengkapan():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM perlegkapan")
    data = cursor.fetchall()
    cursor.close()
    return render_template('masterperlengkapan.html',menu='master', submenu='perlengkapan', data=data)

@app.route('/formperlengkapan')
def form_perlengkapan():
    return render_template('formperlengkapan.html')

@app.route('/simpan_perlengkapan', methods=['POST'])
def simpan_perlengkapan():
    if request.method == 'POST':
        tanggal = request.form['Tanggal']
        nama_barang = request.form['Nama_Barang']
        satuan = request.form['Satuan']
        jumlah_awal = int(request.form['Jumlah_Awal'])
        barang_masuk = int(request.form['Barang_Masuk'])
        barang_keluar = int(request.form['Barang_Keluar'])

        jumlah_awal = hitung_jumlah_akhir(nama_barang)
        jumlah_akhir = jumlah_awal + barang_masuk - barang_keluar

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO perlegkapan (Tanggal, Nama_Barang, Satuan, Jumlah_Awal, Barang_Masuk, Barang_Keluar, Jumlah_Akhir) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (tanggal, nama_barang, satuan, jumlah_awal, barang_masuk, barang_keluar, jumlah_akhir))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('masterperlengkapan'))
    
@app.route('/hapusperlengkapan', methods=['POST', 'GET'])
def hapusperlengkapan():
    if request.method == 'POST':
        tanggal = request.form['Tanggal']
        nama_barang = request.form['Nama_Barang']
 
        tanggal = datetime.strptime(tanggal, '%Y-%m-%d').strftime('%Y-%m-%d')
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM perlegkapan WHERE Tanggal=%s AND Nama_Barang=%s", (tanggal, nama_barang))
        mysql.connection.commit()
        return redirect(url_for('masterperlengkapan'))

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM perlegkapan')
    data = cursor.fetchall()
    return render_template('hapusperlengkapan.html', data=data)






@app.route("/mastersupplier")
def mastersupplier():
    cur = mysql.connection.cursor()
    cur.execute("Select * From supplier")
    data = cur.fetchall()
    cur.close()
    return render_template('mastersupplier.html',menu='master', submenu='supplier', data=data)

@app.route("/formsupplier")
def formsupplier():
    return render_template('formsupplier.html',menu='master', submenu='supplier')

@app.route("/simpansupplier", methods=["POST"])
def simpansupplier ():
    Nama = request.form['Nama']
    Alamat = request.form['Alamat']
    Kode_Pos = request.form['Kode_Pos']
    No_tlp = request.form['No_tlp']
    Deskripsi = request.form['Deskripsi']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO supplier(Nama, Alamat, Kode_Pos, No_tlp, Deskripsi) VALUES(%s,%s,%s,%s,%s)",
                (Nama, Alamat, Kode_Pos, No_tlp, Deskripsi))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('mastersupplier'))

@app.route('/update_supplier', methods=['GET', 'POST'])
def update_supplier():
    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        Nama = request.form['Nama']
        Alamat = request.form['Alamat']
        Kode_Pos = request.form['Kode_Pos']
        No_tlp = request.form['No_tlp']
        Deskripsi = request.form['Deskripsi']
        cur = mysql.connection.cursor()
        cursor.execute('UPDATE supplier SET Alamat=%s, Kode_Pos=%s, No_tlp=%s, Deskripsi=%s WHERE Nama=%s',
                       (Alamat, Kode_Pos, No_tlp, Deskripsi, Nama))
        mysql.connection.commit()
        return redirect(url_for('mastersupplier'))

    cursor.execute('SELECT * FROM supplier')
    data = cursor.fetchall()
    return render_template('update_supplier.html', data=data)

@app.route('/hapussupplier', methods=['POST', 'GET'])
def hapussupplier():
    if request.method == 'POST':
        Nama = request.form['Nama']
        Alamat = request.form['Alamat']
        Kode_Pos = request.form['Kode_Pos']

        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM supplier WHERE Nama=%s AND Alamat=%s AND Kode_Pos=%s", 
                    (Nama, Alamat, Kode_Pos))
        mysql.connection.commit()
        return redirect(url_for('mastersupplier'))

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM supplier')
    data = cursor.fetchall()
    return render_template('hapussupplier.html', data=data)




@app.route("/masterpengiriman")
def masterpengiriman():
    cur = mysql.connection.cursor()
    cur.execute("Select * From pengiriman")
    pengiriman = cur.fetchall()
    cur.close()
    return render_template('masterpengiriman.html',menu='master', submenu='pengiriman', data=pengiriman)

@app.route("/formpengiriman")
def formpengiriman():
    return render_template('formpengiriman.html',menu='master', submenu='pengiriman')

@app.route("/simpan_pengiriman", methods=["POST"])
def simpan_pengiriman ():
    Tanggal = request.form['Tanggal']
    Nama_Pelanggan = request.form['Nama_Pelanggan']
    Nama_Produk = request.form['Nama_Produk']
    Kategori = request.form['Kategori']
    Ekspedisi = request.form['Ekspedisi']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO pengiriman(Tanggal, Nama_Pelanggan, Nama_Produk, Kategori, Ekspedisi) VALUES(%s,%s,%s,%s,%s)",
                (Tanggal, Nama_Pelanggan, Nama_Produk, Kategori, Ekspedisi))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('masterpengiriman'))

@app.route('/update_pengiriman', methods=['GET', 'POST'])
def update_pengiriman():
    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        Tanggal = request.form['Tanggal']
        Nama_Pelanggan = request.form['Nama_Pelanggan']
        Nama_Produk = request.form['Nama_Produk']
        Kategori = request.form['Kategori']
        Ekspedisi = request.form['Ekspedisi']

        cur = mysql.connection.cursor()
        cursor.execute('UPDATE pengiriman SET Tanggal=%s, Nama_Produk=%s, Kategori=%s, Ekspedisi=%s WHERE Nama_Pelanggan=%s AND Tanggal=%s',
                       (Tanggal, Nama_Produk, Kategori, Ekspedisi, Nama_Pelanggan, Tanggal))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('masterpengiriman'))

    cursor.execute('SELECT * FROM pengiriman')
    data = cursor.fetchall()
    return render_template('update_pengiriman.html', data=data)

@app.route('/hapuspengiriman', methods=['POST', 'GET'])
def hapuspengiriman():
    if request.method == 'POST':
        Tanggal = request.form['Tanggal']
        Nama_Pelanggan = request.form['Nama_Pelanggan']

        tanggal = datetime.strptime(Tanggal, '%Y-%m-%d').strftime('%Y-%m-%d')
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM pengiriman WHERE Tanggal=%s AND Nama_Pelanggan=%s", (Tanggal, Nama_Pelanggan))
        mysql.connection.commit()
        return redirect(url_for('masterpengiriman'))

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM pengiriman')
    data = cursor.fetchall()
    return render_template('hapuspengiriman.html', data=data)




@app.route("/produksikhazzanah")
def produksikhazzanah():
    cur = mysql.connection.cursor()
    cur.execute("Select * From produkkhazzanah")
    barang = cur.fetchall()
    cur.close()
    return render_template('produksikhazzanah.html',menu='produksi', submenu='khazzanah', data=barang)

@app.route("/fromproduksikhazzanah")
def fromproduksikhazzanah():
    return render_template('fromproduksikhazzanah.html',menu='produksi', submenu='khazzanah')

@app.route("/simpanformprodukkhazzanah", methods=["POST"])
def simpanformprodukkhazzanah ():
    Tanggal = request.form['Tanggal']
    Nama_Produk = request.form['Nama_Produk']
    Jenis_Produk = request.form['Jenis_Produk']
    Warna = request.form['Warna']
    Size = request.form['Size']
    Jumlah = request.form['Jumlah']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO produkkhazzanah(Tanggal,Nama_Produk,Jenis_Produk,Warna,Size,Jumlah) VALUES(%s,%s,%s,%s,%s,%s)",
                (Tanggal,Nama_Produk,Jenis_Produk,Warna,Size,Jumlah))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('produksikhazzanah'))

@app.route('/update_data', methods=['GET', 'POST'])
def update_data():
    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        nama_produk = request.form['Nama_Produk']
        tanggal = request.form['Tanggal']
        jenis_produk = request.form['Jenis_Produk']
        warna = request.form['Warna']
        Size = request.form['Size']
        jumlah = request.form['Jumlah']

        cursor.execute('UPDATE produkkhazzanah SET Jenis_Produk=%s, Warna=%s, Size=%s, Jumlah=%s WHERE Nama_Produk=%s AND Tanggal=%s',
                       (jenis_produk, warna, Size, jumlah, nama_produk, tanggal))
        mysql.connection.commit()
        return redirect(url_for('produksikhazzanah'))

    cursor.execute('SELECT * FROM produkkhazzanah')
    data = cursor.fetchall()
    return render_template('update_data.html', data=data)

@app.route('/hapusproduksikhazzanah', methods=['POST', 'GET'])
def hapusproduksikhazzanah():
    if request.method == 'POST':
        Tanggal = request.form['Tanggal']
        Nama_Produk = request.form['Nama_Produk']

        tanggal = datetime.strptime(Tanggal, '%Y-%m-%d').strftime('%Y-%m-%d')
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM produkkhazzanah WHERE Tanggal=%s AND Nama_Produk=%s", 
                    (Tanggal, Nama_Produk))
        mysql.connection.commit()
        return redirect(url_for('produksikhazzanah'))

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM produkkhazzanah')
    data = cursor.fetchall()
    return render_template('hapusproduksikhazzanah.html', data=data)




@app.route("/produksisahla")
def produksisahla():
    cur = mysql.connection.cursor()
    cur.execute("Select * From produksahla")
    barang = cur.fetchall()
    cur.close()
    return render_template('produksisahla.html',menu='produksi', submenu='sahla', data=barang)

@app.route("/fromproduksisahla")
def fromproduksisahla():
    return render_template('fromproduksisahla.html',menu='produksi', submenu='sahla')

@app.route("/simpanformproduksahla", methods=["POST"])
def simpanformproduksahla ():
    Tanggal = request.form['Tanggal']
    Nama_Produk = request.form['Nama_Produk']
    Jenis_Produk = request.form['Jenis_Produk']
    Warna = request.form['Warna']
    Size = request.form['Size']
    Jumlah = request.form['Jumlah']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO produksahla(Tanggal,Nama_Produk,Jenis_Produk,Warna,Size,Jumlah) VALUES(%s,%s,%s,%s,%s,%s)",
                (Tanggal,Nama_Produk,Jenis_Produk,Warna,Size,Jumlah))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('produksisahla'))

@app.route('/update_sahla', methods=['GET', 'POST'])
def update_sahla():
    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        nama_produk = request.form['Nama_Produk']
        tanggal = request.form['Tanggal']
        jenis_produk = request.form['Jenis_Produk']
        warna = request.form['Warna']
        Size = request.form['Size']
        jumlah = request.form['Jumlah']

        cursor.execute(
            'UPDATE produksahla SET Tanggal=%s, Jenis_Produk=%s, Warna=%s, Size=%s, Jumlah=%s WHERE Nama_Produk=%s',
            (tanggal, jenis_produk, warna, Size, jumlah, nama_produk))
        mysql.connection.commit()
        return redirect(url_for('produksisahla'))

    cursor.execute('SELECT * FROM produksahla')
    data = cursor.fetchall()
    return render_template('update_sahla.html', data=data)

@app.route('/hapusproduksisahla', methods=['POST', 'GET'])
def hapusproduksisahla():
    if request.method == 'POST':
        Tanggal = request.form['Tanggal']
        Nama_Produk = request.form['Nama_Produk']

        tanggal = datetime.strptime(Tanggal, '%Y-%m-%d').strftime('%Y-%m-%d')
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM produksahla WHERE Tanggal=%s AND Nama_Produk=%s", 
                    (Tanggal, Nama_Produk))
        mysql.connection.commit()
        return redirect(url_for('produksisahla'))

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM produksahla')
    data = cursor.fetchall()
    return render_template('hapusproduksisahla.html', data=data)




@app.route("/pokhazzanah")
def pokhazzanah():
    cur = mysql.connection.cursor()
    cur.execute("Select * From pokhazzanah")
    barang = cur.fetchall()
    cur.close()
    return render_template('pokhazzanah.html', menu='po', submenu='pokhazzanah', data=barang)

@app.route("/formpokhazzanah")
def formpokhazzanah():
    return render_template('formpokhazzanah.html',menu='po', submenu='pokhazzanah')

@app.route("/simpanformpokhazzanah", methods=["POST"])
def simpanformpokhazzanah ():
    Tanggal = request.form['Tanggal']
    Nama_Pelanggan = request.form['Nama_Pelanggan']
    Nama_Produk = request.form['Nama_Produk']
    Warna = request.form['Warna']
    Size = request.form['Size']
    Request_Order = request.form['Request_Order']
    Urgent = request.form['Urgent']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO pokhazzanah(Tanggal,Nama_Pelanggan,Nama_Produk,Warna,Size,Request_Order,Urgent) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                (Tanggal,Nama_Pelanggan,Nama_Produk,Warna,Size,Request_Order,Urgent))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('pokhazzanah'))

@app.route('/update_pokhazzanah', methods=['GET', 'POST'])
def update_pokhazzanah():
    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        Tanggal = request.form['Tanggal']
        Nama_Pelanggan = request.form['Nama_Pelanggan']
        Nama_Produk = request.form['Nama_Produk']
        Warna = request.form['Warna']
        Size = request.form['Size']
        Request_Order = request.form['Request_Order']
        Urgent = request.form['Urgent']

        cursor.execute(
            'UPDATE pokhazzanah SET Nama_Produk=%s, Warna=%s, Size=%s, Request_Order=%s, Urgent=%s WHERE Tanggal=%s AND Nama_Pelanggan=%s',
            (Nama_Produk,Warna,Size,Request_Order,Urgent,Tanggal,Nama_Pelanggan))
        mysql.connection.commit()
        return redirect(url_for('pokhazzanah'))

    cursor.execute('SELECT * FROM pokhazzanah')
    data = cursor.fetchall()
    return render_template('update_pokhazzanah.html', data=data)

@app.route('/hapuspokhazzanah', methods=['POST', 'GET'])
def hapuspokhazzanah():
    if request.method == 'POST':
        Tanggal = request.form['Tanggal']
        Nama_Pelanggan = request.form['Nama_Pelanggan']
        Nama_Produk = request.form['Nama_Produk']
        Warna = request.form['Warna']
        Size = request.form['Size']

        tanggal = datetime.strptime(Tanggal, '%Y-%m-%d').strftime('%Y-%m-%d')
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM pokhazzanah  WHERE Tanggal=%s AND Nama_Pelanggan=%s AND Nama_Produk=%s AND Warna=%s AND Size=%s", 
                    (Tanggal,Nama_Pelanggan,Nama_Produk,Warna,Size))
        mysql.connection.commit()
        return redirect(url_for('pokhazzanah'))

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM pokhazzanah ')
    data = cursor.fetchall()
    return render_template('hapuspokhazzanah.html', data=data)





@app.route("/posahla")
def posahla():
    cur = mysql.connection.cursor()
    cur.execute("Select * From posahla")
    barang = cur.fetchall()
    cur.close()
    return render_template('posahla.html', menu='perlengkapan', submenu='posahla', data=barang)

@app.route("/formposahla")
def formposahla():
    return render_template('formposahla.html',menu='po', submenu='posahla')

@app.route("/simpanformposahla", methods=["POST"])
def simpanformposahla ():
    Tanggal = request.form['Tanggal']
    Nama_Pelanggan = request.form['Nama_Pelanggan']
    Nama_Produk = request.form['Nama_Produk']
    Warna = request.form['Warna']
    Size = request.form['Size']
    Request_Order = request.form['Request_Order']
    Urgent = request.form['Urgent']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO posahla(Tanggal,Nama_Pelanggan,Nama_Produk,Warna,Size,Request_Order,Urgent) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                (Tanggal,Nama_Pelanggan,Nama_Produk,Warna,Size,Request_Order,Urgent))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('posahla'))

@app.route('/update_posahla', methods=['GET', 'POST'])
def update_posahla():
    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        Tanggal = request.form['Tanggal']
        Nama_Pelanggan = request.form['Nama_Pelanggan']
        Nama_Produk = request.form['Nama_Produk']
        Warna = request.form['Warna']
        Size = request.form['Size']
        Request_Order = request.form['Request_Order']
        Urgent = request.form['Urgent']

        cursor.execute(
            'UPDATE posahla SET Nama_Produk=%s, Warna=%s, Size=%s, Request_Order=%s, Urgent=%s WHERE Tanggal=%s AND Nama_Pelanggan=%s',
            (Nama_Produk,Warna,Size,Request_Order,Urgent,Tanggal,Nama_Pelanggan))
        mysql.connection.commit()
        return redirect(url_for('posahla'))

    cursor.execute('SELECT * FROM posahla')
    data = cursor.fetchall()
    return render_template('update_posahla.html', data=data)

@app.route('/hapusposahla', methods=['POST', 'GET'])
def hapusposahla():
    if request.method == 'POST':
        Tanggal = request.form['Tanggal']
        Nama_Pelanggan = request.form['Nama_Pelanggan']
        Nama_Produk = request.form['Nama_Produk']
        Warna = request.form['Warna']
        Size = request.form['Size']

        tanggal = datetime.strptime(Tanggal, '%Y-%m-%d').strftime('%Y-%m-%d')
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM posahla  WHERE Tanggal=%s AND Nama_Pelanggan=%s AND Nama_Produk=%s AND Warna=%s AND Size=%s", 
                    (Tanggal,Nama_Pelanggan,Nama_Produk,Warna,Size))
        mysql.connection.commit()
        return redirect(url_for('posahla'))

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM posahla ')
    data = cursor.fetchall()
    return render_template('hapusposahla.html', data=data)




@app.route("/penjualankhazzanah")
def penjualankhazzanah():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM penjualankhazanah')
    data = cursor.fetchall()
    cursor.close()
    return render_template('penjualankhazzanah.html', menu='penjualan', submenu='penjualankhazzanah', data=data)

@app.route("/formpenjualankhazzanah")
def formpenjualankhazzanah():
    return render_template('formpenjualankhazzanah.html', menu='perlengkapan', submenu='perlengkapankeluar')

@app.route('/simpanpenjualan', methods=["POST"])
def simpanpenjualan():
    if request.method == 'POST':
        Tanggal = request.form['Tanggal']
        Nama_Pelanggan = request.form['Nama_Pelanggan']
        Nama_Produk = request.form['Nama_Produk']
        Jenis_Produk = request.form['Jenis_Produk']
        Jumlah_Produk = request.form['Jumlah_Produk']
        Total_Harga = request.form['Total_Harga']

        if 'Bukti' in request.files:
            file = request.files['Bukti']
            if file.filename == '':
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO penjualankhazanah (Tanggal, Nama_Pelanggan, Nama_Produk, Jenis_Produk, Jumlah_Produk, Total_Harga, Bukti) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (Tanggal, Nama_Pelanggan, Nama_Produk, Jenis_Produk, Jumlah_Produk, Total_Harga, filename))
                mysql.connection.commit()
                cur.close()

                return redirect(url_for('penjualankhazzanah'))
            else:
                return redirect(request.url)
        return redirect(url_for('penjualankhazzanah'))
    
@app.route('/update_penjualankhazzanah', methods=['GET', 'POST'])
def update_penjualankhazzanah():
    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        Tanggal = request.form['Tanggal']
        Nama_Pelanggan = request.form['Nama_Pelanggan']
        Nama_Produk = request.form['Nama_Produk']
        Jenis_Produk = request.form['Jenis_Produk']
        Jumlah_Produk = request.form['Jumlah_Produk']
        Total_Harga = request.form['Total_Harga']

        cur = mysql.connection.cursor()
        cur.execute("UPDATE penjualankhazanah SET Nama_Produk=%s, Jenis_Produk=%s, Jumlah_Produk=%s, Total_Harga=%s WHERE Tanggal=%s AND Nama_Pelanggan=%s",
                    (Nama_Produk, Jenis_Produk, Jumlah_Produk, Total_Harga, Tanggal, Nama_Pelanggan))
        mysql.connection.commit()
        return redirect(url_for('penjualankhazzanah'))
    
    cursor.execute('SELECT * FROM penjualankhazanah')
    data = cursor.fetchall()
    return render_template('update_penjualankhazzanah.html', data=data)

@app.route('/hapuspenjualankhazzanah', methods=['POST', 'GET'])
def hapuspenjualankhazzanah():
    if request.method == 'POST':
        Tanggal = request.form['Tanggal']
        Nama_Pelanggan = request.form['Nama_Pelanggan']
        Nama_Produk = request.form['Nama_Produk']

        tanggal = datetime.strptime(Tanggal, '%Y-%m-%d').strftime('%Y-%m-%d')
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM penjualankhazanah  WHERE Tanggal=%s AND Nama_Pelanggan=%s AND Nama_Produk=%s", 
                    (Tanggal,Nama_Pelanggan,Nama_Produk))
        mysql.connection.commit()
        return redirect(url_for('penjualankhazzanah'))

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM penjualankhazanah')
    data = cursor.fetchall()
    return render_template('hapuspenjualankhazzanah.html', data=data)

    


    
   

 
@app.route("/penjualansahla")
def penjualansahla():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM penjualansahla')
    data = cursor.fetchall()
    cursor.close()
    return render_template('penjualansahla.html', menu='penjualan', submenu='penjualansahla', data=data)

@app.route("/formpenjualansahla")
def formpenjualansahla():
    return render_template('formpenjualansahla.html', menu='perlengkapan', submenu='perlengkapankeluar')

@app.route('/simpanpenjualansahla', methods=["POST"])
def simpanpenjualansahla():
    if request.method == 'POST':
        Tanggal = request.form['Tanggal']
        Nama_Pelanggan = request.form['Nama_Pelanggan']
        Nama_Produk = request.form['Nama_Produk']
        Jenis_Produk = request.form['Jenis_Produk']
        Jumlah_Produk = request.form['Jumlah_Produk']
        Total_Harga = request.form['Total_Harga']

        if 'Bukti' in request.files:
            file = request.files['Bukti']
            if file.filename == '':
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO penjualansahla (Tanggal, Nama_Pelanggan, Nama_Produk, Jenis_Produk, Jumlah_Produk, Total_Harga, Bukti) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (Tanggal, Nama_Pelanggan, Nama_Produk, Jenis_Produk, Jumlah_Produk, Total_Harga, filename))
                mysql.connection.commit()
                cur.close()

                return redirect(url_for('penjualansahla'))
            else:
                return redirect(request.url)
        return redirect(url_for('penjualansahla'))
    
@app.route('/update_penjualansahla', methods=['GET', 'POST'])
def update_penjualansahla():
    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        Tanggal = request.form['Tanggal']
        Nama_Pelanggan = request.form['Nama_Pelanggan']
        Nama_Produk = request.form['Nama_Produk']
        Jenis_Produk = request.form['Jenis_Produk']
        Jumlah_Produk = request.form['Jumlah_Produk']
        Total_Harga = request.form['Total_Harga']

        cur = mysql.connection.cursor()
        cur.execute("UPDATE penjualansahla  SET Nama_Produk=%s, Jenis_Produk=%s, Jumlah_Produk=%s, Total_Harga=%s WHERE Tanggal=%s AND Nama_Pelanggan=%s",
                    (Nama_Produk, Jenis_Produk, Jumlah_Produk, Total_Harga, Tanggal, Nama_Pelanggan))
        mysql.connection.commit()
        return redirect(url_for('penjualansahla'))
    
    cursor.execute('SELECT * FROM penjualansahla')
    data = cursor.fetchall()
    return render_template('update_penjualansahla.html', data=data)

@app.route('/hapuspenjualansahla', methods=['POST', 'GET'])
def hapuspenjualansahla():
    if request.method == 'POST':
        Tanggal = request.form['Tanggal']
        Nama_Pelanggan = request.form['Nama_Pelanggan']
        Nama_Produk = request.form['Nama_Produk']

        tanggal = datetime.strptime(Tanggal, '%Y-%m-%d').strftime('%Y-%m-%d')
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM penjualansahla  WHERE Tanggal=%s AND Nama_Pelanggan=%s AND Nama_Produk=%s", 
                    (Tanggal,Nama_Pelanggan,Nama_Produk))
        mysql.connection.commit()
        return redirect(url_for('penjualansahla'))

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM penjualansahla')
    data = cursor.fetchall()
    return render_template('hapuspenjualansahla.html', data=data)

    


if __name__ == "__main__":
     serve(app, host='0.0.0.0', port=5500)
     