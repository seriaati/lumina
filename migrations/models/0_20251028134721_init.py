from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "luminauser" (
    "id" BIGINT NOT NULL PRIMARY KEY,
    "timezone" SMALLINT NOT NULL DEFAULT 0,
    "lang" VARCHAR(5)
);
CREATE TABLE IF NOT EXISTS "birthday" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "bday_user_id" BIGINT NOT NULL,
    "bday_username" VARCHAR(100),
    "month" INT NOT NULL,
    "day" INT NOT NULL,
    "leap_year_notify_month" INT,
    "leap_year_notify_day" INT,
    "last_notify_year" INT NOT NULL DEFAULT 0,
    "user_id" BIGINT NOT NULL REFERENCES "luminauser" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_birthday_bday_us_1b4a02" UNIQUE ("bday_user_id", "user_id", "bday_username")
);
CREATE TABLE IF NOT EXISTS "notes" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "title" VARCHAR(100) NOT NULL,
    "content" TEXT NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" BIGINT NOT NULL REFERENCES "luminauser" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "reminder" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "text" TEXT NOT NULL,
    "datetime" TIMESTAMP NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "message_url" TEXT,
    "sent" INT NOT NULL DEFAULT 0,
    "user_id" BIGINT NOT NULL REFERENCES "luminauser" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "todotask" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "text" TEXT NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "done" INT NOT NULL DEFAULT 0,
    "user_id" BIGINT NOT NULL REFERENCES "luminauser" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "eJztmltz2jgUx78Kw1M6k+1QE0J23yAhLVsuO4HsdprJeAQW4IksUUnehO3ku68k343s4l"
    "xx4ifw0Tmyzs+y9T+yf9YdYkHEPnZtylcW2NT/qP2sY+BA8Wer7bBWB+t11CINHMyQcp7F"
    "vWaMUzDnwr4AiEFhsiCbU3vNbYKFFbsISSOZC0cbLyOTi+0fLjQ5WUK+glQ0XF3VZ6Jf02"
    "WQmrYl+5d/5W9oVyO+vhYmG1vwDjIZJw/XN+bChshK5OV1ouwm36yVrWsv+5ifK185spk5"
    "J8h1cOS/3vAVwWGAjbm0LiGGFHAoz8CpK1OVmfhUguy9rCIXb5SxGAsugIt4DM2OvOYES9"
    "ZiNEzluJRn+e13w2g220ajeXzSOmq3WyeNE+GrhrTd1L73Eo6AeF0pLP3P/dFUJkrEBfWu"
    "tDTcqxjAgReleEeA09drd9TpyF9DDxDnUQ8MEfZoWpaPu4azMmyBPl0B+gvMQWCKs0htB8"
    "7+3H1JzA64MxHES74Sh58ajRyEf3cuTr90Lg6E14ckyJHfZHhtSaYOwaLzLZaZMzb0L9lU"
    "NT4dtY9OmsdH4QwNLXkTc3sS+s/8HXH53u8VFoJgbW4goCYm3F5szKLTLbuDByF9hVv4uY"
    "kWm49Z4e+VJmA8ICGpFCGpCX2527yxPwwfJHwqzZOjeaSSX9xopWZQCiRJnxMK7SX+CjeK"
    "dl+MG+C5Tun4Nc7AdWwMLv3O9o/1fTBfAmv0tKHgNqxx4tNIJClSg9yTgp3JaeesV1coZ2"
    "B+cwuoZSaYyhZikJQl9N1ucgwnbQEYLFX+Mgs55m28mgIzCT+7xETKL7jiT1tkvnbtuMs0"
    "ex/FI7cd+B/Bmnpm4gCEMknH48q07jSN9nEIWB7kIZ0MO4OBbtkW59nilV3/Bf6lLPtaOx"
    "R9rcySr/VBt6BkPxZj1ba/w8U0TwA/9PzrBURApZe51MS308qz0CSmm1B58JEURkEXJUVA"
    "oSNHQB+J4cLvpsQkOLHIIylMRRdTwG5KRuE5FZN3f2jEUnjjZOuk8PbcH4n0hvbWH1kn5g"
    "kfjgrt4oYBD1rGX6NifP7tW3FGDr3pk8Q4hXcZUzAWUhaQOdymvW9KcjuM/UBxXAfDzjdF"
    "0tn4LYPx6HPgHsN7Ohh301QplPmbQAP2TLRI7Z0BNxGZ4mv5oR+DP/tJWyz2wBpjtImWv0"
    "z6/WFvMu0M/0pcgrPOtCdbjAT+wHpwnJrgYSe1f/rTLzV5WPs+HvUUQcL4kqozRn7T73U5"
    "JuByYmJyawIr9vgLrAGYaq+q2qt6Fb10WI69qlCSa8RXXK5n6y8a96okWJkkmBAJRaRD4F"
    "/pBr1uiK/rRVRDPK6cmqEkGiFIO1ckVOrvjao/BzImFkHTpajIUy8VVpJN5Jd+9jFtGdol"
    "BEGA9WCZvgydiZjnujeKipLdoXbH40ECarefpnY57PZEha8ICyebJ14RVVVKVaVUVUpGlR"
    "JumWuqlPh2enaVIvfteeBVVSlPfxtXVUpJVupK375RfWtpPyPJlWCW/guSSoJVEqySYJUE"
    "i0uwDqT2fKUTYH5LrvwCkU8lvkokvv6FlPkfs+z6nj4WUhYJlnxTb7R2+eZOeGW+qVdtyR"
    "VF3hoFIPru5QT4sp86/DkZj4p+6nCJRYJXlj3nhzVkM369n1hzKMqs80uDdBWQEpyyg26x"
    "j0Offnm5/x9JS62m"
)
