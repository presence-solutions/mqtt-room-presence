-- upgrade --
CREATE TABLE IF NOT EXISTS "predictionmodel" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    "display_name" VARCHAR(100) NOT NULL  DEFAULT '',
    "inputs_hash" VARCHAR(100) NOT NULL,
    "accuracy" REAL NOT NULL  DEFAULT 0,
    "model" BLOB
);
CREATE TABLE IF NOT EXISTS "room" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(100) NOT NULL,
    CONSTRAINT "room_name_unique" UNIQUE ("name")
);
CREATE TABLE IF NOT EXISTS "device" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(100) NOT NULL,
    "uuid" VARCHAR(100) NOT NULL,
    "use_name_as_id" INT NOT NULL  DEFAULT 0,
    "display_name" VARCHAR(100) NOT NULL  DEFAULT '',
    "latest_signal" TIMESTAMP,
    "prediction_model_id" INT REFERENCES "predictionmodel" ("id") ON DELETE CASCADE,
    "current_room_id" INT REFERENCES "room" ("id") ON DELETE CASCADE,
    CONSTRAINT "device_uuid_unique" UNIQUE ("uuid")

);
CREATE TABLE IF NOT EXISTS "deviceheartbeat" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    "signals" TEXT NOT NULL,
    "room_id" INT NOT NULL REFERENCES "room" ("id") ON DELETE CASCADE,
    "device_id" INT NOT NULL REFERENCES "device" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "scanner" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(100) NOT NULL,
    "uuid" VARCHAR(100) NOT NULL  DEFAULT '',
    "display_name" VARCHAR(100) NOT NULL  DEFAULT '',
    "latest_signal" TIMESTAMP,
    CONSTRAINT "scanner_uuid_unique" UNIQUE ("uuid")
);
CREATE TABLE IF NOT EXISTS "devicesignal" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    "rssi" REAL NOT NULL  DEFAULT 0,
    "room_id" INT NOT NULL REFERENCES "room" ("id") ON DELETE CASCADE,
    "device_id" INT NOT NULL REFERENCES "device" ("id") ON DELETE CASCADE,
    "scanner_id" INT NOT NULL REFERENCES "scanner" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(20) NOT NULL,
    "content" TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS "model_device" (
    "predictionmodel_id" INT NOT NULL REFERENCES "predictionmodel" ("id") ON DELETE CASCADE,
    "device_id" INT NOT NULL REFERENCES "device" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "room_scanner" (
    "room_id" INT NOT NULL REFERENCES "room" ("id") ON DELETE CASCADE,
    "scanner_id" INT NOT NULL REFERENCES "scanner" ("id") ON DELETE CASCADE
);
