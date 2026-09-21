"""HTTP flow for the merge import — preview page, confirm, idempotency, export."""
import io
import json
import re

from app.models import db, User, Activity, CompletionLog
from app.models.judge import JudgeReview


def _preview_html(client, payload):
    data = {"backup_file": (io.BytesIO(json.dumps(payload).encode("utf-8")), "backup.json")}
    return client.post("/import/preview", data=data, content_type="multipart/form-data")


def _plan_from(html_text):
    m = re.search(r'name="plan_json" value="([^"]*)"', html_text)
    assert m, "plan_json hidden field missing"
    return json.loads(_unescape(m.group(1)))


def _unescape(value):
    return (value.replace("&quot;", '"').replace("&#34;", '"')
            .replace("&#39;", "'").replace("&amp;", "&"))


def test_preview_requires_file(client):
    r = client.post("/import/preview")
    assert r.status_code == 302
    assert "/profile" in r.headers["Location"]


def test_preview_rejects_empty_upload(client, seed_payload):
    empty = {"backup_file": (io.BytesIO(b""), "empty.json")}
    r = client.post("/import/preview", data=empty, content_type="multipart/form-data",
                    follow_redirects=True)
    assert "empty" in r.get_data(as_text=True)


def test_preview_rejects_invalid_json(client):
    data = {"backup_file": (io.BytesIO(b"not json"), "bad.json")}
    r = client.post("/import/preview", data=data, content_type="multipart/form-data",
                    follow_redirects=True)
    assert "not valid JSON" in r.get_data(as_text=True)


def test_preview_renders_report(client, seed_payload):
    r = _preview_html(client, seed_payload)
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "Import Preview" in body
    assert "4 added" in body          # sub_activities
    assert "Context Switch" in body   # near-duplicate advisory
    assert "100" in body and "160" in body  # recompute preview


def test_reviewed_import_applies(client, seed_payload):
    r = _preview_html(client, seed_payload)
    plan = _plan_from(r.get_data(as_text=True))
    confirm = client.post("/import", data={"plan_json": json.dumps(plan)},
                          follow_redirects=True)
    assert "activities" in confirm.get_data(as_text=True)

    with client.session_transaction() as sess:
        user_id = sess["user_id"]
    user = User.query.get(user_id)
    assert user.total_exp == 160
    assert Activity.query.filter_by(user_id=user.id).count() == 4
    assert CompletionLog.query.filter_by(user_id=user.id).count() == 5
    assert JudgeReview.query.filter_by(user_id=user.id).count() == 2


def test_confirm_without_plan_redirects(client):
    r = client.post("/import", follow_redirects=True)
    assert "no merge plan" in r.get_data(as_text=True).lower()


def test_confirm_disabled_when_nothing_new(client, seed_payload):
    r = _preview_html(client, seed_payload)
    plan = _plan_from(r.get_data(as_text=True))
    client.post("/import", data={"plan_json": json.dumps(plan)})

    again = _preview_html(client, seed_payload).get_data(as_text=True)
    assert "disabled" in again
    assert "Nothing new to import" in again


def test_export_downloads_json(client):
    r = client.get("/export")
    assert r.status_code == 200
    body = json.loads(r.get_data(as_text=True))
    assert body["format"] == "taskquest-backup"
    assert body["schema_version"] == 2
    assert "Content-Disposition" in r.headers and "attachment" in r.headers["Content-Disposition"]


def test_import_requires_login(app, seed_payload):
    anon = app.test_client()
    data = {"backup_file": (io.BytesIO(json.dumps(seed_payload).encode()), "b.json")}
    assert anon.post("/import/preview", data=data,
                     content_type="multipart/form-data").status_code == 302
    assert anon.post("/import", data={"plan_json": "{}"}).status_code == 302
    assert anon.get("/export").status_code == 302