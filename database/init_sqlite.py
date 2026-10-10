import sqlite3
from pathlib import Path


def get_default_db_path():
    return str(Path(__file__).resolve().parent / "fdc_rag_demo.db")


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Sites (
    EntityId INTEGER PRIMARY KEY,
    SiteCode TEXT NOT NULL,
    SiteName TEXT NOT NULL,
    Location TEXT,
    IsActive INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Users (
    EntityId INTEGER PRIMARY KEY,
    UserName TEXT NOT NULL,
    Email TEXT NOT NULL,
    SiteId INTEGER NOT NULL,
    IsActive INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (SiteId) REFERENCES Sites(EntityId)
);

CREATE TABLE IF NOT EXISTS Deviations (
    EntityId INTEGER PRIMARY KEY,
    DeviationNumber TEXT NOT NULL,
    Title TEXT NOT NULL,
    Description TEXT,
    Status TEXT NOT NULL,
    Severity TEXT,
    CreatedOn TEXT NOT NULL,
    SiteId INTEGER NOT NULL,
    AssignedTo INTEGER,
    FOREIGN KEY (SiteId) REFERENCES Sites(EntityId),
    FOREIGN KEY (AssignedTo) REFERENCES Users(EntityId)
);

CREATE TABLE IF NOT EXISTS CAPA (
    EntityId INTEGER PRIMARY KEY,
    CAPANumber TEXT NOT NULL,
    Title TEXT NOT NULL,
    Status TEXT NOT NULL,
    DeviationId INTEGER,
    CreatedOn TEXT NOT NULL,
    DueDate TEXT,
    OwnerId INTEGER,
    FOREIGN KEY (DeviationId) REFERENCES Deviations(EntityId),
    FOREIGN KEY (OwnerId) REFERENCES Users(EntityId)
);

CREATE TABLE IF NOT EXISTS Actions (
    EntityId INTEGER PRIMARY KEY,
    ActionNumber TEXT NOT NULL,
    Description TEXT NOT NULL,
    Status TEXT NOT NULL,
    CAPAId INTEGER NOT NULL,
    AssignedTo INTEGER,
    DueDate TEXT,
    FOREIGN KEY (CAPAId) REFERENCES CAPA(EntityId),
    FOREIGN KEY (AssignedTo) REFERENCES Users(EntityId)
);

CREATE TABLE IF NOT EXISTS Documents (
    EntityId INTEGER PRIMARY KEY,
    DocumentNumber TEXT NOT NULL,
    Title TEXT NOT NULL,
    DocumentType TEXT NOT NULL,
    Status TEXT NOT NULL,
    SiteId INTEGER NOT NULL,
    CreatedOn TEXT NOT NULL,
    FOREIGN KEY (SiteId) REFERENCES Sites(EntityId)
);
"""


SITE_ROWS = [
    (1, "HYD-001", "Hyderabad Manufacturing Plant", "Hyderabad, Telangana", 1),
    (2, "BLR-002", "Bangalore API Plant", "Bangalore, Karnataka", 1),
    (3, "VIZ-003", "Vizag Quality Control Lab", "Visakhapatnam, Andhra Pradesh", 1),
]

USER_ROWS = [
    (1, "Aisha Rao", "aisha.rao@pharma.local", 1, 1),
    (2, "Vikram Singh", "vikram.singh@pharma.local", 2, 1),
    (3, "Neha Patel", "neha.patel@pharma.local", 1, 1),
    (4, "Rohit Kumar", "rohit.kumar@pharma.local", 3, 1),
    (5, "Meera Nair", "meera.nair@pharma.local", 2, 1),
]

DEVIATION_ROWS = [
    (1, "DEV-1001", "Temperature excursion in granulation", "Granulation temperature exceeded the validated range during a batch run.", "Open", "Major", "2025-01-12T09:30:00", 1, 1),
    (2, "DEV-1002", "Label mix-up in packaging line", "Packaging line printed an incorrect batch label during secondary packaging.", "Closed", "Critical", "2024-12-05T14:10:00", 2, 2),
    (3, "DEV-1003", "Air handling filter alarm", "The AHU filter alarm triggered during cleanroom changeover and was not released on time.", "Open", "Moderate", "2025-02-14T11:00:00", 1, 3),
    (4, "DEV-1004", "Raw material weighing variance", "Balance printout showed abnormal variance in raw material weighing for one batch.", "Open", "Major", "2025-03-03T08:45:00", 2, 5),
]

CAPA_ROWS = [
    (1, "CAPA-2001", "Investigate temperature excursion", "Open", 1, "2025-01-13T10:00:00", "2025-02-20", 1),
    (2, "CAPA-2002", "Correct packaging label control", "Closed", 2, "2024-12-08T09:15:00", "2025-01-25", 2),
    (3, "CAPA-2003", "Review AHU filter monitoring", "Open", 3, "2025-02-16T13:00:00", "2025-03-30", 3),
    (4, "CAPA-2004", "Validate weighing process controls", "Open", 4, "2025-03-04T09:00:00", "2025-04-15", 5),
]

ACTION_ROWS = [
    (1, "ACT-3001", "Review batch records and compare temperature logs.", "Open", 1, 3, "2025-01-20"),
    (2, "ACT-3002", "Verify packaging line label configuration and operator training records.", "Closed", 2, 2, "2025-01-10"),
    (3, "ACT-3003", "Inspect AHU alarm trend and perform filter replacement check.", "In Progress", 3, 4, "2025-03-15"),
    (4, "ACT-3004", "Recalibrate weighing balance and assess operator adherence.", "Open", 4, 5, "2025-04-01"),
    (5, "ACT-3005", "SOP review for deviation escalation process.", "Closed", 1, 1, "2025-01-18"),
]

DOCUMENT_ROWS = [
    (1, "DOC-4001", "Temperature Excursion SOP", "SOP", "Approved", 1, "2025-01-05T08:00:00"),
    (2, "DOC-4002", "Packaging Label Verification Checklist", "Checklist", "Issued", 2, "2024-12-10T10:00:00"),
    (3, "DOC-4003", "AHU Monitoring Log", "Log", "Active", 1, "2025-02-10T12:00:00"),
    (4, "DOC-4004", "Weighing Balance Calibration Record", "Record", "Approved", 2, "2025-03-05T11:00:00"),
]


def ensure_sqlite_database(db_path=None):
    if db_path is None:
        db_path = get_default_db_path()

    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_file)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA_SQL)

    connection.executemany(
        "INSERT OR IGNORE INTO Sites(EntityId, SiteCode, SiteName, Location, IsActive) VALUES (?, ?, ?, ?, ?)",
        SITE_ROWS,
    )
    connection.executemany(
        "INSERT OR IGNORE INTO Users(EntityId, UserName, Email, SiteId, IsActive) VALUES (?, ?, ?, ?, ?)",
        USER_ROWS,
    )
    connection.executemany(
        "INSERT OR IGNORE INTO Deviations(EntityId, DeviationNumber, Title, Description, Status, Severity, CreatedOn, SiteId, AssignedTo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        DEVIATION_ROWS,
    )
    connection.executemany(
        "INSERT OR IGNORE INTO CAPA(EntityId, CAPANumber, Title, Status, DeviationId, CreatedOn, DueDate, OwnerId) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        CAPA_ROWS,
    )
    connection.executemany(
        "INSERT OR IGNORE INTO Actions(EntityId, ActionNumber, Description, Status, CAPAId, AssignedTo, DueDate) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ACTION_ROWS,
    )
    connection.executemany(
        "INSERT OR IGNORE INTO Documents(EntityId, DocumentNumber, Title, DocumentType, Status, SiteId, CreatedOn) VALUES (?, ?, ?, ?, ?, ?, ?)",
        DOCUMENT_ROWS,
    )

    connection.commit()
    connection.close()

    return str(db_file)
