-- upgrade --
ALTER TABLE "deviceheartbeat" ADD "learning_session_id" INT;
ALTER TABLE "devicesignal" ADD "learning_session_id" INT;
CREATE TABLE IF NOT EXISTS "learningsession" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    "device_id" INT NOT NULL REFERENCES "device" ("id") ON DELETE CASCADE,
    "room_id" INT NOT NULL REFERENCES "room" ("id") ON DELETE CASCADE
);-- downgrade --
ALTER TABLE "deviceheartbeat" DROP COLUMN "learning_session_id";
ALTER TABLE "devicesignal" DROP COLUMN "learning_session_id";
DROP TABLE IF EXISTS "learningsession";
