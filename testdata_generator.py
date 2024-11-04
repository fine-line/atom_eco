import psycopg2
import bcrypt


def hash_password(password: str) -> str:
    password = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=password, salt=salt)
    hashed_password = hashed_password.decode('utf8')
    return hashed_password


def get_env_data_as_dict(path: str) -> dict:
    with open(path, 'r') as f:
        return dict(tuple(line.replace('\n', "").replace('"', "").split("="))
                    for line in f.readlines() if not line.startswith('#'))


def create_waste(cur, name: str):
    cur.execute("INSERT INTO waste (name) VALUES (%s);", (name,))


def create_company(cur, name: str, email: str, password: str):
    hashed_password = hash_password(password)
    cur.execute("INSERT INTO company (name, email, hashed_password) \
                VALUES (%s, %s, %s);", (name, email, hashed_password))


def create_storage(cur, name: str, email: str, password: str):
    hashed_password = hash_password(password)
    cur.execute("INSERT INTO storage (name, email, hashed_password) \
                VALUES (%s, %s, %s);", (name, email, hashed_password))


def create_location(cur, name: str):
    cur.execute("INSERT INTO location (name) VALUES (%s);", (name,))


def create_one_way_road(cur, from_: str, to: str, distance: int):
    cur.execute(
        "INSERT INTO road \
        (location_from_id, location_to_id, distance) \
        VALUES (\
            (SELECT id FROM location WHERE name=%s), \
            (SELECT id FROM location WHERE name=%s), %s);",
        (from_, to, distance)
        )


def create_two_way_road(cur, from_: str, to: str, distance: int):
    cur.execute(
        "INSERT INTO road \
        (location_from_id, location_to_id, distance) \
        VALUES (\
            (SELECT id FROM location WHERE name=%s), \
            (SELECT id FROM location WHERE name=%s), %s);",
        (from_, to, distance)
        )
    cur.execute(
        "INSERT INTO road \
        (location_from_id, location_to_id, distance) \
        VALUES (\
            (SELECT id FROM location WHERE name=%s), \
            (SELECT id FROM location WHERE name=%s), %s);",
        (to, from_, distance)
        )


def create_company_waste_link(cur, company: str, waste: str, max_amount: int):
    cur.execute(
        "INSERT INTO companywastelink \
        (company_id, waste_id, max_amount, amount) \
        VALUES (\
            (SELECT id FROM company WHERE name=%s), \
            (SELECT id FROM waste WHERE name=%s), %s, %s);",
        (company, waste, max_amount, 0)
        )


def create_storage_waste_link(cur, storage: str, waste: str, max_amount: int):
    cur.execute(
        "INSERT INTO storagewastelink \
        (storage_id, waste_id, max_amount, amount) \
        VALUES (\
            (SELECT id FROM storage WHERE name=%s), \
            (SELECT id FROM waste WHERE name=%s), %s, %s);",
        (storage, waste, max_amount, 0)
        )


def create_company_location_link(cur, company: str, location: str):
    cur.execute(
        "INSERT INTO companylocationlink \
        (company_id, location_id) \
        VALUES (\
            (SELECT id FROM company WHERE name=%s), \
            (SELECT id FROM location WHERE name=%s));",
        (company, location)
        )


def create_storage_location_link(cur, storage: str, location: str):
    cur.execute(
        "INSERT INTO storagelocationlink \
        (storage_id, location_id) \
        VALUES (\
            (SELECT id FROM storage WHERE name=%s), \
            (SELECT id FROM location WHERE name=%s));",
        (storage, location)
        )


env_data = get_env_data_as_dict(".env")
db_user = env_data["DB_USER"]
db_password = env_data["DB_PASSWORD"]
db_service = env_data["DB_SERVICE"]

conn = psycopg2.connect(user=db_user, password=db_password, host=db_service)

with conn.cursor() as cur:
    # Create waste types
    create_waste(cur=cur, name="Bio")
    create_waste(cur=cur, name="Glass")
    create_waste(cur=cur, name="Plastic")
    conn.commit()

    # Create companies and locations
    for i in range(1, 2 + 1):
        create_company(
            cur=cur, name=f"company{i}", email=f"company{i}@example.com",
            password=f"company{i}"
            )
        create_location(cur=cur, name=f"C{i}_location")
    conn.commit()

    # Create storages and locations
    for i in range(1, 9 + 1):
        create_storage(
            cur=cur, name=f"storage{i}", email=f"storage{i}@example.com",
            password=f"storage{i}"
            )
        create_location(cur=cur, name=f"S{i}_location")
    conn.commit()

    # Create roads
    create_one_way_road(
        cur=cur, from_="C1_location", to="S1_location", distance=100)
    create_one_way_road(
        cur=cur, from_="C1_location", to="S2_location", distance=50)
    create_one_way_road(
        cur=cur, from_="C1_location", to="S3_location", distance=600)
    create_one_way_road(
        cur=cur, from_="C2_location", to="S3_location", distance=50)

    create_one_way_road(
        cur=cur, from_="S1_location", to="S8_location", distance=500)
    create_two_way_road(
        cur=cur, from_="S8_location", to="S9_location", distance=10)
    create_two_way_road(
        cur=cur, from_="S2_location", to="S5_location", distance=50)
    create_two_way_road(
        cur=cur, from_="S3_location", to="S7_location", distance=50)
    create_one_way_road(
        cur=cur, from_="S3_location", to="S6_location", distance=600)
    conn.commit()

    # Create company waste links
    create_company_waste_link(
        cur=cur, company="company1", waste="Plastic", max_amount=10)
    create_company_waste_link(
        cur=cur, company="company1", waste="Glass", max_amount=50)
    create_company_waste_link(
        cur=cur, company="company1", waste="Bio", max_amount=50)

    create_company_waste_link(
        cur=cur, company="company2", waste="Plastic", max_amount=60)
    create_company_waste_link(
        cur=cur, company="company2", waste="Glass", max_amount=20)
    create_company_waste_link(
        cur=cur, company="company2", waste="Bio", max_amount=50)
    conn.commit()

    # Create storage waste links
    create_storage_waste_link(
        cur=cur, storage="storage1", waste="Glass", max_amount=300)
    create_storage_waste_link(
        cur=cur, storage="storage1", waste="Plastic", max_amount=100)

    create_storage_waste_link(
        cur=cur, storage="storage2", waste="Plastic", max_amount=50)
    create_storage_waste_link(
        cur=cur, storage="storage2", waste="Bio", max_amount=150)

    create_storage_waste_link(
        cur=cur, storage="storage3", waste="Plastic", max_amount=10)
    create_storage_waste_link(
        cur=cur, storage="storage3", waste="Bio", max_amount=250)

    create_storage_waste_link(
        cur=cur, storage="storage5", waste="Glass", max_amount=220)
    create_storage_waste_link(
        cur=cur, storage="storage5", waste="Bio", max_amount=25)

    create_storage_waste_link(
        cur=cur, storage="storage6", waste="Glass", max_amount=100)
    create_storage_waste_link(
        cur=cur, storage="storage6", waste="Bio", max_amount=150)

    create_storage_waste_link(
        cur=cur, storage="storage7", waste="Plastic", max_amount=100)
    create_storage_waste_link(
        cur=cur, storage="storage7", waste="Bio", max_amount=250)

    create_storage_waste_link(
        cur=cur, storage="storage8", waste="Glass", max_amount=35)
    create_storage_waste_link(
        cur=cur, storage="storage8", waste="Plastic", max_amount=25)
    create_storage_waste_link(
        cur=cur, storage="storage8", waste="Bio", max_amount=52)

    create_storage_waste_link(
        cur=cur, storage="storage9", waste="Plastic", max_amount=250)
    create_storage_waste_link(
        cur=cur, storage="storage9", waste="Bio", max_amount=20)
    conn.commit()

    # Create company location links
    for i in range(1, 2 + 1):
        create_company_location_link(
            cur=cur, company=f"company{i}", location=f"C{i}_location")
    conn.commit()

    # Create storage location_links
    for i in range(1, 9 + 1):
        create_storage_location_link(
            cur=cur, storage=f"storage{i}", location=f"S{i}_location"
            )
    conn.commit()
