import json, os

DB_PATH = "descargas_temp.json"

def init_db():
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, "w") as f:
            json.dump([], f)

def load_db():
    with open(DB_PATH, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)

def add_entry(entry):
    db = load_db()
    db.append(entry)
    save_db(db)

def update_entry(index, new_entry):
    db = load_db()
    db[index] = new_entry
    save_db(db)

def remove_url_from_entry(index, bad_url):
    db = load_db()
    entry = db[index]
    urls = entry["url"]
    passwords = entry.get("password", "")
    if isinstance(urls, list):
        try:
            idx = urls.index(bad_url)
            urls.pop(idx)
            if isinstance(passwords, list):
                passwords.pop(idx)
        except ValueError:
            pass
        if not urls:
            db.pop(index)
    else:
        if urls == bad_url:
            db.pop(index)
    save_db(db)
