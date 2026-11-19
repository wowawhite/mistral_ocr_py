from pathlib import Path
import pipeline


def test_batch_keeps_failed_document(monkeypatch, tmp_path):
    (tmp_path / "one.jpg").write_bytes(b"x")
    (tmp_path / "two.jpg").write_bytes(b"x")

    def fail(_):
        raise RuntimeError("test failure")

    monkeypatch.setattr(pipeline, "process_image", fail)
    results = pipeline.process_batch(tmp_path)
    assert len(results) == 2
    assert all(item.status == "failed" for item in results)
    assert all(item.page_confidence == 0 for item in results)
