from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import mysql.connector
from starlette.middleware.cors import CORSMiddleware
import logging

app = FastAPI()

# Konfigurasi CORS
orig_origins = [
    "http://127.0.0.1:5500",  # Ganti dengan asal yang sesuai
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=orig_origins,  # Mengizinkan asal yang ditentukan
    allow_credentials=True,
    allow_methods=["*"],  # Mengizinkan semua metode HTTP
    allow_headers=["*"],  # Mengizinkan semua header
)

# Model untuk request body
class Register(BaseModel):
    status: str
    name: str
    numberPhone: str 
    email: str
    password: str
    token: Optional[str] = None
    namaAnak: Optional[str] = None
    mapel: Optional[str] = None
    sekolah: Optional[str] = None

class Login(BaseModel):
    email: str
    password: str

# Koneksi ke database MySQL
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="sekolah"
    )

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/register")
async def register_user(user: Register):
    try:
        db = get_db_connection()
        cursor = db.cursor()

        if user.status == "siswa":
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS siswa (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    fullname VARCHAR(100) NULL,
                    phone VARCHAR(20) NULL,
                    email VARCHAR(100) NULL,
                    pass VARCHAR(255) NULL,
                    token VARCHAR(100) NULL
                )
            """)
            cursor.execute("""
                INSERT INTO siswa (fullname, phone, email, pass, token)
                VALUES (%s, %s, %s, %s, %s)
            """, (user.name, user.numberPhone, user.email, user.password, user.token))
            db.commit()
        elif user.status == "orangtua":
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orangtua (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    fullname VARCHAR(100) NULL,
                    phone VARCHAR(20) NULL,
                    email VARCHAR(100) NULL,
                    pass VARCHAR(255) NULL,
                    anak VARCHAR(100) NULL
                )
            """)
            cursor.execute("""
                INSERT INTO orangtua (fullname, phone, email, pass, anak)
                VALUES (%s, %s, %s, %s, %s)
            """, (user.name, user.numberPhone, user.email, user.password, user.namaAnak))
            db.commit()

        elif user.status == "guru":
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS guru (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    fullname VARCHAR(100) NULL,
                    phone VARCHAR(20) NULL,
                    email VARCHAR(100) NULL,
                    pass VARCHAR(255) NULL,
                    mapel VARCHAR(100) NULL,
                    sekolah VARCHAR(100) NULL
                )
            """)
            cursor.execute("""
                INSERT INTO guru (fullname, phone, email, pass, mapel, sekolah)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user.name, user.numberPhone, user.email, user.password, user.mapel, user.sekolah))
            db.commit()

        cursor.close()
        db.close()

        return {"status": "success", "message": f"User {user.name} registered successfully"}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    
@app.post("/login")
async def login_user(user: Login):
    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        for table_tuple in tables:
            table = table_tuple[0]  # Mengambil nama tabel dari tuple
            cursor.execute(f"SHOW COLUMNS FROM {table} LIKE 'email'")
            user_exists = cursor.fetchone() is not None

            if user_exists:
                cursor.execute(f"SELECT * FROM {table} WHERE email = %s AND pass = %s", (user.email, user.password))
                result = cursor.fetchone()

                if result:
                    cursor.close()
                    db.close()
                    return {"status": "success", "message": "Login success", "username": result[1], "email": result[3], "token": result[5]}

        cursor.close()
        db.close()
        return {"status": "failed", "message": "Login failed"}
    
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=str(err))

# Model untuk data provinsi
class Provinsi(BaseModel):
    provinsi: str

# Endpoint untuk mendapatkan provinsi
@app.get("/provinsi", response_model=List[Provinsi])
async def get_provinsi():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT provinsi FROM data_sekolah")  # Ganti dengan query yang sesuai
        provinsi = cursor.fetchall()
        cursor.close()
        db.close()
        return provinsi
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=str(err))

# Model untuk data kota
class Kota(BaseModel):
    kota: str

# Endpoint untuk mendapatkan kota berdasarkan provinsi
@app.get("/kota", response_model=List[Kota])
async def get_kota(provinsi: str):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT kota FROM data_sekolah WHERE provinsi = %s", (provinsi,))
        kota = cursor.fetchall()
        cursor.close()
        db.close()
        return kota
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=str(err))

# Model untuk data sekolah
class Sekolah(BaseModel):
    sekolah: str

# Endpoint untuk mendapatkan sekolah berdasarkan kota
@app.get("/sekolah", response_model=List[Sekolah])
async def get_sekolah(kota: str):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT sekolah FROM data_sekolah WHERE kota = %s", (kota,))
        sekolah = cursor.fetchall()
        cursor.close()
        db.close()
        return sekolah
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    
class Mapel(BaseModel):
    mapel: str
    warna: str
    url_gambar: str

@app.get("/mapel", response_model=List[Mapel])
async def get_mapel():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM mapel")
        
        # Mengambil nama kolom
        columns = [column[0] for column in cursor.description]
        
        # Mengambil data dan menggabungkannya dengan nama kolom
        mapel = cursor.fetchall()
        results = [dict(zip(columns, row)) for row in mapel]
        
        cursor.close()
        db.close()
        
        return results
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    
class Token(BaseModel):
    kelas: str
    semester: int
    jumlah_mapel: int
    
@app.get('/token/{token_code}', response_model=List[Token])
async def get_token(token_code: str):
    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("SELECT * FROM token WHERE token_code = %s", (token_code,))

        columns = [column[0] for column in cursor.description]

        token = cursor.fetchall()
        result = [dict(zip(columns, row)) for row in token]

        cursor.close()
        db.close()
        
        return result
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    
class Nilai(BaseModel):
    matematika: Optional[float] = None
    fisika: Optional[float] = None
    kimia: Optional[float] = None

@app.get("/nilai/{user_name}", response_model=List[Nilai])
async def get_nilai(user_name: str):
    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        table_names = [table[0] for table in tables]
        kolom_name = ['ulangan_1', 'ulangan_2', 'uts', 'ulangan_3', 'ulangan_4', 'uas']

        for tabel in table_names:
            cursor.execute(f"SHOW COLUMNS FROM {tabel}")
            columns = cursor.fetchall()

            column_names = [column[0] for column in columns]
            column_exists = all(kolom in column_names for kolom in kolom_name)

            if column_exists:
                cursor.execute(f"""
                    SELECT (ulangan_1 + ulangan_2 + uts + ulangan_3 + ulangan_4 + uas) as total_nilai, (ulangan_1 + ulangan_2 + uts + ulangan_3 + ulangan_4 + uas) / 6 AS rata_rata
                    FROM {tabel} WHERE fullname = %s
                """, (user_name,))
                result = cursor.fetchall()

                cursor.execute(f"""
                    UPDATE nilai
                    SET matematika = %s
                    WHERE fullname = %s
                """, (result[0][1], user_name))
                db.commit()

                cursor.execute("SELECT * FROM nilai WHERE fullname = %s", (user_name,))
                # Mengambil nama kolom
                columns = [column[0] for column in cursor.description]
                
                # Mengambil data dan menggabungkannya dengan nama kolom
                nilai = cursor.fetchall()
                results = [dict(zip(columns, row)) for row in nilai]
                
                cursor.close()
                db.close()
                
                return results

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)