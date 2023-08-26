from enum import Enum


class RequestStatus:
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    NOT_CLEAR = "NOT_CLEAR"
    INVALID = "INVALID"

    @staticmethod
    def get_choices():
        return (
            (RequestStatus.RECEIVED, "تم إستلام الطلب"),
            (RequestStatus.PROCESSING, "بصدد  معالجة الطلب"),
            (RequestStatus.ACCEPTED, "تمت الموافقة على الطلب"),
            (RequestStatus.REJECTED, "تعذر على البلدية الموافقة على الطلب"),
            (RequestStatus.NOT_CLEAR, "المطلب منقوص أو غير مفهوم"),
            (RequestStatus.INVALID, "الوثيقة المطلوبة ليست من مشمولات البلدية"),
        )

    @staticmethod
    def get_choices_complaints():
        return (
            (RequestStatus.RECEIVED, "تم تلقي المشكل"),
            (RequestStatus.PROCESSING, "البلدية بصدد حل المشكل"),
            (RequestStatus.ACCEPTED, "تم حل المشكل بنجاح"),
            (RequestStatus.REJECTED, "تعذر على البلدية حل المشكل"),
            (RequestStatus.NOT_CLEAR, "معطيات منقوصة أو غير مفهومة"),
            (RequestStatus.INVALID, "التشكي ليس من مشمولات البلدية"),
        )

    @staticmethod
    def get_choices_comments():
        return (
            (RequestStatus.RECEIVED, "تم تسجيل المقترح للعرض على المجلس البلدي"),
            (RequestStatus.PROCESSING, "المقترح في طور النقاش"),
            (RequestStatus.ACCEPTED, "تم تبني المقترح"),
            (RequestStatus.REJECTED, "تعذر على البلدية تبني المقترح"),
        )

    @staticmethod
    def get_statuses():
        return [status[0] for status in RequestStatus.get_choices()]


class ReactionsTypes:
    """Include several reaction types (like, angry, hahaha...)"""

    LIKE = "L"

    @staticmethod
    def get_choices():
        return ((ReactionsTypes.LIKE, "Like"),)


class ReactionPostsTypes:
    """Include several reaction post types (comment, news...)"""

    COMMENT = "COMMENT"
    NEWS = "NEWS"
    COMPLAINT = "COMPLAINT"

    @staticmethod
    def get_choices():
        return (
            (ReactionPostsTypes.NEWS, "NEWS"),
            (ReactionPostsTypes.COMMENT, "COMMENT"),
            (ReactionPostsTypes.COMPLAINT, "COMPLAINT"),
        )


class OsTypes:
    ANDROID = "ANDROID"
    IOS = "IOS"
    OTHER = "OTHER"

    @staticmethod
    def get_choices():
        return (
            (OsTypes.ANDROID, "Android"),
            (OsTypes.IOS, "iOS"),
            (OsTypes.OTHER, "Other"),
        )


class DossierTypes:
    BUILDING = "BUILDING"
    TEMPORARY_WORKS = "TEMPORARY_WORKS"
    TAKSIM = "TAKSIM"
    STREET = "STREET"
    ONAS = "ONAS"
    NETWORKS = "NETWORKS"
    SONEDE = "SONEDE"
    ELECTRICITY = "ELECTRICITY"
    GAZ = "GAZ"
    OTHER = "OTHER"

    @staticmethod
    def get_choices():
        return (
            (DossierTypes.BUILDING, "رخصة بناء"),
            (DossierTypes.TEMPORARY_WORKS, "رخصة في الأشغال الوقتية"),
            (DossierTypes.TAKSIM, "رخصة المصادقة على تقسيم"),
            (DossierTypes.STREET, "رخصة الاستغلال الوقتي للطريق العام"),
            (DossierTypes.NETWORKS, "ربط بالشبكات العمومية"),
            (DossierTypes.SONEDE, "ربط بشبكة المياه"),
            (DossierTypes.ONAS, "ربط بشبكة التطهير"),
            (DossierTypes.ELECTRICITY, "ربط بشبكة الكهرباء"),
            (DossierTypes.GAZ, "ربط بشبكة الغاز"),
            (DossierTypes.OTHER, "غير محدد"),
        )

    @staticmethod
    def translate(type):
        return {
            status: translation for (status, translation) in DossierTypes.get_choices()
        }.get(type)


class ProcedureTypes:
    ADMINISTRATIVE = "خدمات إدارية"
    CIVIL_STATUS = "خدمات الحالة المدنية"
    URBAN = "خدمات عمرانية"
    REGULATORY = "خدمات ترتيبية"
    FINANCIAL = "خدمات مالية"
    OTHER = "خدمات مختلفة"

    @staticmethod
    def get_choices():
        return (
            (ProcedureTypes.ADMINISTRATIVE, "خدمات إدارية"),
            (ProcedureTypes.CIVIL_STATUS, "خدمات الحالة المدنية"),
            (ProcedureTypes.URBAN, "خدمات عمرانية"),
            (ProcedureTypes.REGULATORY, "خدمات ترتيبية"),
            (ProcedureTypes.FINANCIAL, "خدمات مالية"),
            (ProcedureTypes.OTHER, "خدمات مختلفة"),
        )


TUNISIA_CITIES_LIST = [
    "باجة",
    "أريانة",
    "سيدي بوزيد",
    "منوبة",
    "قفصة",
    "المنستير",
    "توزر",
    "جندوبة",
    "سوسة",
    "تونس",
    "القصرين",
    "قابس",
    "القيروان",
    "سليانة",
    "مدنين",
    "بن عروس",
    "قبلي",
    "صفاقس",
    "تطاوين",
    "نابل",
    "زغوان",
    "الكاف",
    "المهدية",
    "بنزرت",
]


class TunisianCities:
    @staticmethod
    def get_choices():
        return map(lambda elem: (elem, elem), TUNISIA_CITIES_LIST)


class CachePrefixes:
    REGISTER = "REGISTER"
    RESET = "RESET"


class TransporationMethods(Enum):
    WALKING = 20  # Assume it takes 20 minutes to walk 1 kilometer
    BIKING = 10  # Assume it takes 10 minutes to bike 1 kilometer
    DRIVING = 5


class MunicipalityPermissions:
    MANAGE_DOSSIERS = "MANAGE_DOSSIERS"
    MANAGE_PROCEDURES = "MANAGE_PROCEDURES"
    MANAGE_COMPLAINTS = "MANAGE_COMPLAINTS"
    MANAGE_REPORTS = "MANAGE_REPORTS"
    MANAGE_SUBJECT_ACCESS_REQUESTS = "MANAGE_SUBJECT_ACCESS_REQUESTS"
    MANAGE_COMMITTEES = "MANAGE_COMMITTEES"
    MANAGE_NEWS = "MANAGE_NEWS"
    MANAGE_EVENTS = "MANAGE_EVENTS"
    MANAGE_PERMISSIONS = "MANAGE_PERMISSIONS"
    MANAGE_APPOINTMENTS = "MANAGE_APPOINTMENTS"
    MANAGE_FORUM = "MANAGE_FORUM"
    MANAGE_POLLS = "MANAGE_POLLS"
    MANAGE_ETICKET = "MANAGE_ETICKET"

    @staticmethod
    def get_choices():
        return (
            ("MANAGE_DOSSIERS", "Gerer les dossiers et demandes"),
            ("MANAGE_PROCEDURES", "Gérer les procedures de la commune"),
            ("MANAGE_COMPLAINTS", "Gérer les plaintes des citoyens"),
            ("MANAGE_REPORTS", "Gerer les rapports du conseil municipal"),
            (
                "MANAGE_SUBJECT_ACCESS_REQUESTS",
                "Gerer les demandes d'acces à l'information",
            ),
            ("MANAGE_COMMITTEES", "Gerer les comités du conseil municipal"),
            ("MANAGE_NEWS", "Gerer les actualités de la commune"),
            ("MANAGE_EVENTS", "Gerer les événements"),
            (
                "MANAGE_PERMISSIONS",
                "Gerer les permissions de chaque membre sur la plateforme",
            ),
            ("MANAGE_APPOINTMENTS", "Gerer les rendez-vous"),
            ("MANAGE_FORUM", "Gerer le forum"),
            ("MANAGE_POLLS", "Gerer les sondages"),
            ("MANAGE_ETICKET", "Gerer le service e-ticket"),
        )


class SMSAPIType:
    Dev = "Dev"
    Orange = "Orange"


class ResetPasswordTypes:
    SMS = "SMS"
    EMAIL = "EMAIL"

    @staticmethod
    def get_choices():
        return (
            (ResetPasswordTypes.SMS, "SMS"),
            (ResetPasswordTypes.EMAIL, "EMAIL"),
        )


class SMSBroadcastRequestStatus:
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    SENDING = "SENDING"
    SENT = "SENT"
    DECLINED = "DECLINED"

    @staticmethod
    def get_choices():
        return (
            (SMSBroadcastRequestStatus.PENDING, "PENDING"),
            (SMSBroadcastRequestStatus.APPROVED, "APPROVED"),
            (SMSBroadcastRequestStatus.SENDING, "SENDING"),
            (SMSBroadcastRequestStatus.SENT, "SENT"),
            (SMSBroadcastRequestStatus.DECLINED, "DECLINED"),
        )


class SMSBroadcastRequestTarget:
    REGISTERED_CITIZENS = "REGISTERED_CITIZENS"
    FOLLOWING_CITIZENS = "FOLLOWING_CITIZENS"
    ALL_CITIZENS = "ALL_CITIZENS"
    CUSTOM = "CUSTOM"
    INACTIVE_CITIZENS = "INACTIVE_CITIZENS"

    @staticmethod
    def get_choices():
        return (
            (SMSBroadcastRequestTarget.REGISTERED_CITIZENS, "REGISTERED_CITIZENS"),
            (SMSBroadcastRequestTarget.FOLLOWING_CITIZENS, "FOLLOWING_CITIZENS"),
            (SMSBroadcastRequestTarget.ALL_CITIZENS, "ALL_CITIZENS"),
            (SMSBroadcastRequestTarget.CUSTOM, "CUSTOM"),
            (SMSBroadcastRequestTarget.INACTIVE_CITIZENS, "INACTIVE_CITIZENS"),
        )


class NewsCategory:
    ANNOUNCEMENT = "بلاغ"
    ACTIVITIES_AND_EVENTS = "أنشطة وتظاهرات"
    WORKS_AND_MAINTENANCE = "أشغال و صيانة"
    CALL_FOR_TENDER = "طلب عروض"
    JOB_OFFERS = "عروض شغل"

    @staticmethod
    def get_choices():
        return (
            (NewsCategory.ANNOUNCEMENT, "بلاغ"),
            (NewsCategory.ACTIVITIES_AND_EVENTS, "أنشطة وتظاهرات"),
            (NewsCategory.WORKS_AND_MAINTENANCE, "أشغال و صيانة"),
            (NewsCategory.CALL_FOR_TENDER, "طلب عروض"),
            (NewsCategory.JOB_OFFERS, "عروض شغل"),
        )


class ForumTypes:
    QUESTION = "QUESTION"
    SUGGESTION = "SUGGESTION"
    REMARK = "REMARK"

    @staticmethod
    def get_choices():
        return (
            (ForumTypes.QUESTION, "سؤال"),
            (ForumTypes.SUGGESTION, "مقترح"),
            (ForumTypes.REMARK, "ملاحظة"),
        )


class GenderType:
    MALE = "MALE"
    FEMALE = "FEMALE"

    @staticmethod
    def get_choices():
        return (
            (GenderType.MALE, "ذكر"),
            (GenderType.FEMALE, "أنثى"),
        )


class TopicStates:
    ACTIVATED = "ACTIVATED"
    ARCHIVED = "ARCHIVED"
    HIDDEN = "HIDDEN"

    @staticmethod
    def get_choices():
        return (
            (TopicStates.ACTIVATED, "مفتوح"),
            (TopicStates.ARCHIVED, "مغلق"),
            (TopicStates.HIDDEN, "مخفي"),
        )


class StatusLabel:
    COMPLAINT = "COMPLAINT"
    DOSSIER = "DOSSIER"
    SUBJECT_ACCESS_REQUEST = "SUBJECT_ACCESS_REQUEST"
    SUGGESTION = "SUGGESTION"
    QUESTION = "QUESTION"
    REMARK = "REMARK"

    @staticmethod
    def get_choices():
        return {
            "FRONTOFFICE_LABEL": {
                StatusLabel.COMPLAINT: {
                    RequestStatus.RECEIVED: "تم إستلام المشكل",
                    RequestStatus.PROCESSING: "المشكل بصدد المعالجة",
                    RequestStatus.ACCEPTED: "تم حل المشكل",
                    RequestStatus.REJECTED: "تعذر على البلدية معالجة المشكل",
                    RequestStatus.NOT_CLEAR: "المشكل غير واضح",
                    RequestStatus.INVALID: "المشكل خارج نطاق عمل البلدية",
                },
                StatusLabel.SUBJECT_ACCESS_REQUEST: {
                    RequestStatus.RECEIVED: "تم إستلام المطلب",
                    RequestStatus.PROCESSING: "المطلب بصدد المعالجة",
                    RequestStatus.ACCEPTED: "تم الموافقة على المطلب",
                    RequestStatus.REJECTED: "تعذر على البلدية الموافقة على المطلب",
                    RequestStatus.NOT_CLEAR: "المطلب غير واضح",
                    RequestStatus.INVALID: "المطلب خارج مشمولات البلدية",
                },
                StatusLabel.DOSSIER: {
                    RequestStatus.RECEIVED: "تم إستلام المطلب",
                    RequestStatus.PROCESSING: "المطلب بصدد المعالجة",
                    RequestStatus.ACCEPTED: "تم الموافقة على المطلب",
                    RequestStatus.REJECTED: "تعذر على البلدية الموافقة على المطلب",
                    RequestStatus.NOT_CLEAR: "المطلب غير واضح",
                    RequestStatus.INVALID: "المطلب خارج نطاق عمل البلدية",
                },
                StatusLabel.SUGGESTION: {
                    RequestStatus.RECEIVED: "مقترح مفتوح للنقاش",
                    RequestStatus.PROCESSING: "تم التسجيل للعرض على المجلس البلدي",
                    RequestStatus.ACCEPTED: "تم تبني المقترح",
                    RequestStatus.REJECTED: "تعذر على البلدية تبني المقترح",
                    RequestStatus.NOT_CLEAR: "مقترح غير واضح",
                    RequestStatus.INVALID: "المقترح خارج نطاق عمل البلدية",
                },
                StatusLabel.QUESTION: {
                    RequestStatus.RECEIVED: "السؤال مفتوح للإجابة",
                    RequestStatus.PROCESSING: "تم التسجيل للعرض على المجلس البلدي",
                    RequestStatus.ACCEPTED: "تم الإجابة على السؤال",
                    RequestStatus.REJECTED: "تعذر الإجابة",
                    RequestStatus.NOT_CLEAR: "السؤال غير واضح",
                    RequestStatus.INVALID: "السؤال خارج نطاق عمل البلدية",
                },
                StatusLabel.REMARK: {
                    RequestStatus.RECEIVED: "الملاحظة مفتوحة للنقاش",
                    RequestStatus.PROCESSING: "تم التسجيل للعرض على المجلس البلدي",
                    RequestStatus.ACCEPTED: "تم التداول في الملاحظة",
                    RequestStatus.REJECTED: "تم نفي الملاحظة",
                    RequestStatus.NOT_CLEAR: "الملاحظة غير واضحة",
                    RequestStatus.INVALID: "الملاحظة خارج نطاق عمل البلدية",
                },
            },
            "BACKOFFICE_LABEL": {
                StatusLabel.COMPLAINT: {
                    RequestStatus.RECEIVED: "غير معالج",
                    RequestStatus.PROCESSING: "بصدد المعالجة",
                    RequestStatus.ACCEPTED: "تم الانجاز",
                    RequestStatus.REJECTED: "تعذر الانجاز",
                    RequestStatus.NOT_CLEAR: "غير واضح",
                    RequestStatus.INVALID: "خارج مشمولات البلدية",
                },
                StatusLabel.DOSSIER: {
                    RequestStatus.RECEIVED: "غير معالج",
                    RequestStatus.PROCESSING: "بصدد المعالجة",
                    RequestStatus.ACCEPTED: "تمت الموافقة",
                    RequestStatus.REJECTED: "لم تتم الموافقة",
                    RequestStatus.NOT_CLEAR: "غير واضح",
                    RequestStatus.INVALID: "خارج مشمولات البلدية",
                },
                StatusLabel.SUBJECT_ACCESS_REQUEST: {
                    RequestStatus.RECEIVED: "غير معالج",
                    RequestStatus.PROCESSING: "بصدد المعالجة",
                    RequestStatus.ACCEPTED: "تمت الموافقة",
                    RequestStatus.REJECTED: "لم تتم الموافقة",
                    RequestStatus.NOT_CLEAR: "غير واضح",
                    RequestStatus.INVALID: "خارج مشمولات البلدية",
                },
                StatusLabel.SUGGESTION: {
                    RequestStatus.RECEIVED: "مفتوح للنقاش",
                    RequestStatus.PROCESSING: "مسجل للعرض على المجلس",
                    RequestStatus.ACCEPTED: "تم تبني المقترح",
                    RequestStatus.REJECTED: "لم تتم الموافقة",
                    RequestStatus.NOT_CLEAR: "غير واضح",
                    RequestStatus.INVALID: "خارج مشمولات البلدية",
                },
                StatusLabel.QUESTION: {
                    RequestStatus.RECEIVED: "مفتوح للنقاش",
                    RequestStatus.PROCESSING: "بصدد المعالجة",
                    RequestStatus.ACCEPTED: "تمت الموافقة",
                    RequestStatus.REJECTED: "لم تتم الموافقة",
                    RequestStatus.NOT_CLEAR: "غير واضح",
                    RequestStatus.INVALID: "خارج مشمولات البلدية",
                },
                StatusLabel.REMARK: {
                    RequestStatus.RECEIVED: "مفتوحة للنقاش",
                    RequestStatus.PROCESSING: "مسجل للعرض على المجلس",
                    RequestStatus.ACCEPTED: "تم التداول",
                    RequestStatus.REJECTED: "تم النفي",
                    RequestStatus.NOT_CLEAR: "غير واضح",
                    RequestStatus.INVALID: "خارج مشمولات البلدية",
                },
            },
        }
