import pymysql
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.db import get_db_connection
from pymysql.cursors import DictCursor

class User(UserMixin):
    def __init__(self, id, username, email, role='user'):
        self.id = id
        self.username = username
        self.email = email
        self.role = role

    @staticmethod
    def get(user_id):
        conn = get_db_connection()
        cursor = conn.cursor(DictCursor)
        cursor.execute("SELECT id, username, email, role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            return User(user['id'], user['username'], user['email'], user['role'])
        return None

    @staticmethod
    def create(username, email, password, role='user'):
        password_hash = generate_password_hash(password)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role)
            VALUES (%s, %s, %s, %s)
        """, (username, email, password_hash, role))
        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def find_by_username(username):
        conn = get_db_connection()
        cursor = conn.cursor(DictCursor)
        cursor.execute("SELECT id, username, email, password_hash, role FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user
    
    @staticmethod
    def get_all_users_paginated(page, per_page):
        conn = get_db_connection()
        cursor = conn.cursor(DictCursor)
        offset = (page - 1) * per_page
        cursor.execute("""
            SELECT id, username, email, role, created_at 
            FROM users
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (per_page, offset))
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        return users
    
    @staticmethod
    def verify_password(password_hash, password):
        """Verify that provided password matches the hash."""
        return check_password_hash(password_hash, password)
    
    @staticmethod
    def update_by_id(user_id, username=None, email=None, password=None, role=None):
        """Update user information by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        fields = []
        values = []
        
        if username:
            fields.append("username = %s")
            values.append(username)
        if email:
            fields.append("email = %s")
            values.append(email)
        if password:
            password_hash = generate_password_hash(password)
            fields.append("password_hash = %s")
            values.append(password_hash)
        if role:
            fields.append("role = %s")
            values.append(role)
        
        if fields:
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(fields)} WHERE id = %s"
            cursor.execute(query, tuple(values))
            conn.commit()
        
        cursor.close()
        conn.close()
    
    @staticmethod
    def delete_by_id(user_id):
        """Delete user by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()

# Fungsi untuk keyword
def get_all_keywords():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT keyword FROM keywords ORDER BY keyword")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row[0] for row in rows]

def add_keyword(keyword):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO keywords (keyword) VALUES (%s)", (keyword,))
        conn.commit()
    except pymysql.IntegrityError:
        raise ValueError("Keyword sudah ada")
    finally:
        cursor.close()
        conn.close()

def delete_keyword_by_id(keyword_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM keywords WHERE id = %s", (keyword_id,))
    conn.commit()
    cursor.close()
    conn.close()

def get_keywords_with_details():
    conn = get_db_connection()
    cursor = conn.cursor(DictCursor)
    cursor.execute("SELECT id, keyword, created_at FROM keywords ORDER BY keyword")
    keywords = cursor.fetchall()
    cursor.close()
    conn.close()
    return keywords

# Fungsi untuk berita
def get_berita_paginated(page, per_page, filter_analyzed=False):
    conn = get_db_connection()
    cursor = conn.cursor(DictCursor)
    offset = (page - 1) * per_page

    if filter_analyzed:
        # Hanya berita yang sudah dianalisis (analysis_data IS NOT NULL)
        cursor.execute("SELECT COUNT(*) as total FROM berita WHERE arsip = FALSE AND analysis_data IS NOT NULL")
        total = cursor.fetchone()['total']
        cursor.execute("""
            SELECT id, judul, link, tanggal, ringkasan, keyword, 
                   relevance_score, relevance_explanation, created_at,
                   need_analysis, analysis_data, analysis_conclusion, analysis_updated_at
            FROM berita
            WHERE arsip = FALSE AND analysis_data IS NOT NULL
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (per_page, offset))
    else:
        # Semua berita (untuk admin)
        cursor.execute("SELECT COUNT(*) as total FROM berita WHERE arsip = FALSE")
        total = cursor.fetchone()['total']
        cursor.execute("""
            SELECT id, judul, link, tanggal, ringkasan, keyword, 
                   relevance_score, relevance_explanation, created_at,
                   need_analysis, analysis_data, analysis_conclusion, analysis_updated_at
            FROM berita
            WHERE arsip = FALSE 
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (per_page, offset))

    berita = cursor.fetchall()
    cursor.close()
    conn.close()
    return berita, total

def get_berita_by_id(berita_id):
    conn = get_db_connection()
    cursor = conn.cursor(DictCursor)
    cursor.execute("SELECT id, judul, link, need_analysis, analysis_data, analysis_conclusion, analysis_updated_at FROM berita WHERE id = %s", (berita_id,))
    berita = cursor.fetchone()
    cursor.close()
    conn.close()
    return berita

def update_berita_relevance(berita_id, score, explanation):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE berita 
        SET relevance_score = %s, relevance_explanation = %s 
        WHERE id = %s
    """, (score, explanation, berita_id))
    conn.commit()
    cursor.close()
    conn.close()

def delete_berita_by_ids(ids):
    if not ids:
        return 0
    conn = get_db_connection()
    cursor = conn.cursor()
    format_strings = ','.join(['%s'] * len(ids))
    cursor.execute(f"DELETE FROM berita WHERE id IN ({format_strings})", tuple(ids))
    deleted = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return deleted

def arsip_berita_by_ids(ids):
    if not ids:
        return 0
    conn = get_db_connection()
    cursor = conn.cursor()
    format_strings = ','.join(['%s'] * len(ids))
    cursor.execute(f"UPDATE berita SET arsip=TRUE WHERE id IN ({format_strings})", tuple(ids))
    arsip = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return arsip

def insert_berita(judul, link, tanggal, ringkasan, keyword, sumber):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO berita (judul, link, tanggal, ringkasan, keyword, sumber)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (judul, link, tanggal, ringkasan, keyword, sumber))
        conn.commit()
    except pymysql.Error:
        pass  # log bisa ditambahkan
    finally:
        cursor.close()
        conn.close()

def get_berita_by_link(berita_link):
    conn = get_db_connection()
    cursor = conn.cursor(DictCursor)
    cursor.execute("SELECT * FROM berita WHERE link = %s", (berita_link,))
    berita = cursor.fetchone()
    cursor.close()
    conn.close()
    return berita

def update_berita_analysis(berita_id, analysis_data, analysis_conclusion):
    """Menyimpan hasil analisis data dan kesimpulan."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE berita 
        SET analysis_data = %s, 
            analysis_conclusion = %s, 
            analysis_updated_at = NOW()
        WHERE id = %s
    """, (analysis_data, analysis_conclusion, berita_id))
    conn.commit()
    cursor.close()
    conn.close()

def set_need_analysis(berita_id, need=True):
    """Menandai berita perlu dianalisis atau tidak."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE berita SET need_analysis = %s WHERE id = %s", (1 if need else 0, berita_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_berita_need_analysis():
    """Mengambil daftar berita yang perlu dianalisis (need_analysis = 1)."""
    conn = get_db_connection()
    cursor = conn.cursor(DictCursor)
    cursor.execute("SELECT id, judul, link FROM berita WHERE need_analysis = 1")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data