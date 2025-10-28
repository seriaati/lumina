from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "birthday" ADD "last_early_notify_year" INT NOT NULL DEFAULT 0;
        ALTER TABLE "birthday" ADD "notify_days_before" INT;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "birthday" DROP COLUMN "last_early_notify_year";
        ALTER TABLE "birthday" DROP COLUMN "notify_days_before";"""


MODELS_STATE = (
    "eJztmltz2jgUx78Kw1M6k+1QCCG7b5CQli2XnUB2O81kPAIL8ESWqCRvwnby3VeS70Z2cc"
    "gFBz8lHJ0jSz8fWf8j+2fVJiZE7GPHonxpgnX1j8rPKgY2FP9stB1XqmC1ClukgYMpUs7T"
    "qNeUcQpmXNjnADEoTCZkM2qtuEWwsGIHIWkkM+Fo4UVocrD1w4EGJwvIl5CKhpub6lT0az"
    "gMUsMyZf/yX/k3sKsR394Kk4VN+ACZjJM/V3fG3ILIjM3L7UTZDb5eKVvHWvQwv1S+cmRT"
    "Y0aQY+PQf7XmS4KDAAtzaV1ADCngUF6BU0dOVc7Eo+LP3p1V6OKOMhJjwjlwEI+g2ZLXjG"
    "DJWoyGqTku5FV++71ebzRa9Vrj9Kx50mo1z2pnwlcNabOp9ehOOATidqWw9D73hhM5USJu"
    "qHunpeFRxQAO3CjFOwScvF/bo05G/hq6jziLum8IsYdpWTzuGs7KsAH6fAnoLzD7gQnOYm"
    "pbcPZy9zUx2+DBQBAv+FL8/FSrZSD8u311/qV9dSS8PsRBDr2mutsWZ2oTLDrfYJmasYF/"
    "wVK1/umkdXLWOD0JMjSwZCXmZhJ6z/wtcXnehwoLQbAy1hBQAxNuzddG3nRL7+BJSN9gCb"
    "800Xz5mBZ+qDQB4z4JSSUPSU3o6y3z2v4wDBOJGVM4J1SzNadS1AcfcjaKVELrXXJS28FB"
    "ZuaTJHmpxjPUuKwx53faIsgvUuOkL8WKthb4K1wr2j0xboBnukXuVd99x7YwuPY62z/Wj3"
    "6++NbwyUPBfVB9R9NITFJMDXK3SGmPz9sX3apCOQWzu3tATSPGVLaQOklYAt/NJrtuJy0A"
    "g4Wav5yFHPMmXs3RRxx++uEHUn7+HX/e44+3PtXYJs0O41iDWzb8j2DNdj62AUKppKNxRd"
    "p3GvXWaQBY/shCOh60+33dFi6us8Er/WTC9y/kgURzi+OIZuphRPODbkNJfyxGzoG8s1em"
    "eQJ4oZdfryACanqpW030oLc4G01Se8MdKQz9LgqKgEJbjoDuiOHK66bAJDgxyY4UJqKLCW"
    "B3BaPwkorJXR8asRQsnHSdFCzP/ZFI7+itz451Ypbw4SjX+4Ug4Enb+FtUjC//YkFckUM3"
    "feIYJ/AhJQUjIUUBmcFt0v2mJLfN2A8UxXU0aH9TJO2119IfDT/77hG85/1RJ0mVQjl/A2"
    "jAXogWqb1T4MYiE3xNL/Sj/89+0habPTBHGK3D7S+Vfm/QHU/ag79it+CiPenKlnoMv289"
    "Ok0keNBJ5Z/e5EtF/qx8Hw27iiBhfEHVFUO/yfeqHBNwODEwuTeAGXn8+VYfTHlWVZ5VvY"
    "leOi7GWVUgyTXiKyrX0/UXjXqVEqxIEkyIhDzSwfcvdYNeN0T39TyqIRpXTM1QEI3gTztT"
    "JJTq752qPxsyJjZBw6Eoz1MvEVaQQ+TXfvYxbRnaIQRBgPVgmb4MnYqYl1obeUXJ9lA7o1"
    "E/BrXTS1K7HnS6osJXhIWTxWOviMoqpaxSyiolpUoJjsw1VUr0OD29SpHn9tz3KquU51/G"
    "ZZVSkJ261LfvVN+a2s9IMiWYqf+CpJRgpQQrJVgpwaISrA2pNVvqBJjXkim/QOhTiq8Cia"
    "9/IWXexyzbvqePhBRFgsXf1Neb23xzJ7xS39SrtviOIpdGDoieezEBvu6nDn+OR8O8nzpc"
    "YzHBG9Oa8eMKshi/3U+sGRTlrLNLg2QVkBCcsoNOvo9Dn397efwfiX6D2Q=="
)
