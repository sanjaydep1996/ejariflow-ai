# Copyright (c) 2026 Sanjaydeep Gowrishankar. Licensed under the MIT License.

"""Bilingual 90-Day Tenancy Renewal Notice Generator (English & Arabic).

Pursuant to:
    - Article 14 of Dubai Law No. 26 of 2007 (as amended by Law No. 33 of 2008)
    - Dubai Decree No. 43 of 2013 on rent increase caps

Generates legally grounded notices for landlords, property managers, and brokerages.
"""

import datetime as dt
from typing import Any, Dict, Optional
from .rera import allowed_increase, check_increase

LAW_CITATION_EN = "Dubai Law No. 26 of 2007 (amended by Law No. 33 of 2008), Article 14 & Dubai Decree No. 43 of 2013"
LAW_CITATION_AR = "المادة (14) من القانون رقم (26) لسنة 2007 المعدل بالقانون رقم (33) لسنة 2008، والمرسوم رقم (43) لسنة 2013"


def generate_90day_notice(
    tenant: str,
    landlord: str,
    property_name: str,
    unit: str,
    area: str,
    current_rent: float,
    average_rent: float,
    lease_end_date: str,
    notice_date: Optional[str] = None,
    proposed_rent: Optional[float] = None,
    ejari_number: Optional[str] = None,
    cheques: int = 4,
) -> Dict[str, Any]:
    """Generates a formal bilingual (English + Arabic) 90-day renewal notice."""
    end_d = dt.date.fromisoformat(lease_end_date)
    notice_d = dt.date.fromisoformat(notice_date) if notice_date else dt.date.today()
    days_notice = (end_d - notice_d).days

    rera_cap = allowed_increase(current_rent, average_rent)
    target_rent = proposed_rent if proposed_rent is not None else rera_cap["max_rent"]
    check = check_increase(current_rent, target_rent, average_rent)

    on_time = days_notice >= 90
    timing_warning = "" if on_time else f"WARNING: Only {days_notice} days notice provided. Dubai Law No. 26 of 2007 requires at least 90 days before contract expiry."
    timing_warning_ar = "" if on_time else f"تنبيه: تم تقديم الإخطار قبل {days_notice} يوماً فقط من انتهاء العقد. يتطلب القانون مهلة لا تقل عن 90 يوماً."

    notice_en = f"""================================================================================
FORMAL NOTICE OF TENANCY CONTRACT RENEWAL & RENT REVISION
Pursuant to {LAW_CITATION_EN}
================================================================================
Date: {notice_d.strftime('%d %B %Y')}

TO (TENANT): {tenant}
FROM (LANDLORD / AUTHORIZED AGENT): {landlord}
PROPERTY: Unit {unit}, {property_name}, {area}, Dubai, United Arab Emirates
EJARI NUMBER: {ejari_number or 'On Record'}
CURRENT TENANCY EXPIRY DATE: {end_d.strftime('%d %B %Y')}

Dear {tenant},

Please be advised that pursuant to Article 14 of Dubai Law No. 26 of 2007 (as amended by Law No. 33 of 2008), this letter serves as formal written notification regarding the upcoming expiration of your tenancy contract on {end_d.strftime('%d %B %Y')}.

In accordance with Dubai Decree No. 43 of 2013, the proposed terms for the renewal of your lease for the upcoming term are as follows:

1. CURRENT ANNUAL RENT: AED {current_rent:,.2f}
2. RERA BENCHMARK AVERAGE RENT: AED {average_rent:,.2f} (Gap: {rera_cap['gap_percent']}%)
3. PERMITTED RERA INCREASE CAP: {rera_cap['max_percent']}% (Max Allowed: AED {rera_cap['max_rent']:,.2f})
4. REVISED PROPOSED ANNUAL RENT: AED {target_rent:,.2f} ({check['proposed_percent']}% increase)
5. PAYMENT TERMS: Payable in {cheques} post-dated cheque(s).

COMPLIANCE VERDICT:
{'[COMPLIANT] The revised rent strictly adheres to Dubai Decree No. 43 of 2013.' if check['compliant'] else f'[NON-COMPLIANT] Proposed rent exceeds RERA cap by AED {check.get("excess", 0):,.2f}.'}

Kindly confirm your intention to renew on the revised terms within thirty (30) days of receipt of this notice, failing which standard legal procedures before the Dubai Land Department and Rental Disputes Centre shall apply.

Sincerely,
{landlord}
"""

    notice_ar = f"""================================================================================
إشعار رسمي بتعديل بدلات وشروط عقد الإيجار
عملاً بأحكام {LAW_CITATION_AR}
================================================================================
التاريخ: {notice_d.strftime('%d %B %Y')}

إلى المستأجر: {tenant}
من المؤجر / الوكيل المعتمد: {landlord}
العقار: الوحدة رقم {unit}، {property_name}، {area}، دبي، الإمارات العربية المتحدة
رقم عقد إيجاري: {ejari_number or 'مسجل لدى الدائرة'}
تاريخ انتهاء عقد الإيجار الحالي: {end_d.strftime('%d %B %Y')}

تحية طيبة وبعد،

عملاً بأحكام المادة (14) من القانون رقم (26) لسنة 2007 بشأن تنظيم العلاقة بين مؤجري ومستأجري العقارات في إمارة دبي (المعدل بالقانون رقم 33 لسنة 2008)، يرجى اعتبار هذا الخطاب إشعاراً رسمياً خطياً بشأن انتهاء عقد إيجاركم الحالي في {end_d.strftime('%d %B %Y')}.

واستناداً إلى معايير حاسبة الإيجارات الصادرة بموجب المرسوم رقم (43) لسنة 2013، فإن الشروط والبدلات المقترحة لتجديد العقد للفترة القادمة هي كما يلي:

1. بدل الإيجار السنوي الحالي: {current_rent:,.2f} درهم إماراتي
2. متوسط أجر المثل المعتمد من ريرا: {average_rent:,.2f} درهم إماراتي (فارق: {rera_cap['gap_percent']}%)
3. النسبة القصوى المصرح بها قانوناً للزيادة: {rera_cap['max_percent']}% (الحد الأقصى: {rera_cap['max_rent']:,.2f} درهم)
4. بدل الإيجار السنوي الجديد المقترح: {target_rent:,.2f} درهم إماراتي (زيادة قدرها {check['proposed_percent']}%)
5. طريقة السداد: بموجب ({cheques}) شيكات مصرفية آجلة.

حالة المطابقة القانونية:
{'[مطابق قانوناً] بدل الإيجار المقترح يلتزم تماماً بالمرسوم رقم (43) لسنة 2013.' if check['compliant'] else f'[مخالف للسقف القانوني] يتجاوز المقترح السقف المعتمد بمقدار {check.get("excess", 0):,.2f} درهم.'}

يرجى التكرم بتأكيد رغبتكم في تجديد العقد بالشروط المذكورة أعلاه خلال ثلاثين (30) يوماً من تاريخ استلام هذا الإخطار ليتسنى لنا توثيق العقد عبر نظام إيجاري.

وتفضلوا بقبول فائق الاحترام والتقدير،
{landlord}
"""

    return {
        "status": "generated",
        "compliant": check["compliant"] and on_time,
        "days_notice_given": days_notice,
        "on_time": on_time,
        "timing_warning": timing_warning,
        "timing_warning_ar": timing_warning_ar,
        "current_rent": current_rent,
        "average_rent": average_rent,
        "max_rent_allowed": rera_cap["max_rent"],
        "proposed_rent": target_rent,
        "increase_percent": check["proposed_percent"],
        "max_increase_percent": rera_cap["max_percent"],
        "citation": LAW_CITATION_EN,
        "notice_en": notice_en,
        "notice_ar": notice_ar,
    }
