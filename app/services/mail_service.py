from app.core.mail import mail
from app.core.config import settings
from fastapi_mail import MessageSchema, MessageType

class MailService:
    def __init__(self):
        pass

    async def send_password_reset_email(self, email:str, token:str):
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        message = MessageSchema(
            subject="Redefinição de senha",
            recipients=[email], #type: ignore
            body=f"""
                <p>Você solicitou a redefinição de sua senha.</p>
                <p>Clique no link abaixo para continuar. Ele expira em <strong>5 minutos</strong>.</p>
                <p><a href="{reset_link}">Redefinir minha senha</a></p>
                <p>Se você não solicitou isso, ignore este e-mail.</p>
            """,
            subtype=MessageType.html,
        )

        await mail.send_message(message)
        