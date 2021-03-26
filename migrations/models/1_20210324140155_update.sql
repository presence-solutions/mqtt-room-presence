-- upgrade --
CREATE TABLE "room_scanner" ("room_id" INT NOT NULL REFERENCES "room" ("id") ON DELETE CASCADE,"scanner_id" INT NOT NULL REFERENCES "scanner" ("id") ON DELETE CASCADE);
-- downgrade --
DROP TABLE IF EXISTS "room_scanner";
