CREATE TABLE AcquireSettings
(
   Id INT NOT NULL AUTO_INCREMENT,
   CroppingString TEXT,
   SkippingMode VARCHAR(255) NOT NULL DEFAULT 'Off',
   NumberOfRepetitions INT,
   SampleContainer VARCHAR(255),
   AcquireDuration BIGINT,
   AcquireMode VARCHAR(255),
   TimeBetweenRepetitionStarts BIGINT,
   UseExtraTimeBetweenRepetition BOOLEAN,
   TimeBetweenRepetitionStartsNextStart BIGINT,
   TimeBetweenRepetitionStartsNextValue BIGINT,
   IsCrystalJob BOOLEAN,
   OriginalAcquireTask_id INT,
   PRIMARY KEY (Id)
);

CREATE TABLE AcquireTask
(
   JobTask_id INT NOT NULL,
   CameraAngle FLOAT,
   CameraSensorHeight INT,
   CameraSensorWidth INT,
   LensMagnificationFactor FLOAT,
   PixelSize FLOAT,
   NumberOfCompleteRepetitions INT,
   UsedDuration BIGINT,
   UsedRepetitions INT,
   FirstAvailableRepetition INT DEFAULT 0,
   AcquireSettings_id INT,
   InstrumentInfo_id INT,
   PRIMARY KEY (JobTask_id) 
);


CREATE TABLE Job
(
   Id INT NOT NULL AUTO_INCREMENT,
   Name VARCHAR(255),
   Status VARCHAR(255),
   ModifiedTimeUtc DATETIME,
   FilePath VARCHAR(255),
   IsPreview BOOLEAN,
   ContinuationOrderIndex INT,
   OriginalJob_id INT,
   PRIMARY KEY (Id)
);


CREATE TABLE JobEvent
(
   Id INT NOT NULL AUTO_INCREMENT,
   Description TEXT,
   Category VARCHAR(255),
   Level VARCHAR(255),
   TimestampUtc DATETIME,
   Job_id INT,
   PRIMARY KEY (Id)
);


CREATE TABLE JobTask
(
   Id INT NOT NULL AUTO_INCREMENT,
   IsOwnedTask BOOLEAN DEFAULT 0,
   ShowInComplete BOOLEAN DEFAULT 1,
   ShowInRunning BOOLEAN DEFAULT 1,
   OrderIndex INT,
   AppVersion VARCHAR(255),
   FileLayoutVersion INT,
   PathInDataStore VARCHAR(255),
   StartTimeUtc DATETIME,
   FinishTimeUtc DATETIME,
   Job_id INT,
   PRIMARY KEY (Id)
);


CREATE TABLE Scan
(
   Id INT NOT NULL AUTO_INCREMENT,
   RepetitionIndex INT,
   OptimalZLevel INT,
   TemperatureMeasuredTimeUtc DATETIME,
   BoardTemperature INT,
   PT1000Sensor0Temperature INT,
   PT1000Sensor1Temperature INT,
   PT1000Sensor2Temperature INT,
   PT1000Sensor3Temperature INT,
   ScanArea_id INT,
   PRIMARY KEY (Id)
);


CREATE TABLE ScanArea
(
   Id INT NOT NULL AUTO_INCREMENT,
   AutoAdjustIlluminationLevel BOOLEAN NOT NULL DEFAULT 1,
   FocusOffset FLOAT DEFAULT 0,
   OrderIndex INT,
   Name VARCHAR(255),
   NameIsUserDefined BOOLEAN,
   IlluminationLevel INT,
   Enabled BOOLEAN,
   Highlighted BOOLEAN,
   Deleted BOOLEAN,
   IlluminationTime INT,
   TrayPosition FLOAT,
   CameraStartPosition FLOAT,
   CameraStepSize FLOAT,
   NumberOfImages INT,
   FocusPosition FLOAT,
   Comment VARCHAR(255),
   AcquireSettings_id INT,
   PRIMARY KEY (Id)
);


CREATE INDEX IX_OriginalAcquireTask ON AcquireSettings (OriginalAcquireTask_id ASC);

CREATE INDEX IX_AcquireSettings ON AcquireTask (AcquireSettings_id ASC);

CREATE INDEX IX_OriginalJob ON Job (OriginalJob_id ASC);

CREATE INDEX IX_JobEvent_Job ON JobEvent (Job_id ASC);

CREATE INDEX IX_JobTask_Job ON JobTask (Job_id ASC);

CREATE INDEX IX_RepetitionIndex ON Scan (RepetitionIndex ASC);

CREATE INDEX IX_ScanArea ON Scan (ScanArea_id ASC);

CREATE INDEX IX_AcquireSettings ON ScanArea (AcquireSettings_id ASC);

CREATE INDEX idx_JobTask_id ON AcquireTask (JobTask_id);

 
ALTER TABLE AcquireSettings
ADD FOREIGN KEY (OriginalAcquireTask_id)
REFERENCES AcquireTask (JobTask_id) ON DELETE NO ACTION ON UPDATE NO ACTION;

ALTER TABLE AcquireTask
ADD FOREIGN KEY (JobTask_id)
REFERENCES JobTask (Id) ON DELETE NO ACTION ON UPDATE NO ACTION;

ALTER TABLE AcquireTask
ADD FOREIGN KEY (AcquireSettings_id)
REFERENCES AcquireSettings (Id) ON DELETE NO ACTION ON UPDATE NO ACTION;

ALTER TABLE Job 
ADD FOREIGN KEY (OriginalJob_id)
REFERENCES Job (Id) ON DELETE NO ACTION ON UPDATE NO ACTION;

ALTER TABLE JobEvent 
ADD FOREIGN KEY (Job_id)
REFERENCES Job (Id) ON DELETE NO ACTION ON UPDATE NO ACTION;

ALTER TABLE JobTask 
ADD FOREIGN KEY (Job_id)
REFERENCES Job (Id) ON DELETE NO ACTION ON UPDATE NO ACTION;

ALTER TABLE Scan 
ADD CONSTRAINT FOREIGN KEY (ScanArea_id)
REFERENCES ScanArea (Id) ON DELETE NO ACTION ON UPDATE NO ACTION;

ALTER TABLE ScanArea 
ADD CONSTRAINT FOREIGN KEY (AcquireSettings_id)
REFERENCES AcquireSettings (Id) ON DELETE NO ACTION ON UPDATE NO ACTION;




