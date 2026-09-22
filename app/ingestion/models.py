from dataclasses import dataclass, field


@dataclass
class SourceLocation:
    page: int | None = None
    bbox: dict[str, float] | None = None
    line_start: int | None = None
    line_end: int | None = None
    row_start: int | None = None
    row_end: int | None = None
    column_start: int | None = None
    column_end: int | None = None


@dataclass
class DocumentElement:
    element_id: str
    text: str
    element_type: str
    source_file: str
    order: int
    location: SourceLocation = field(
        default_factory=SourceLocation
    )
    parent_id: str | None = None
    metadata: dict = field(default_factory=dict)

@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str
    text: str
    source_file: str
    locations: list[SourceLocation] = field(
        default_factory=list
    )
    element_types: list[str] = field(
        default_factory=list
    )
    metadata: dict = field(
        default_factory=dict
    )
    
@dataclass
class CanonicalDocument:
    document_id: str
    source_file: str
    file_type: str
    elements: list[DocumentElement] = field(
        default_factory=list
    )