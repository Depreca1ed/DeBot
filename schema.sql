BEGIN;

DO $$ BEGIN
        CREATE TYPE WaifuType AS ENUM('pokemon', 'waifu');
        CREATE TYPE BlacklistTypes AS ENUM('guild', 'user');
EXCEPTION
        WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS Blacklists (
    snowflake BIGINT NOT NULL PRIMARY KEY,
    reason TEXT NOT NULL,
    lasts_until TIMESTAMP,
    blacklist_type BlacklistTypes NOT NULL
);

CREATE TABLE IF NOT EXISTS Prefixes (
    guild BIGINT NOT NULL,
    prefix TEXT NOT NULL,
    PRIMARY KEY (guild, prefix)
);

CREATE TABLE IF NOT EXISTS WaifuFavourites (
    waifu_url TEXT NOT NULL,
    user_id BIGINT NOT NULL,
    nsfw BOOLEAN NOT NULL,
    tm TIMESTAMP NOT NULL,
    PRIMARY KEY (user_id, waifu_url)
);

CREATE TABLE IF NOT EXISTS Waifus (
    id INTEGER NOT NULL,
    smashes INTEGER NOT NULL DEFAULT 0,
    passes INTEGER NOT NULL DEFAULT 0,
    nsfw BOOLEAN NOT NUll,
    type WaifuType NOT NULL,
    PRIMARY KEY (id, type)
);

COMMIT;
