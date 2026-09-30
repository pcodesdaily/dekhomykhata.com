import pytest
from fastapi.testclient import TestClient

from mykhata_api.accounts import upsert_user
from mykhata_api.main import create_app
from mykhata_ml.config import path

H = {"x-mykhata-request": "1"}
PDF = path("data/raw/statements/digital_type1/00001.pdf")
CSV = path("data/raw/devildyno_bank_statements.csv")


@pytest.fixture
def app(tmp_path):
    return create_app({"database_url": f"sqlite:///{tmp_path / 'test.db'}", "login_attempts": 3})


def make_user(app, email="asha@example.com", password="correct horse") -> None:
    with app.state.sessionmaker() as db:
        upsert_user(db, email, password, "Asha")


def signed_up(app, email="asha@example.com") -> TestClient:
    client = TestClient(app)
    client.__enter__()
    make_user(app, email)
    r = client.post("/api/auth/login", json={"email": email, "password": "correct horse"}, headers=H)
    assert r.status_code == 200
    return client


def test_there_is_no_signup(app) -> None:
    with TestClient(app) as c:
        r = c.post("/api/auth/signup", json={"name": "A", "email": "a@example.com", "password": "correct horse"}, headers=H)
        assert r.status_code in (404, 405)


def test_login_logout(app) -> None:
    with TestClient(app) as c:
        assert c.get("/api/auth/me").status_code == 401
        make_user(app, "Asha@Example.com")
        r = c.post("/api/auth/login", json={"email": "ASHA@example.com", "password": "correct horse"}, headers=H)
        assert r.status_code == 200 and c.get("/api/auth/me").json()["email"] == "asha@example.com"
        assert c.post("/api/auth/logout", headers=H).status_code == 204
        assert c.get("/api/auth/me").status_code == 401


def test_login_errors_are_generic_and_rate_limited(app) -> None:
    with TestClient(app) as c:
        make_user(app, "a@example.com")
        wrong = c.post("/api/auth/login", json={"email": "a@example.com", "password": "nope"}, headers=H).json()
        missing = c.post("/api/auth/login", json={"email": "b@example.com", "password": "nope"}, headers=H).json()
        assert wrong == missing
        codes = [c.post("/api/auth/login", json={"email": "a@example.com", "password": "nope"}, headers=H).status_code
                 for _ in range(3)]
        assert codes[-1] == 429


def test_account_script_helper_resets_password_and_sessions(app) -> None:
    c = signed_up(app)
    with app.state.sessionmaker() as db:
        _, created = upsert_user(db, "asha@example.com", "brand new secret")
        with pytest.raises(ValueError):
            upsert_user(db, "asha@example.com", "short")
    assert not created
    assert c.get("/api/auth/me").status_code == 401
    assert c.post("/api/auth/login", json={"email": "asha@example.com", "password": "brand new secret"},
                  headers=H).status_code == 200


def test_mutations_need_csrf_header(app) -> None:
    c = signed_up(app)
    assert c.post("/api/transactions", json={}).status_code == 403
    assert c.delete("/api/auth/me/data").status_code == 403


def test_transactions_crud_and_categorisation(app) -> None:
    c = signed_up(app)
    body = {"date": "2026-09-10", "narration": "UPI/DR/412345678901/SWIGGY/YESB/swiggy@ybl/food", "type": "DEBIT",
            "amount": 342.57}
    tx = c.post("/api/transactions", json=body, headers=H).json()
    assert tx["category"] == "FOOD_DINING" and tx["amount"] == 342.57 and tx["source"] == "manual"
    tx = c.patch(f"/api/transactions/{tx['id']}", json={"category": "GROCERIES", "amount": 100}, headers=H).json()
    assert tx["category"] == "GROCERIES" and tx["amount"] == 100 and tx["confidence"] is None
    assert c.patch(f"/api/transactions/{tx['id']}", json={"category": "SALARY"}, headers=H).status_code == 422
    assert c.delete(f"/api/transactions/{tx['id']}", headers=H).status_code == 204
    assert c.get("/api/transactions").json() == []


def test_users_cannot_touch_each_others_data(app) -> None:
    a, b = signed_up(app, "a@example.com"), signed_up(app, "b@example.com")
    body = {"date": "2026-09-10", "narration": "Rent", "type": "DEBIT", "amount": 20000, "category": "RENT"}
    tx = a.post("/api/transactions", json=body, headers=H).json()
    assert b.get("/api/transactions").json() == []
    assert b.patch(f"/api/transactions/{tx['id']}", json={"amount": 1}, headers=H).status_code == 404
    assert b.delete(f"/api/transactions/{tx['id']}", headers=H).status_code == 404


def test_upload_csv_and_pdf_statements(app) -> None:
    c = signed_up(app)
    r = c.post("/api/statements", files={"file": (CSV.name, CSV.read_bytes(), "text/csv")}, headers=H)
    assert r.status_code == 201, r.text
    stats = r.json()
    assert stats["rows"] == stats["added"] == 985 and stats["balance_failures"] == 0
    again = c.post("/api/statements", files={"file": (CSV.name, CSV.read_bytes(), "text/csv")}, headers=H)
    assert again.status_code == 409
    pdf = c.post("/api/statements", files={"file": (PDF.name, PDF.read_bytes(), "application/pdf")}, headers=H).json()
    assert pdf["rows"] == 162 and pdf["added"] == 162
    assert len(c.get("/api/statements").json()) == 2


def test_identical_rows_in_one_file_are_kept_but_overlaps_are_not(app) -> None:
    c = signed_up(app)
    rows = "date,narration,type,amount\n2026-09-01,UPI/PAYTM,DEBIT,10\n2026-09-01,UPI/PAYTM,DEBIT,10\n"
    first = c.post("/api/statements", files={"file": ("a.csv", rows.encode(), "text/csv")}, headers=H).json()
    assert first["rows"] == 2 and first["added"] == 2
    overlap = rows + "2026-09-02,UPI/PAYTM,DEBIT,10\n"
    second = c.post("/api/statements", files={"file": ("b.csv", overlap.encode(), "text/csv")}, headers=H).json()
    assert second["rows"] == 3 and second["added"] == 1
    assert len(c.get("/api/transactions").json()) == 3


def test_validation_errors_are_plain_language(app) -> None:
    with TestClient(app) as c:
        r = c.post("/api/auth/login", json={"email": "a@mykhata.test", "password": "x"}, headers=H)
        assert r.status_code == 422 and r.json() == {"detail": "Enter a valid email address you can receive mail at."}


def test_upload_rejects_bad_files(app) -> None:
    c = signed_up(app)
    assert c.post("/api/statements", files={"file": ("notes.txt", b"hi", "text/plain")}, headers=H).status_code == 400
    assert c.post("/api/statements", files={"file": ("fake.pdf", b"not a pdf", "application/pdf")},
                  headers=H).status_code == 400


def test_budgets_and_delete_all(app) -> None:
    c = signed_up(app)
    assert c.put("/api/budgets/FOOD_DINING", json={"amount": 3500}, headers=H).status_code == 200
    assert c.put("/api/budgets/SALARY", json={"amount": 1}, headers=H).status_code == 422
    assert c.get("/api/budgets").json() == {"FOOD_DINING": 3500}
    c.post("/api/transactions", json={"date": "2026-09-01", "narration": "Tea", "type": "DEBIT", "amount": 20,
                                      "category": "FOOD_DINING"}, headers=H)
    assert c.delete("/api/auth/me/data", headers=H).status_code == 204
    assert c.get("/api/budgets").json() == {} and c.get("/api/transactions").json() == []


def test_model_results_need_login(app) -> None:
    with TestClient(app) as c:
        assert c.get("/api/model/results").status_code == 401
    c = signed_up(app)
    body = c.get("/api/model/results").json()
    assert {"test_seen", "benchmark", "per_class_seen", "parser", "export"} <= body.keys()
