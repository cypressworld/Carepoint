from flask import current_app, flash
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db


def commit_with_feedback(success_message):
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("Database transaction failed.")
        flash("The change could not be saved. Please try again.", "danger")
        return False

    flash(success_message, "success")
    return True
