-- upgrade --
ALTER TABLE "scanner" ADD "unknown" INT NOT NULL  DEFAULT 0;
-- downgrade --
ALTER TABLE "scanner" DROP COLUMN "unknown";
