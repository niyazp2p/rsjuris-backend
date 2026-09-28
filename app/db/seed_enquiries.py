import asyncio
import uuid
from datetime import datetime
from sqlalchemy.future import select

from app.db.session import AsyncSessionLocal
from app.models.enquiry import Enquiry
from app.models.enums import EnquiryStatus, MatterType

SAMPLE_ENQUIRIES = [
    {
        "full_name": "Aditi Sharma",
        "phone": "+91 98100 12345",
        "email": "aditi.sharma@innovatetech.io",
        "matter_type": MatterType.CORPORATE_COMMERCIAL,
        "summary": "Urgent shareholder dispute and breach of Master Service Agreement covenants regarding IP ownership prior to initiation of corporate insolvency or NCLT filings.",
        "status": EnquiryStatus.NEW,
    },
    {
        "full_name": "Meera Nair",
        "phone": "+91 97112 44321",
        "email": "meera.nair@outlook.com",
        "matter_type": MatterType.CIVIL_LITIGATION,
        "summary": "Seeking urgent ex-parte ad-interim injunction before the High Court regarding breach of commercial agreement and recovery of security deposits.",
        "status": EnquiryStatus.CONTACTED,
    },
    {
        "full_name": "Vikramaditya Singhania",
        "phone": "+91 98200 99881",
        "email": "v.singhania@apexholding.com",
        "matter_type": MatterType.CRIMINAL_LAW,
        "summary": "Notice received under Section 41A CrPC. Seeking urgent anticipatory bail application before Sessions Court and strategic trial advocacy.",
        "status": EnquiryStatus.NEW,
    },
    {
        "full_name": "Siddharth Oberoi",
        "phone": "+91 98110 55432",
        "email": "siddharth.oberoi@gmail.com",
        "matter_type": MatterType.PROPERTY_REAL_ESTATE,
        "summary": "Builder-buyer dispute concerning delay in possession of commercial IT space; require filing under RERA Authority and adjudication for complete refund with interest.",
        "status": EnquiryStatus.CONTACTED,
    },
    {
        "full_name": "Apex Logistics Private Limited",
        "phone": "+91 11 2341 9988",
        "email": "legal@apexlogistics.in",
        "matter_type": MatterType.BANKING_FINANCIAL,
        "summary": "Challenging notice issued under Section 13(2) of SARFAESI Act before the Debt Recovery Tribunal (DRT); seeking stay of asset possession and restructuring counsel.",
        "status": EnquiryStatus.NEW,
    },
]

async def seed_enquiries():
    async with AsyncSessionLocal() as db:
        year = datetime.utcnow().year
        for idx, item in enumerate(SAMPLE_ENQUIRIES, start=1001):
            ref = f"RSJ-ENQ-{year}-{idx}"
            
            existing = await db.execute(select(Enquiry).where(Enquiry.reference_number == ref))
            if existing.scalar_one_or_none():
                continue

            enquiry = Enquiry(
                id=str(uuid.uuid4()),
                reference_number=ref,
                full_name=item["full_name"],
                phone=item["phone"],
                email=item["email"],
                matter_type=item["matter_type"],
                summary=item["summary"],
                status=item["status"],
                ip_address="127.0.0.1",
                user_agent="RS-Juris-Web-Client/1.0"
            )
            db.add(enquiry)

        await db.commit()
        print("✓ Successfully seeded contact enquiries into Neon!")

if __name__ == "__main__":
    asyncio.run(seed_enquiries())