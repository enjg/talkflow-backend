"""端到端测试 — 覆盖完整业务流程"""
import pytest
import httpx
import uuid

BASE = "http://127.0.0.1:8000/api/v1"
UNIQUE = uuid.uuid4().hex[:8]
NICKNAME = f"tester_{UNIQUE}"
PASSWORD = "test123456"


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE, timeout=15) as c:
        yield c


class TestHealth:
    def test_health_check(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["data"]["status"] == "healthy"
        assert data["data"]["services"]["database"] == "connected"


class TestRegister:
    def test_register_success(self, client):
        r = client.post("/auth/register", json={"nickname": NICKNAME, "password": PASSWORD})
        assert r.status_code == 200
        data = r.json()
        assert data["code"] == 0
        assert "access_token" in data["data"]

    def test_register_duplicate(self, client):
        r = client.post("/auth/register", json={"nickname": NICKNAME, "password": PASSWORD})
        assert r.status_code == 400

    def test_register_short_password(self, client):
        r = client.post("/auth/register", json={"nickname": f"short_{UNIQUE}", "password": "12"})
        assert r.status_code == 422


class TestLogin:
    def test_login_success(self, client):
        r = client.post("/auth/login", json={"nickname": NICKNAME, "password": PASSWORD})
        assert r.status_code == 200
        assert "access_token" in r.json()["data"]

    def test_login_wrong_password(self, client):
        r = client.post("/auth/login", json={"nickname": NICKNAME, "password": "wrong"})
        assert r.status_code == 401

    def test_login_nonexistent(self, client):
        r = client.post("/auth/login", json={"nickname": "nobody_xyz", "password": "123456"})
        assert r.status_code == 401


class TestAuth:
    def test_no_token_rejected(self, client):
        assert client.get("/users/me").status_code == 401

    def test_invalid_token_rejected(self, client):
        assert client.get("/users/me", headers={"Authorization": "Bearer bad"}).status_code == 401


class TestUser:
    @pytest.fixture(autouse=True)
    def login(self, client):
        r = client.post("/auth/login", json={"nickname": NICKNAME, "password": PASSWORD})
        self.token = r.json()["data"]["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_get_me(self, client):
        r = client.get("/users/me", headers=self.headers)
        assert r.status_code == 200
        assert r.json()["data"]["nickname"] == NICKNAME

    def test_update_me(self, client):
        r = client.patch("/users/me", headers=self.headers, json={"target_lang": "en", "level": "intermediate"})
        assert r.status_code == 200


class TestSessions:
    @pytest.fixture(autouse=True)
    def login(self, client):
        r = client.post("/auth/login", json={"nickname": NICKNAME, "password": PASSWORD})
        self.token = r.json()["data"]["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_create_session(self, client):
        r = client.post("/sessions", headers=self.headers, json={"title": "测试对话", "topic": "daily"})
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["title"] == "测试对话"
        self.__class__.session_id = data["id"]

    def test_list_sessions(self, client):
        r = client.get("/sessions", headers=self.headers)
        assert r.status_code == 200
        assert r.json()["data"]["total"] >= 1

    def test_get_session(self, client):
        sid = self.__class__.session_id
        r = client.get(f"/sessions/{sid}", headers=self.headers)
        assert r.status_code == 200
        assert r.json()["data"]["id"] == sid

    def test_delete_session(self, client):
        r = client.post("/sessions", headers=self.headers, json={"title": "待删除"})
        sid = r.json()["data"]["id"]
        r = client.delete(f"/sessions/{sid}", headers=self.headers)
        assert r.status_code == 200


class TestChat:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        r = client.post("/auth/login", json={"nickname": NICKNAME, "password": PASSWORD})
        self.token = r.json()["data"]["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        r = client.post("/sessions", headers=self.headers, json={"title": "聊天测试", "topic": "free"})
        self.session_id = r.json()["data"]["id"]

    def test_send_message_returns_sse(self, client):
        with client.stream("POST", "/chat/send", headers=self.headers, json={
            "session_id": self.session_id, "message": "Hello!", "reply_lang": "auto"
        }) as r:
            assert r.status_code == 200
            assert "text/event-stream" in r.headers.get("content-type", "")
            chunks = []
            for line in r.iter_lines():
                if line.startswith("data:"):
                    chunks.append(line)
                if len(chunks) >= 2:
                    break
            assert len(chunks) >= 1


class TestRefresh:
    def test_refresh_token(self, client):
        r = client.post("/auth/login", json={"nickname": NICKNAME, "password": PASSWORD})
        refresh = r.json()["data"]["refresh_token"]
        r = client.post("/auth/refresh", json={"refresh_token": refresh})
        assert r.status_code == 200
        assert "access_token" in r.json()["data"]
