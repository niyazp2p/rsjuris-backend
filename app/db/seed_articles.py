import asyncio
from datetime import datetime
from sqlalchemy.future import select
from app.db.session import AsyncSessionLocal
from app.models.cms import Article
from app.models.user import User
from app.models.enums import ContentStatus, AudienceSegment

SAMPLE_ARTICLES = [
    {
        "title": "Corporate Insolvency Resolution Under the IBC: 2026 Jurisprudential Trends",
        "slug": "corporate-insolvency-resolution-ibc-2026-trends",
        "practice_area": "Corporate & Commercial Law",
        "target_audience": AudienceSegment.BUSINESS,
        "summary": "An in-depth analysis of recent Supreme Court and NCLAT rulings redefining Section 7 admission thresholds and personal guarantor obligations.",
        "content": "<h2>Evolution of Resolution Frameworks</h2><p>The Insolvency and Bankruptcy Code (IBC) has witnessed significant doctrinal refinement regarding Section 7 admissions, operational debt disputes under Section 9, and the liability of personal corporate guarantors.</p><blockquote>The Supreme Court in landmark pronouncements affirmed that frivolous insolvency petitions cannot substitute commercial debt recovery suits.</blockquote><h3>Key Takeaways for Boardrooms</h3><p>Corporate debtors and financial creditors must conduct exhaustive statutory audits prior to initiating CIRP proceedings before NCLT benches.</p>",
        "reading_time_min": 4,
        "meta_title": "IBC 2026 Legal Insights | RS Juris & Co.",
        "meta_description": "Comprehensive briefing on NCLAT and Supreme Court insolvency doctrine in 2026 by RS Juris & Co. Advocates.",
        "status": ContentStatus.PUBLISHED,
        "cover_image_url": "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "title": "Arbitration Agreements & Judicial Intervention: The Section 11 Doctrine",
        "slug": "arbitration-agreements-judicial-intervention-section-11",
        "practice_area": "Arbitration & Alternative Dispute Resolution",
        "target_audience": AudienceSegment.BUSINESS,
        "summary": "Examining the minimal judicial intervention rule when High Courts appoint sole arbitrators under the Arbitration and Conciliation Act.",
        "content": "<h2>Balancing Judicial Restraint and Party Autonomy</h2><p>Section 11 of the Arbitration and Conciliation Act mandates swift reference to arbitration once the existence of a prima facie valid arbitration clause is established.</p><h3>Evidentiary Scrutiny</h3><p>Courts refrain from delving into mini-trials at the referral stage, leaving issues of arbitrability and limitation to the arbitral tribunal.</p>",
        "reading_time_min": 5,
        "meta_title": "Arbitration Section 11 Jurisprudence | RS Juris & Co.",
        "meta_description": "Strategic brief on invoking Section 11 before High Courts for appointment of sole arbitrators.",
        "status": ContentStatus.PUBLISHED,
        "cover_image_url": "https://images.unsplash.com/photo-1450133064473-71024230f91b?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "title": "Ad-Interim Injunctions in Commercial Trademark & Passing Off Suits",
        "slug": "ad-interim-injunctions-trademark-passing-off-suits",
        "practice_area": "Intellectual Property Rights",
        "target_audience": AudienceSegment.BUSINESS,
        "summary": "Strategic trial steps for securing urgent ex-parte ad-interim injunctions in deceptive brand similarity and counterfeit litigation.",
        "content": "<h2>Establishing the Tripartite Standard</h2><p>In trademark infringement actions before Commercial High Court divisions, plaintiffs must establish a prima facie case, balance of convenience, and irreparable injury.</p><p>Immediate inspection of trade dress and deceptive phonetic similarities remains central to winning ex-parte interim injunctions.</p>",
        "reading_time_min": 3,
        "meta_title": "Trademark Injunction Litigation | RS Juris & Co.",
        "meta_description": "Essential guidance on securing ex-parte commercial injunctions in intellectual property disputes.",
        "status": ContentStatus.PUBLISHED,
        "cover_image_url": "https://images.unsplash.com/photo-1505664194779-8beaceb93744?auto=format&fit=crop&w=1200&q=80",
    }
]

async def seed_articles():
    async with AsyncSessionLocal() as db:
        user_res = await db.execute(select(User).where(User.email == "admin@rsjuris.com"))
        admin = user_res.scalar_one_or_none()
        if not admin:
            print("Please run python -m app.db.seed first to create the Super Admin.")
            return

        for art in SAMPLE_ARTICLES:
            existing = await db.execute(select(Article).where(Article.slug == art["slug"]))
            if existing.scalar_one_or_none():
                continue

            article = Article(
                title=art["title"],
                slug=art["slug"],
                practice_area=art["practice_area"],
                target_audience=art["target_audience"],
                summary=art["summary"],
                content=art["content"],
                reading_time_min=art["reading_time_min"],
                meta_title=art["meta_title"],
                meta_description=art["meta_description"],
                status=art["status"],
                cover_image_url=art["cover_image_url"],
                author_id=admin.id,
                published_at=datetime.utcnow(),
            )
            db.add(article)

        await db.commit()
        print("✓ Successfully seeded published legal articles!")

if __name__ == "__main__":
    asyncio.run(seed_articles())