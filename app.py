from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import os

app = Flask(__name__)
app.secret_key = "keuangan123"


# =====================================================
# DATABASE
# =====================================================

def init_db():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transaksi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tanggal TEXT,
        deskripsi TEXT,
        kategori TEXT,
        jenis TEXT,
        jumlah INTEGER
    )
    """)

    conn.commit()
    conn.close()


init_db()


# =====================================================
# LOGIN
# =====================================================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "photographer" and password == "225":

            session["login"] = True
            return redirect("/dashboard")

        else:

            return render_template(
                "login.html",
                pesan="Username atau Password Salah"
            )

    return render_template("login.html")


# =====================================================
# LOGOUT
# =====================================================

@app.route("/logout")
def logout():

    session.clear()
    return redirect("/")


# =====================================================
# DASHBOARD
# =====================================================

@app.route("/dashboard")
def dashboard():

    if "login" not in session:
        return redirect("/")

    return render_template("dashboard.html")


# =====================================================
# TAMBAH TRANSAKSI
# =====================================================

@app.route("/tambah", methods=["GET", "POST"])
def tambah():

    if "login" not in session:
        return redirect("/")

    if request.method == "POST":

        tanggal = request.form["tanggal"]
        deskripsi = request.form["deskripsi"]
        kategori = request.form["kategori"]
        jenis = request.form["jenis"]
        jumlah = int(request.form["jumlah"])

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO transaksi
        (tanggal, deskripsi, kategori, jenis, jumlah)
        VALUES (?, ?, ?, ?, ?)
        """, (
            tanggal,
            deskripsi,
            kategori,
            jenis,
            jumlah
        ))

        conn.commit()
        conn.close()

        return redirect("/laporan")

    return render_template("tambah.html")


# =====================================================
# LAPORAN
# =====================================================

@app.route("/laporan")
def laporan():

    if "login" not in session:
        return redirect("/")

    periode = request.args.get("periode", "semua")
    tanggal = request.args.get("tanggal", "")
    bulan = request.args.get("bulan", "")
    triwulan = request.args.get("triwulan", "")

    conn = sqlite3.connect("database.db")

    if periode == "semua":

        query = """
        SELECT *
        FROM transaksi
        ORDER BY tanggal
        """

    elif periode == "harian":

        if tanggal:

            query = f"""
            SELECT *
            FROM transaksi
            WHERE tanggal = '{tanggal}'
            """

        else:

            query = """
            SELECT *
            FROM transaksi
            WHERE 1=0
            """

    elif periode == "bulanan":

        if bulan:

            query = f"""
            SELECT *
            FROM transaksi
            WHERE strftime('%Y-%m', tanggal) = '{bulan}'
            """

        else:

            query = """
            SELECT *
            FROM transaksi
            WHERE 1=0
            """

    elif periode == "triwulan":

        if triwulan == "1":

            query = """
            SELECT *
            FROM transaksi
            WHERE CAST(strftime('%m', tanggal) AS INTEGER)
            BETWEEN 1 AND 3
            """

        elif triwulan == "2":

            query = """
            SELECT *
            FROM transaksi
            WHERE CAST(strftime('%m', tanggal) AS INTEGER)
            BETWEEN 4 AND 6
            """

        elif triwulan == "3":

            query = """
            SELECT *
            FROM transaksi
            WHERE CAST(strftime('%m', tanggal) AS INTEGER)
            BETWEEN 7 AND 9
            """

        elif triwulan == "4":

            query = """
            SELECT *
            FROM transaksi
            WHERE CAST(strftime('%m', tanggal) AS INTEGER)
            BETWEEN 10 AND 12
            """

        else:

            query = """
            SELECT *
            FROM transaksi
            WHERE 1=0
            """

    else:

        query = """
        SELECT *
        FROM transaksi
        """

    df = pd.read_sql_query(query, conn)

    conn.close()

    data = df.values.tolist()

    total_masuk = int(
        df[df["jenis"] == "masuk"]["jumlah"].sum()
    ) if not df.empty else 0

    total_keluar = int(
        df[df["jenis"] == "keluar"]["jumlah"].sum()
    ) if not df.empty else 0

    saldo = total_masuk - total_keluar

    return render_template(
        "laporan.html",
        data=data,
        masuk=total_masuk,
        keluar=total_keluar,
        saldo=saldo,
        periode=periode,
        tanggal=tanggal,
        bulan=bulan,
        triwulan=triwulan
    )
# =====================================================
# EDIT
# =====================================================

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    if "login" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == "POST":

        tanggal = request.form["tanggal"]
        deskripsi = request.form["deskripsi"]
        kategori = request.form["kategori"]
        jenis = request.form["jenis"]
        jumlah = int(request.form["jumlah"])

        cursor.execute("""
        UPDATE transaksi
        SET tanggal=?,
            deskripsi=?,
            kategori=?,
            jenis=?,
            jumlah=?
        WHERE id=?
        """, (
            tanggal,
            deskripsi,
            kategori,
            jenis,
            jumlah,
            id
        ))

        conn.commit()
        conn.close()

        return redirect("/laporan")

    cursor.execute(
        "SELECT * FROM transaksi WHERE id=?",
        (id,)
    )

    data = cursor.fetchone()

    conn.close()

    return render_template(
        "edit.html",
        d=data
    )


# =====================================================
# HAPUS
# =====================================================

@app.route("/hapus/<int:id>")
def hapus(id):

    if "login" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM transaksi WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/laporan")


# =====================================================
# LABA RUGI
# =====================================================

@app.route("/laba_rugi")
def laba_rugi():

    if "login" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")

    df = pd.read_sql_query(
        "SELECT * FROM transaksi",
        conn
    )

    conn.close()

    pendapatan = int(
        df[df["jenis"] == "masuk"]["jumlah"].sum()
    ) if not df.empty else 0

    beban = int(
        df[df["jenis"] == "keluar"]["jumlah"].sum()
    ) if not df.empty else 0

    laba = pendapatan - beban

    return render_template(
        "laba_rugi.html",
        pendapatan=pendapatan,
        beban=beban,
        laba=laba
    )


# =====================================================
# NERACA
# =====================================================

@app.route("/neraca")
def neraca():

    if "login" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")

    df = pd.read_sql_query(
        "SELECT * FROM transaksi",
        conn
    )

    conn.close()

    kas = (
        int(df[df["jenis"] == "masuk"]["jumlah"].sum())
        if not df.empty else 0
    ) - (
        int(df[df["jenis"] == "keluar"]["jumlah"].sum())
        if not df.empty else 0
    )

    aset = kas
    kewajiban = 0
    modal = aset - kewajiban

    return render_template(
        "neraca.html",
        aset=aset,
        kewajiban=kewajiban,
        modal=modal
    )


# =====================================================
# GRAFIK
# =====================================================

@app.route("/grafik")
def grafik():

    if "login" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")

    df = pd.read_sql_query(
        "SELECT * FROM transaksi",
        conn
    )

    conn.close()

    masuk = int(
        df[df["jenis"] == "masuk"]["jumlah"].sum()
    ) if not df.empty else 0

    keluar = int(
        df[df["jenis"] == "keluar"]["jumlah"].sum()
    ) if not df.empty else 0

    if not os.path.exists("static"):
        os.makedirs("static")

    plt.figure(figsize=(6, 4))

    plt.bar(
        ["Pemasukan", "Pengeluaran"],
        [masuk, keluar],
        color=["pink", "grey"]
    )

    plt.title("Grafik Keuangan")
    plt.tight_layout()

    plt.savefig("static/grafik.png")
    plt.close()

    return render_template("grafik.html")


# =====================================================
# EXPORT CSV
# =====================================================

@app.route("/export")
def export():

    if "login" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")

    df = pd.read_sql_query(
        "SELECT * FROM transaksi",
        conn
    )

    conn.close()

    if not os.path.exists("export"):
        os.makedirs("export")

    file_path = "export/laporan.csv"

    df.to_csv(
        file_path,
        index=False
    )

    return send_file(
        file_path,
        as_attachment=True
    )


# =====================================================
# CETAK PDF
# =====================================================

@app.route("/cetak_pdf")
def cetak_pdf():

    if "login" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")

    df = pd.read_sql_query(
        "SELECT * FROM transaksi",
        conn
    )

    conn.close()

    data = df.values.tolist()

    total_masuk = int(
        df[df["jenis"] == "masuk"]["jumlah"].sum()
    ) if not df.empty else 0

    total_keluar = int(
        df[df["jenis"] == "keluar"]["jumlah"].sum()
    ) if not df.empty else 0

    saldo = total_masuk - total_keluar

    return render_template(
        "cetak_pdf.html",
        data=data,
        masuk=total_masuk,
        keluar=total_keluar,
        saldo=saldo
    )


# =====================================================
# RUN APP
# =====================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        use_reloader=True
    )
