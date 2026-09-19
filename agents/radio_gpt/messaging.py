import os

from dotenv import load_dotenv
from vonage import Auth, Vonage
from vonage_messages import Sms


PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../.."
    )
)

env_path = os.path.join(
    PROJECT_ROOT,
    ".env"
)

load_dotenv(env_path)


def send_sms(
    phone_number: str,
    message_text: str
):
    application_id = os.getenv(
        "VONAGE_APPLICATION_ID"
    )

    private_key_path = os.getenv(
        "VONAGE_PRIVATE_KEY_PATH"
    )

    sender_id = os.getenv(
        "VONAGE_SMS_SENDER_ID"
    )

    if not application_id:
        raise Exception(
            "VONAGE_APPLICATION_ID is missing from .env"
        )

    if not private_key_path:
        raise Exception(
            "VONAGE_PRIVATE_KEY_PATH is missing from .env"
        )
    if not os.path.isabs(private_key_path):
        private_key_path = os.path.join(
            PROJECT_ROOT,
            private_key_path
        )
    if not os.path.isfile(private_key_path):
        raise Exception(
            f"Private key not found: {private_key_path}"
        )

    if not sender_id:
        raise Exception(
            "VONAGE_SMS_SENDER_ID is missing from .env"
        )

    with open(
        private_key_path,
        "r",
        encoding="utf-8"
    ) as key_file:
        private_key = key_file.read()

    client = Vonage(
        Auth(
            application_id=application_id,
            private_key=private_key
        )
    )

    response = client.messages.send(
        Sms(
            to=phone_number,
            from_=sender_id,
            text=message_text
        )
    )

    return {
        "status": "sms_sent",
        "message_uuid": getattr(
            response,
            "message_uuid",
            None
        ),
        "to": phone_number,
        "from": sender_id
    }
