# Netflix Search API (Flask + Polars)

This project exposes a **Flask API** for searching Netflix shows/movies.  
The dataset is taken from Kaggle:  
👉 [Netflix Shows Dataset on Kaggle](https://www.kaggle.com/datasets/shivamb/netflix-shows/data)

The API loads the dataset once at startup using **Polars** for optimized performance, and exposes a `/search` endpoint to query shows by actor, director, or genre.

---

## 📂 Project Structure
```
project-root/
│── app/
│   ├── __init__.py       # App factory + dataset loader
│   ├── routes.py         # Flask routes (API endpoints)
│── tests/                 # Unit tests
│── run.py                 # App entry point
│── requirements.txt
│── README.md
│── netflix_titles.csv     # Dataset (must be placed in project root)
```

---

## ⚡ Setup Instructions

### 1. Clone repository
```bash
git clone https://github.com/khushwanthwork-sys/ubiquitous-computing-machine.git
cd ubiquitous-computing-machine
```

### 2. Create virtual environment
```bash
python -m venv venv
```

### 3. Activate environment
- **Windows**
```bash
venv\Scripts\activate
```
- **Linux / Mac**
```bash
source venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

---

## 📊 Dataset
- Download dataset from Kaggle: [Netflix Shows](https://www.kaggle.com/datasets/shivamb/netflix-shows/data)  
- Place the CSV in project root:
```
project-root/netflix_titles.csv
```

---

## 🚀 Running the API
Start the Flask server:
```bash
python run.py
```

API will be available at:
```
http://127.0.0.1:5000
```

---

## 📡 API Documentation

### **GET** `/search`
Search Netflix shows/movies by **actor**, **director**, or **genre**.  

**Query Parameters**:
- `actor` (optional) — match shows with the actor in `cast`
- `director` (optional) — match shows by director
- `genre` (optional) — match shows by genre (`listed_in`)
- You can combine multiple parameters.

**Examples**:

```bash
# Search by actor
curl "http://127.0.0.1:5000/search?actor=Tom%20Hanks"

# Search by director
curl "http://127.0.0.1:5000/search?director=Martin%20Scorsese"

# Search by genre
curl "http://127.0.0.1:5000/search?genre=Comedy"

# Combined search
curl "http://127.0.0.1:5000/search?actor=Tom%20Hanks&genre=Drama"
```

**Example Response**:

```json
{
  "results": [
    {
      "title": "Forrest Gump",
      "type": "Movie",
      "release_year": 1994
    },
    {
      "title": "The Terminal",
      "type": "Movie",
      "release_year": 2004
    }
  ]
}
```

---

## 🧪 Running Tests
We are testing the `/search` endpoint using Flask test client:

Run tests:
```bash
pytest -v
```

---

## 🛠 Tech Stack
- **Flask** → Web API  
- **Polars** → High-performance DataFrame library for optimized data operations  
- **Pytest** → Unit testing

---

## ⚡ Optimizations Implemented
1. **Columns cast once at startup** (`cast`, `director`, `listed_in`) → no repeated `.cast()` per request.  
2. **Polars LazyFrame** → filters applied efficiently only when needed.  
3. **LRU caching** → repeated queries return instantly.  
4. Substring search preserved with `.str.contains(..., literal=False)`.

---
## Notes
- Ensure `netflix_titles.csv` is in the **project root** before running the app.  
- All string operations in `/search` automatically cast Polars categorical columns to strings, ensuring search works reliably.
