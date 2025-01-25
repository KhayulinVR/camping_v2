import datetime

date = "2023.05.26"
#       0123456789

new_date = datetime.date(int(date[:4]), int(date[5:7]), int(date[8:]))
print(type(new_date))
print(new_date)