import threading
import time
import pymysql
from datetime import datetime, date, timedelta
from app.services.scraper import scrape_detik_by_keyword, scrape_kompas_by_keyword, fetch_article_content
from app.services.ai import generate_conclusion_with_deepseek
from app.models import insert_berita, get_berita_by_link
from config import Config

# Global task status
tasks = {}
tasks_lock = threading.Lock()

def generate_task_id():
    import random
    return f"task_{int(time.time())}_{random.randint(1000,9999)}"

def run_scrape_task(task_id, keywords):
    with tasks_lock:
        tasks[task_id] = {
            'status': 'running',
            'progress': 0,
            'total_keywords': len(keywords),
            'current_keyword': '',
            'saved_count': 0,
            'error': None,
            'complete': False
        }

    total_saved = 0
    try:
        # Proses setiap keyword
        total_processed = 0
        total_items_estimate = len(keywords) * 20  # perkiraan, agar progress tidak mentok

        for keyword in keywords:
            with tasks_lock:
                tasks[task_id]['current_keyword'] = keyword

            # Scrape kompas
            kompas_items = scrape_kompas_by_keyword(keyword)
            # Scrape detik
            detik_items = scrape_detik_by_keyword(keyword)
            all_items = kompas_items + detik_items
            total_items_estimate = len(keywords) * len(all_items)

            for item in all_items:
                # Cek duplikat berdasarkan link?
                duplikat = get_berita_by_link(item['link'])
                if duplikat:
                    continue
                else:
                    # Ambil konten dan buat ringkasan
                    konten = fetch_article_content(item['link'])
                    ringkasan = None
                    if konten:
                        ringkasan = generate_conclusion_with_deepseek(item['judul'], konten)
                    time.sleep(1)  # jeda antar request

                    # Parsing tanggal
                    tgl_parsed = parse_tanggal(item['tanggal'], item['sumber'])
                    if tgl_parsed:
                        insert_berita(
                            judul=item['judul'],
                            link=item['link'],
                            tanggal=tgl_parsed,
                            ringkasan=ringkasan,
                            keyword=item['keyword'],
                            sumber=item['sumber']
                        )
                        total_saved += 1
                        with tasks_lock:
                            tasks[task_id]['saved_count'] = total_saved

                total_processed += 1
                progress = int((total_processed / total_items_estimate) * 100)
                with tasks_lock:
                    tasks[task_id]['progress'] = min(progress, 99)  # jangan sampai 100 sebelum selesai

            time.sleep(1)  # jeda antar keyword

        with tasks_lock:
            tasks[task_id].update({
                'status': 'completed',
                'progress': 100,
                'saved_count': total_saved,
                'complete': True
            })
    except Exception as e:
        with tasks_lock:
            tasks[task_id].update({
                'status': 'error',
                'error': str(e),
                'complete': True
            })

def parse_tanggal(tanggal_str, sumber):
    """Mengubah string tanggal menjadi format YYYY-MM-DD"""
    now = datetime.now()
    if "jam" in tanggal_str or "menit" in tanggal_str:
        return now.strftime("%Y-%m-%d")

    bulan_indonesia = {
        'kompas.com': ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
                       "Juli", "Agustus", "September", "Oktober", "November", "Desember"],
        'detik.com': ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
                      "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    }
    bulan_list = bulan_indonesia.get(sumber, bulan_indonesia['detik.com'])
    parts = tanggal_str.split()
    if len(parts) < 3:
        return None
    try:
        if sumber == 'kompas.com':
            # format: "25 Maret 2024" -> parts: ["25", "Mar", "2024"]
            tgl = int(parts[0])
            bln_str = parts[1]
            thn = parts[2]
        else:  # detik.com
            # format: "Senin, 25 Mar 2024" sama? di detik mungkin "Senin, 25 Mar 2024"
            # asumsi: ["Senin,", "25", "Mar", "2024"]
            tgl = int(parts[1])
            bln_str = parts[2]
            thn = parts[3]
        bln_angka = bulan_list.index(bln_str) + 1
        return f"{thn}-{bln_angka:02d}-{tgl:02d}"
    except (ValueError, IndexError):
        return None

def get_task_status(task_id):
    with tasks_lock:
        return tasks.get(task_id)