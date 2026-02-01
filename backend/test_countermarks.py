"""Test script to verify countermarks persistence."""
import requests
import json

BASE_URL = "http://localhost:8000/api/v2"

# Test data: Roman Imperial coin with legion countermark (FLAT API schema)
test_coin = {
    "category": "roman_imperial",
    "metal": "silver",
    "weight_g": 3.5,
    "diameter_mm": 19.0,
    "issuer": "Vespasian",
    "year_start": 72,
    "year_end": 73,
    "grading_state": "raw",
    "grade": "VF",
    "strike_quality_detail": {
        "detail": "Well struck with full legends",
        "is_off_center": False
    },
    "countermarks": [
        {
            "countermark_type": "legionary",
            "description": "LEG X",
            "position": "obverse",
            "condition": "clear",
            "punch_shape": "rectangular",
            "authority": "Legio X Fretensis",
            "notes": "Applied during Judaean campaigns"
        },
        {
            "countermark_type": "civic_symbol",
            "description": "Bull symbol",
            "position": "reverse",
            "condition": "partial",
            "punch_shape": "circular"
        }
    ]
}

print("=" * 80)
print("TEST 1: Create coin with countermarks")
print("=" * 80)
print(json.dumps(test_coin, indent=2))
print()

# Create coin
response = requests.post(f"{BASE_URL}/coins", json=test_coin)
print(f"Response status: {response.status_code}")

if response.status_code == 201:
    coin = response.json()
    coin_id = coin["id"]
    print(f"✅ Coin created successfully with ID: {coin_id}")
    print(f"Countermarks in response: {len(coin.get('countermarks', []))}")
    print(json.dumps(coin.get('countermarks', []), indent=2))
else:
    print(f"❌ Failed to create coin: {response.text}")
    exit(1)

print()
print("=" * 80)
print(f"TEST 2: Retrieve coin {coin_id} and verify countermarks")
print("=" * 80)

# Retrieve coin
response = requests.get(f"{BASE_URL}/coins/{coin_id}")
if response.status_code == 200:
    coin = response.json()
    countermarks = coin.get("countermarks", [])
    print(f"✅ Coin retrieved successfully")
    print(f"Countermarks count: {len(countermarks)}")

    if len(countermarks) == 2:
        print("✅ All countermarks persisted!")
        print(json.dumps(countermarks, indent=2))

        # Verify fields
        cm1 = countermarks[0]
        assert cm1["countermark_type"] == "legionary", f"Expected 'legionary', got '{cm1['countermark_type']}'"
        assert cm1["description"] == "LEG X", f"Expected 'LEG X', got '{cm1['description']}'"
        assert cm1["position"] == "obverse", f"Expected 'obverse', got '{cm1['position']}'"
        assert cm1["condition"] == "clear", f"Expected 'clear', got '{cm1['condition']}'"
        print("✅ Countermark 1 validated")

        cm2 = countermarks[1]
        assert cm2["countermark_type"] == "civic_symbol", f"Expected 'civic_symbol', got '{cm2['countermark_type']}'"
        assert cm2["description"] == "Bull symbol", f"Expected 'Bull symbol', got '{cm2['description']}'"
        print("✅ Countermark 2 validated")

    elif len(countermarks) == 0:
        print("❌ COUNTERMARKS NOT PERSISTED TO DATABASE!")
    else:
        print(f"⚠️  Expected 2 countermarks, got {len(countermarks)}")
        print(json.dumps(countermarks, indent=2))
else:
    print(f"❌ Failed to retrieve coin: {response.text}")
    exit(1)

print()
print("=" * 80)
print("TEST 3: Verify strike_quality_detail")
print("=" * 80)
strike_detail = coin.get("strike_quality_detail")
if strike_detail:
    print("✅ Strike quality detail persisted!")
    print(json.dumps(strike_detail, indent=2))
else:
    print("❌ Strike quality detail NOT persisted!")

print()
print("=" * 80)
print(f"TEST 4: Update coin {coin_id} - add third countermark")
print("=" * 80)

update_data = {
    **test_coin,
    "countermarks": [
        *test_coin["countermarks"],
        {
            "countermark_type": "imperial_portrait",
            "description": "Galba portrait",
            "position": "obverse",
            "condition": "worn",
            "punch_shape": "oval",
            "authority": "Emperor Galba",
            "date_applied": "68-69 AD"
        }
    ]
}

response = requests.put(f"{BASE_URL}/coins/{coin_id}", json=update_data)
if response.status_code == 200:
    coin = response.json()
    countermarks = coin.get("countermarks", [])
    print(f"✅ Coin updated successfully")
    print(f"Countermarks count after update: {len(countermarks)}")

    if len(countermarks) == 3:
        print("✅ Third countermark added successfully!")
        print(json.dumps(countermarks, indent=2))
    else:
        print(f"⚠️  Expected 3 countermarks, got {len(countermarks)}")
else:
    print(f"❌ Failed to update coin: {response.text}")

print()
print("=" * 80)
print("TEST 5: Direct database query")
print("=" * 80)
import sqlite3
conn = sqlite3.connect('coinstack_v2.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM countermarks WHERE coin_id = ?", (coin_id,))
db_count = cursor.fetchone()[0]
cursor.execute("SELECT id, coin_id, countermark_type, description, position FROM countermarks WHERE coin_id = ?", (coin_id,))
db_rows = cursor.fetchall()
conn.close()

print(f"Countermarks in database: {db_count}")
for row in db_rows:
    print(f"  ID={row[0]}, coin_id={row[1]}, type={row[2]}, desc='{row[3]}', pos={row[4]}")

if db_count == 3:
    print("✅ DATABASE PERSISTENCE VERIFIED!")
else:
    print(f"❌ Expected 3 countermarks in DB, found {db_count}")

print()
print("=" * 80)
print("ALL TESTS COMPLETE")
print("=" * 80)
