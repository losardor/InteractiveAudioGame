import logging
import os

from flask import render_template
from flask_mail import Message

from app import create_app, mail

logger = logging.getLogger(__name__)


def send_email(recipient, subject, template, **kwargs):
    """
    Send a transactional email. Runs inside an RQ worker — exceptions
    must be caught and logged here, otherwise they disappear silently.
    """
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    with app.app_context():
        logger.info(
            'Sending email: recipient=%s subject=%r template=%s',
            recipient, subject, template
        )
        try:
            msg = Message(
                app.config['EMAIL_SUBJECT_PREFIX'] + ' ' + subject,
                sender=app.config['EMAIL_SENDER'],
                recipients=[recipient])
            msg.body = render_template(template + '.txt', **kwargs)
            msg.html = render_template(template + '.html', **kwargs)
            mail.send(msg)
            logger.info(
                'Email sent successfully: recipient=%s subject=%r',
                recipient, subject
            )
        except Exception as e:
            logger.error(
                'Email send FAILED: recipient=%s subject=%r error=%s',
                recipient, subject, str(e),
                exc_info=True  # includes full traceback in the log
            )
            raise  # re-raise so RQ marks the job as failed
