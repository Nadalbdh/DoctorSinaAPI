from backend.models import Municipality
from utils.SMSManager import SMSManager


class NotifyCitizensService:
    SMS_TEMPLATES = {
        "sms_for_active_citizens": """
        يسرنا إعلامكم بانضمام بلدية التسجيل الخاصة لمنصة elbaladiya.tn.
        تمتع الآن بخدمات بلدية {} المفعلة يمكنكم تحميل تطبيقة الهاتف الضغط على هذا الرابط:
        elbaladiya.tn
        """,
        "sms_for_inactive_citizens": """
        يسرنا إعلامكم بانضمام بلدية التسجيل الخاصة لمنصة elbaladiya.tn.
        لا يزال بإمكانك تفعيل حسابك للتمتع بالخدمات الرقمية لبلدية {} المفعلة عبر هذا الرابط:
        elbaladiya.tn/reset
        """,
    }

    def __init__(self, municipality: Municipality):
        self.municipality = municipality

    def notify_all_active_citizens(self):
        for citizen in self.municipality.registered_citizens.all():
            sms_content = self.SMS_TEMPLATES[
                "sms_for_active_citizens"
                if citizen.user.is_active
                else "sms_for_inactive_citizens"
            ].format(
                self.municipality.name,
            )
            SMSManager.send_sms(citizen.user.username, sms_content)
