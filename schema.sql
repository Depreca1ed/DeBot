BEGIN;
CREATE TABLE IF NOT EXISTS Blacklists (id BIGINT NOT NULL, type TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS Prefixes (
    guild BIGINT NOT NULL,
    prefix TEXT NOT NULL,
    PRIMARY KEY(guild, prefix)
);
CREATE TABLE IF NOT EXISTS ErrorLogs (
    id BIGINT PRIMARY KEY,
    command TEXT NOT NULL,
    error TEXT NOT NULL,
    full_error TEXT NOT NULL,
    message TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS Features (id BIGINT NOT NULL, type TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS WaifuFavourites (
    waifu_url TEXT NOT NULL,
    user_id BIGINT NOT NULL,
    nsfw BOOLEAN NOT NULL,
    tm TIMESTAMP NOT NULL,
    PRIMARY KEY (user_id, waifu_url)
);

CREATE TYPE WaifuType AS ENUM ('pokemon', 'waifu');

CREATE TABLE Waifus(
    id INTEGER,
    smashes INTEGER NOT NULL DEFAULT 0,
    passes INTEGER NOT NULL DEFAULT 0,
    nsfw BOOLEAN NOT NUll,
    type WaifuType NOT NULL,
    PRIMARY KEY(id, type)
);
COMMIT;