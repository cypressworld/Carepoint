from flask import get_flashed_messages
from sqlalchemy.exc import SQLAlchemyError

from app import database


def test_failed_commit_rolls_back_and_flashes_failure(app, monkeypatch):
    rollback_called = False

    def fail_commit():
        raise SQLAlchemyError("database unavailable")

    def record_rollback():
        nonlocal rollback_called
        rollback_called = True

    with app.test_request_context():
        monkeypatch.setattr(database.db.session, "commit", fail_commit)
        monkeypatch.setattr(database.db.session, "rollback", record_rollback)

        assert database.commit_with_feedback("Saved.") is False
        assert rollback_called
        assert get_flashed_messages(with_categories=True) == [
            ("danger", "The change could not be saved. Please try again.")
        ]
