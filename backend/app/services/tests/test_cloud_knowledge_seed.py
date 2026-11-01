
import importlib


def test_cloud_knowledge_seed_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "CLOUD_RAG_DB",
        str(tmp_path / "cloud_rag_test.db"),
    )

    from backend.app.services import cloud_rag_service

    importlib.reload(cloud_rag_service)

    try:
        assert cloud_rag_service.seed_cloud_knowledge() == 1
        assert cloud_rag_service.seed_cloud_knowledge() == 0

        documents = cloud_rag_service.list_documents()
        assert len(documents) == 1
        assert documents[0]["filename"].startswith(
            "vpn_troubleshooting.md@"
        )

        matches = cloud_rag_service.search_documents(
            "VPN authentication MFA"
        )
        assert len(matches) > 0
        assert all(
            item["document_id"] == documents[0]["id"]
            for item in matches
        )
    finally:
        monkeypatch.delenv("CLOUD_RAG_DB", raising=False)
        importlib.reload(cloud_rag_service)



def test_cloud_knowledge_retrieval_after_seed(
    tmp_path,
    monkeypatch,
):
    from backend.app.services import cloud_rag_service

    monkeypatch.setattr(
        cloud_rag_service,
        "DB_PATH",
        tmp_path / "fresh_cloud_rag.db",
    )

    assert cloud_rag_service.seed_cloud_knowledge() == 1

    matches = cloud_rag_service.search_documents(
        "VPN authentication MFA"
    )

    assert matches
    assert any(
        "vpn_troubleshooting.md" in item["filename"]
        for item in matches
    )




def test_updated_knowledge_replaces_old_version(
    tmp_path,
    monkeypatch,
):
    from backend.app.services import cloud_rag_service

    monkeypatch.setattr(
        cloud_rag_service,
        "DB_PATH",
        tmp_path / "version_test.db",
    )

    assert cloud_rag_service.seed_cloud_knowledge() == 1

    original = cloud_rag_service.list_documents()
    assert len(original) == 1

    old_id = original[0]["id"]
    old_filename = original[0]["filename"]

    # Simulate an older indexed version of the same runbook.
    with cloud_rag_service.connect() as db:
        db.execute(
            "UPDATE documents SET filename = ? WHERE id = ?",
            ("vpn_troubleshooting.md@oldversion", old_id),
        )

    assert cloud_rag_service.seed_cloud_knowledge() == 1

    updated = cloud_rag_service.list_documents()

    assert len(updated) == 1
    assert updated[0]["filename"] == old_filename
    assert updated[0]["id"] != old_id

    with cloud_rag_service.connect() as db:
        old_chunks = db.execute(
            "SELECT COUNT(*) FROM chunks WHERE document_id = ?",
            (old_id,),
        ).fetchone()[0]

    assert old_chunks == 0
