import enum

class Role(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    SENIOR_PARTNER = "SENIOR_PARTNER"
    ASSOCIATE_EDITOR = "ASSOCIATE_EDITOR"
    INQUIRY_OFFICER = "INQUIRY_OFFICER"

class EnquiryStatus(str, enum.Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    CONVERTED_TO_LEAD = "CONVERTED_TO_LEAD"
    ARCHIVED = "ARCHIVED"
    SPAM = "SPAM"

class MatterType(str, enum.Enum):
    CORPORATE_COMMERCIAL = "Corporate & Commercial Law"
    CIVIL_LITIGATION = "Civil Litigation & Dispute Resolution"
    CRIMINAL_LAW = "Criminal Law"
    PROPERTY_REAL_ESTATE = "Property & Real Estate Law"
    FAMILY_MATRIMONIAL = "Family & Matrimonial Law"
    EMPLOYMENT_LABOUR = "Employment & Labour Law"
    BANKING_FINANCIAL = "Banking & Financial Disputes"
    INTELLECTUAL_PROPERTY = "Intellectual Property Rights"
    ARBITRATION_ADR = "Arbitration & Alternative Dispute Resolution"
    GENERAL_ADVISORY = "General Chamber Advisory / Other"

class LeadStatus(str, enum.Enum):
    INTAKE = "INTAKE"
    PRE_LITIGATION_REVIEW = "PRE_LITIGATION_REVIEW"
    RETAINED = "RETAINED"
    IN_LITIGATION = "IN_LITIGATION"
    SETTLED = "SETTLED"
    CLOSED = "CLOSED"

class LeadPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

class ContentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"

class AssetType(str, enum.Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    DOCUMENT_PDF = "DOCUMENT_PDF"
    DOCUMENT_DOCX = "DOCUMENT_DOCX"

class AudienceSegment(str, enum.Enum):
    INDIVIDUAL = "INDIVIDUAL"
    BUSINESS = "BUSINESS"