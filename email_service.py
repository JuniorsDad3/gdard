from flask_mail import Mail, Message
from flask import current_app

mail = Mail()

def send_email(to, subject, template):
    try:
        msg = Message(
            subject,
            recipients=[to],
            html=template,
            sender=current_app.config['MAIL_USERNAME']
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Error sending email: {e}")
        return False

def send_alert_notification(farm_id, alert_type, message):
    # Get farm owner email from Excel DB
    excel_db = ExcelDatabase()
    users = excel_db.get_users()
    farms = pd.read_excel(current_app.config['EXCEL_DB_PATH'], sheet_name='farms')
    
    farm = farms[farms['id'] == farm_id].iloc[0]
    owner = users[users['id'] == farm['owner_id']].iloc[0]
    
    subject = f"GDARD Alert: {alert_type} on Farm {farm['name']}"
    template = f"""
    <h2>Smart Agriculture Alert</h2>
    <p>Dear {owner['username']},</p>
    <p>Our system has detected an important alert for your farm:</p>
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
        <h3>{alert_type}</h3>
        <p>{message}</p>
    </div>
    <p>Please log in to your GDARD Smart Agriculture account for more details.</p>
    <p>Best regards,<br>GDARD Smart Agriculture Team</p>
    """
    
    return send_email(owner['email'], subject, template)