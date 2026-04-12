"""
Data models for Postulae CV Generator.
Clean, simple Pydantic models for type safety and validation.
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class ContactInformation(BaseModel):
    """Contact details for CV header."""
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None


class EducationEntry(BaseModel):
    """Education section entry."""
    year: Optional[str] = None  # Renamed to "date" during normalization
    date: Optional[str] = None
    institution: str
    location: str
    degree: str
    major: Optional[str] = None
    honors: Optional[str] = None
    coursework: List[str] = Field(default_factory=list)


class WorkExperienceEntry(BaseModel):
    """Work experience section entry."""
    date: str  # Format: "Mon YYYY-Mon YYYY" or "Since Mon YYYY"
    company: str
    location: str  # Format: "City, Country"
    position: str
    duration: Optional[str] = None
    bullets: List[str] = Field(default_factory=list)


class CVContent(BaseModel):
    """Complete CV content structure."""
    contact_information: List[ContactInformation] = Field(default_factory=list)
    education: List[EducationEntry] = Field(default_factory=list)
    work_experience: List[WorkExperienceEntry] = Field(default_factory=list)
    experience: List[WorkExperienceEntry] = Field(default_factory=list)  # Alias
    language_skills: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)  # Alias
    it_skills: List[str] = Field(default_factory=list)
    financial_databases: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)  # Alias
    activities_interests: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)  # Alias

    # Metadata
    domain: str = "finance"  # finance, consulting, startup, government
    summary: Optional[str] = None
    certifications: List[str] = Field(default_factory=list)


class CVGenerationResult(BaseModel):
    """Result of CV generation with PDF and DOCX bytes."""
    pdf_bytes: bytes
    docx_bytes: bytes
    page_count: int
    fill_percentage: float
    char_count: int
    warnings: List[str] = Field(default_factory=list)
    warning_info: Optional[Dict] = None  # Adaptive enrichment warning (level, title, message)


class PageFillMetrics(BaseModel):
    """Page fill rate metrics for density optimization."""
    page_count: int
    fill_percentage: float
    char_count: int
    text_height: Optional[float] = None
    page_height: Optional[float] = None
