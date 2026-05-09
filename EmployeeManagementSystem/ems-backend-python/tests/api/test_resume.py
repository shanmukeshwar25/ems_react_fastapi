from chatbot import resume_router


class FakeMessage:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.message = FakeMessage(content)


class FakeResponse:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]


class FakeCompletions:
    def __init__(self, content):
        self._content = content

    def create(self, **kwargs):
        return FakeResponse(self._content)


class FakeChat:
    def __init__(self, content):
        self.completions = FakeCompletions(content)


class FakeGroqClient:
    def __init__(self, content):
        self.chat = FakeChat(content)


def test_resume_upload_success(client, monkeypatch):
    temp_file = "resume_test_temp_success.pdf"
    monkeypatch.setattr(resume_router, "TEMP_FILE", temp_file)
    monkeypatch.setattr(resume_router, "extract_text", lambda file_path: "Jane Doe Python FastAPI")
    monkeypatch.setattr(
        resume_router,
        "client",
        FakeGroqClient(
            '{"fName":"Jane","lName":"Doe","pEmail":"jane@example.com","phoneNumber":"1234567890","dob":"01/02/2000","address":{"street":"Main","city":"Pune","state":"MH","zip":"411001","country":"India"},"skills":["Python","FastAPI"]}'
        ),
    )

    response = client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json()["fName"] == "Jane"
    assert response.json()["dob"] == "2000-02-01"
    assert response.json()["skills"] == ["Python", "FastAPI"]


def test_resume_upload_failure_returns_error_payload(client, monkeypatch):
    monkeypatch.setattr(resume_router, "TEMP_FILE", "resume_test_temp_failure.pdf")

    def fake_extract_text(file_path):
        raise RuntimeError("PDF parse failed")

    monkeypatch.setattr(resume_router, "extract_text", fake_extract_text)

    response = client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json()["error"] == "Failed to process resume"
