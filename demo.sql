-- SQLite3 syntax

DROP TABLE IF EXISTS quotes;
CREATE TABLE quotes (quote VARCHAR(60), nsfw BOOLEAN);

INSERT INTO quotes (quote, nsfw) VALUES ('"Off with his head!", the Queen said.', 0);
INSERT INTO quotes (quote, nsfw) VALUES ('It''s the luck of the Irish!', 0);
INSERT INTO quotes (quote, nsfw) VALUES ('Expletive-deleted, expletive-deleted you expletive-deleted.', 1);
INSERT INTO quotes (quote, nsfw) VALUES ('This is a teeny, tiny bit longer than sixty bytes/characters.', 0);
INSERT INTO quotes (quote, nsfw) VALUES ('Ready?
Steady?
Go!', 0);
INSERT INTO quotes (quote, nsfw) VALUES (replace('Annother.\nNewline?\nDemo.','\n',char(10)),0);

COMMIT;

SELECT * FROM quotes;
