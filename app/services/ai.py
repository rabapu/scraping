import requests
import json
from config import Config

def generate_conclusion_with_deepseek(judul, konten):
    headers = {
        'Authorization': f'Bearer {Config.DEEPSEEK_API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        'model': Config.DEEPSEEK_MODEL,
        'messages': [
            {'role': 'system', 'content': 'Anda adalah asisten yang membuat kesimpulan singkat.'},
            {'role': 'user', 'content': Config.DEEPSEEK_PROMPT.format(judul=judul, konten=konten[:4000])}
        ],
        'temperature': 0.3,
        'max_tokens': 150
    }
    try:
        response = requests.post(Config.DEEPSEEK_API_URL, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error DeepSeek request: {e}")
        return None

def generate_relevance_with_deepseek(judul, konten):
    if not Config.DEEPSEEK_API_KEY:
        return None

    system_prompt = (
        "Anda adalah analis kebijakan di Direktorat Jenderal Bea dan Cukai (DJBC). "
        "Tugas Anda adalah menilai seberapa relevan suatu berita dengan tugas pokok, fungsi, dan risiko DJBC.\n\n"
        "Tugas pokok DJBC:\n"
        "- Melaksanakan perumusan dan pelaksanaan kebijakan di bidang kepabeanan dan cukai\n"
        "- Melindungi masyarakat dari barang ilegal\n"
        "- Mengoptimalkan penerimaan negara\n"
        "- Fasilitasi perdagangan\n"
        "- Pengawasan dan penindakan\n\n"
        "Fungsi:\n"
        "- Penyusunan kebijakan\n"
        "- Pelaksanaan kebijakan\n"
        "- Bimbingan teknis dan supervisi\n"
        "- Pengawasan dan evaluasi\n\n"
        "Risiko:\n"
        "- Penyelundupan\n"
        "- Pelanggaran cukai\n"
        "- Narkotika dan prekursor\n"
        "- Barang berbahaya/ilegal\n"
        "- Under-invoicing / salah tarif\n"
        "- Korupsi dan kolusi internal\n"
        "- Ancaman siber\n"
        "- Krisis ekonomi dan perdagangan global\n"
        "- Perubahan regulasi internasional\n"
        "- Isu lingkungan terkait barang impor\n"
        "- Keamanan maritim dan perbatasan\n"
        "- False Declaration dan penipuan dokumen\n"
        "- Keamanan nasional\n\n"
        "Beri skor relevansi dalam bentuk persentase 0-100% dan penjelasan singkat mengenai relevansi dan analisis risiko\n" 
        "dan dampak untuk institusi maksimal 100 kata\n"
        "Apabila perlu hubungkan juga dengan kebijakan yang perlu diambil dan saran perbaikan dengan narasi yang tepat.\n\n "
        "Format output HARUS JSON murni tanpa teks lain:\n"
        '{"score": 85, "explanation": "Berita ini membahas penindakan penyelundupan rokok ilegal yang merupakan tugas pokok DJBC."}'
    )

    user_prompt = f"Judul: {judul}\n\nKonten: {konten[:4000]}"
    headers = {
        'Authorization': f'Bearer {Config.DEEPSEEK_API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        'model': Config.DEEPSEEK_MODEL,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ],
        'temperature': 0.2,
        'max_tokens': 200,
        'response_format': {'type': 'json_object'}
    }
    try:
        response = requests.post(Config.DEEPSEEK_API_URL, json=payload, headers=headers, timeout=25)
        response.raise_for_status()
        result = response.json()
        content = result['choices'][0]['message']['content'].strip()
        # Bersihkan jika ada markdown
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        data = json.loads(content)
        score = int(data.get('score', 0))
        score = max(0, min(100, score))
        explanation = data.get('explanation', '').strip()
        return {'score': score, 'explanation': explanation}
    except Exception as e:
        print(f"Error DeepSeek relevance: {e}")
        return None