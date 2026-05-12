# ProKOBİ Sesli İş Takip Asistanı

ProKOBİ, KOBİ’ler için geliştirilmiş bir sesli iş takip asistanıdır.  
Kullanıcılar sesli veya yazılı komutlarla görev ekleyebilir ve güncelleyebilir.

---

## Özellikler

- Sesli komut ile görev ekleme ve güncelleme  
- Gemini AI ile doğal dil işleme  
- Kanban görünümü (To Do / In Progress / Done)  
- Türkçe metin → ses çıktısı  
- FastAPI backend + Streamlit frontend  
- SQLite veritabanı  

---

## Proje Yapısı

```
.
├── backend
│   ├── crud.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│
├── frontend
│   ├── app.py
│
├── config.py
├── requirements.txt
├── .env (local, gitignore)
```

---

## Kurulum

### 1. Repo klonla

```
git clone <repo-url>
cd prokobi
```

### 2. Sanal ortam

```
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Bağımlılıklar

```
pip install -r requirements.txt
```

---

## Ortam Değişkenleri (.env)

API key’ler koda yazılmamalıdır.

Proje root’unda `.env` oluştur:

```
GEMINI_API_KEY=your_api_key_here
API_URL=http://localhost:8000
```

---

## Çalıştırma

### Backend

```
uvicorn backend.main:app --reload
```

### Frontend

```
streamlit run frontend/app.py
```

---

## API Endpointleri

- GET /tasks → görevleri listeler  
- POST /tasks → görev ekler  
- PATCH /tasks/update → görev günceller  

---

## Kullanım

- “Yarın toplantı ekle”  
- “Toplantıyı tamamlandı yap”  
- “Rapor task'ını in progress olarak güncelle”  

---

## Veritabanı

- SQLite kullanılır  
- Otomatik oluşturulur (kobi_asistan.db)  

---

## Güvenlik Notu

- API key’ler `.env` içinde tutulur  
- `.env` dosyası `.gitignore` içindedir  
- Hardcoded key kullanılmaz  

---

## Geliştirme Önerileri

- Kullanıcı authentication sistemi  
- Görev silme endpointi  
- Docker desteği  
- Cloud deployment  

---

## Not

Bu proje eğitim ve demo amaçlı geliştirilmiştir.
