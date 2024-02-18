import datetime

start_date = input("Start date (YYYY-MM-DD): ")
date = datetime.date.fromisoformat(start_date)

moderator = None
textfile = open("events.txt", "w", encoding="utf-8")

while True:
    if date.weekday() == 2:
        moderator = None
    if date.weekday() in [2, 3, 4, 5]:
        if moderator is None:
            moderator = input("Moderation am {}: ".format(date.strftime("%d.%m.%y")))
            if moderator == "":
                break
        textfile.write(date.isoformat() + " " + moderator + "\n")
    date += datetime.timedelta(days=1)
textfile.close()