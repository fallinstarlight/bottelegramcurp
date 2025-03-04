import logging
import re
import datetime

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

replymanager = 0

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Expresión regular para detectar mensajes que contienen "Hola"
expresion_regular = re.compile(r"hello|hi|hey|hola", re.IGNORECASE)
solicitud = re.compile(r"CURP|pasaporte|acta|cartilla|consrancia", re.IGNORECASE)
curpexpression = re.compile(r"^[A-Z][AEIOU][A-Z]{2}\d{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])[HM](AS|BC|BS|CC|CS|CH|DF|CL|CM|DG|GT|GR|HG|JC|MC|MN|MS|NT|OC|PL|QO|QR|SP|SL|SR|TC|TS|TL|VZ|YN|ZS|NE)[BCDFGHJKLMNÑPQRSTVWXYZ]{3}[0-9A-Z]{2}$")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message if it matches the regular expression."""
    message_text = update.message.text
    if "replymanager" not in context.user_data:
        context.user_data["replymanager"] = 0
    
    if context.user_data["replymanager"] == 0:
        if expresion_regular.search(message_text):
            await update.message.reply_text("¡Hola! ¿En qué te puedo ayudar?") 
        elif solicitud.search(message_text):
            await update.message.reply_text("Porfavor ingresa tu CURP")
            context.user_data["replymanager"] = 1
        else:
            await update.message.reply_text("No entendí tu mensaje.")
    elif context.user_data["replymanager"] == 1:
        if curpexpression.search(message_text):
            await update.message.reply_text("Gracias por ingresar tu curp, tu solicitud será procesada")
            context.user_data["replymanager"] = 0
        else:
            await update.message.reply_text(validate_id(message_text))        
           
def main() -> None:
    """Start the bot."""
    application = Application.builder().token("######").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

valid_states = {"AS", "BC", "BS", "CC", "CS", "CH", "DF", "CL", "CM", "DG", "GT", "GR", 
                "HG", "JC", "MC", "MN", "MS", "NT", "OC", "PL", "QO", "QR", "SP", "SL", 
                "SR", "TC", "TS", "TL", "VZ", "YN", "ZS", "NE"}

def validate_id(id_str) -> None:
    errors = ["Tu CURP no puede ser procesado pues contiene los siguientes errores: "]
    # 1. Length check
    if len(id_str) != 18:
        errors.append("El CURP debe de contener 18 caracteres.")
        return errors  # Stop further checks

    # 2. First letter must be uppercase
    if not re.match(r"^[A-Z]", id_str[0]):
        errors.append("El primer caracter debe de ser una letra mayuscula.")

    # 3. Second letter must be an uppercase vowel
    if not re.match(r"^[AEIOU]", id_str[1]):
        errors.append("El segundo caracter debe de ser una vocal mayuscula (A, E, I, O, U).")

    # 4. Third & Fourth letters must be uppercase
    if not re.match(r"^[A-Z]{2}", id_str[2:4]):
        errors.append("Los caracteres tres y cuatro deben de ser letras mayusculas.")

    # 5. Year (YY)
    if not re.match(r"^\d{2}", id_str[4:6]):
        errors.append("Caracteres cinco y seis deben de ser dos numeros que representen un año.")

    # 6. Month (MM)
    month = id_str[6:8]
    if not re.match(r"^(0[1-9]|1[0-2])$", month):
        errors.append("Los caracteres siete y ocho deben de representar un mes valido (01-12).")

    # 7. Day (DD)
    day = id_str[8:10]
    if not re.match(r"^(0[1-9]|[12][0-9]|3[01])$", day):
        errors.append("Caracteres nueve y diez deben de representar un dia valido  (01-31).")

    # 8. Validate actual date (checking leap years)
    try:
        year = int(id_str[4:6]) + (1900 if int(id_str[4:6]) >= 50 else 2000)  # Adjust YY to YYYY
        datetime.datetime(year, int(month), int(day))
    except ValueError:
        errors.append("El dia y el mes no coinciden o no son validos.")

    # 9. Sex character must be 'H' or 'M'
    if id_str[10] not in "HM":
        errors.append("El decimo primer caracter debe de ser una letra H (Hombre) o M (Mujer).")

    # 10. Validate state code
    state_code = id_str[11:13]
    if state_code not in valid_states:
        errors.append(f"Caracteres 12 y 13 deben de ser un codigo de estado valido (se obtuvo: '{state_code}').")

    # 11. Next 3 characters must be uppercase consonants
    if not re.match(r"^[BCDFGHJKLMNÑPQRSTVWXYZ]{3}$", id_str[13:16]):
        errors.append("Caracteres catorce, quince y dieciseis deben de ser consonantes mayusculas.")

    # 12. Last 2 characters must be alphanumeric
    if not re.match(r"^[0-9A-Z]{2}$", id_str[16:]):
        errors.append("Caracteres diecisite y dieciocho deben de ser alfanumericos (0-9 o A-Z).")

    return errors
if __name__ == "__main__":
    main()
