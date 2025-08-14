# cd /mnt/d/projects/SolarSoundBytes && python3 - <<'PY'
import importlib.util, pathlib, sys, sqlite3

module_path = pathlib.Path("data_acquisition/db_update/add_location.py").resolve()
spec = importlib.util.spec_from_file_location("add_location", module_path)
mod = importlib.util.module_from_spec(spec)
sys.modules["add_location"] = mod
spec.loader.exec_module(mod)

conn = sqlite3.connect(mod.get_db_path())
try:
    mod.ensure_geolocation_columns(conn)
    # Ensure the tracking column exists: "location-checked"
    cols = {r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
    if "location-checked" not in cols:
        conn.execute('ALTER TABLE users ADD COLUMN "location-checked" INTEGER DEFAULT 0')
        conn.commit()
    rows = conn.execute(
        'SELECT id, location, "location-checked" FROM users ORDER BY id ASC LIMIT 50'
    ).fetchall()
    api_calls = 0
    for user_id, location, checked in rows:
        if not location or not location.strip():
            print(f"{user_id}\t<empty location>\tskipped")
            conn.execute('UPDATE users SET "location-checked" = 1 WHERE id = ?', (user_id,))
            conn.commit()
            continue
        if checked and int(checked) == 1:
            print(f"{user_id}\t{location}\talready checked")
            continue
        api_calls += 1
        coords = mod.call_chatgpt_for_geocode(location)
        print(f"{user_id}\t{location}\t{coords if coords else 'invalid/unknown'}")
        if coords:
            lat, lon = coords
            mod.update_user_coordinates(conn, user_id, lat, lon)
        conn.execute('UPDATE users SET "location-checked" = 1 WHERE id = ?', (user_id,))
        conn.commit()
    print(f"API calls performed: {api_calls}")
finally:
    conn.close()
# PY