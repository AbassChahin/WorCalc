import pymongo
import os
from datetime import datetime, timedelta, time

class DBHandler:
  def __init__(self):
    self.user = None
    self.connected = False
    self.collection = None
    self.dbName = os.environ.get("DBName")
    self.colName = os.environ.get("CollectionName")
    self.dbAccess = os.environ.get("DBAccess")
    self.connect()

  def connect(self):
    if self.connected == False:
      try:
        client = pymongo.MongoClient(self.dbAccess)
        db = client[self.dbName]
        self.collection = db[self.colName]
        self.connected = True
        print("[SUCCESS] Database Connection Passed")
      except Exception:
        print("[ERROR] Database Connection Failed!")
    else:
      print("Database Already Connected!")

  def get_user(self, username, password):
    results = self.collection.find_one({"Username": username, "Password": password})
    return results

  def set_user(self, username):
    self.user = username
    
  def get_information(self, accountHolder):
    if self.connected == True:
      # Needed Variables
      user = os.environ.get(accountHolder)
      accountHolder = accountHolder + "Pay"
      hourlyPay = int(os.environ.get(accountHolder))
      hoursWorked = 0
      batSold = 0
      tipsMade = 0
      currPay = 0

      # Get Dates
      today = datetime.now()
      lastSat = today.weekday() - 5
      nextFri = 4 - today.weekday()
      
      if lastSat <= 0:
        lastSat += 7
      if nextFri <= 0:
        nextFri += 7
        
      lastSat = today - timedelta(days=lastSat)
      nextFri = today + timedelta(days=nextFri)

      lastSat = datetime.combine(lastSat.date(), time())
      nextFri = datetime.combine(nextFri.date(), time())
      
      dateFormat = "%Y-%m-%d"
      print("Last Sat: ", lastSat.strftime(dateFormat))
      print("Next Fri: ", nextFri.strftime(dateFormat))

      results = self.collection.find(
        {"Date": {"$gte": lastSat, "$lt": nextFri}, "User": user})
      for doc in results:
        logoutTime = doc["LogOutTime"]
        tipsMade += doc["TipsMadeTotal"]
        batSold += doc["BatteriesSoldTotal"]
        hoursWorked += 14

        # Calculate extra minutes
        hour1, minute1 = map(int, "10:00".split(":"))
        hour2, minute2 = map(int, logoutTime.split(":"))

        time1Minutes = hour1 * 60 + minute1
        time2Minutes = hour2 * 60 + minute2

        timeDiff = time2Minutes - time1Minutes
        
        if timeDiff <= 0:
          hoursWorked += 0
        else:
          hoursWorked += timeDiff / 60

      hoursWorked = round(hoursWorked, 1)
      currPay = (hoursWorked * hourlyPay) + tipsMade + (batSold * 15)
      currPay = round(currPay, 2)

      content = {
        "HoursWorked": hoursWorked,
        "BatSold": batSold,
        "TipsMade": tipsMade,
        "CurrPay": currPay,
        "FromDate": lastSat.strftime("%m-%d-%Y"),
        "ToDate": nextFri.strftime("%m-%d-%Y"),
        "User": user
      }
      return content
    else:
      print("[ERROR] Database Not Connected!")

  def log_tips(self, tips):
    if self.connected == True:
      user = os.environ.get(self.user)
      today = datetime.now()
      today = datetime.combine(today.date(), time())

      results = self.check_current(today)
      if (results):
        tipsTotal = results["TipsMadeTotal"]
        tipsList = results["TipsMade"]

        tipsTotal += tips
        tipsList.append(tips)

        self.collection.update_one({"Date": today, "User": user}, {"$set": {
          "TipsMadeTotal": tipsTotal,
          "TipsMade": tipsList,
        }})
      else:
        doc = {
          "Date": today,
          "LogOutTime": "10:00",
          "TipsMadeTotal": tips,
          "BatteriesSoldTotal": 0,
          "TipsMade": [tips],
          "BatteriesSold": [],
          "User": os.environ.get(self.user)
        }
        self.collection.insert_one(doc)
    else:
      print("[ERROR] Database Not Connected!")
  
  def log_sale(self, type, cost, tips):
    if self.connected == True:
      user = os.environ.get(self.user)
      today = datetime.now()
      today = datetime.combine(today.date(), time())

      results = self.check_current(today)
      if (results):
        tipsTotal = results["TipsMadeTotal"]
        batsTotal = results["BatteriesSoldTotal"]
        tipsList = results["TipsMade"]
        batList = results["BatteriesSold"]

        tipsTotal += tips
        batsTotal += 1
        tipsList.append(tips)
        batList.append(type)

        self.collection.update_one({"Date": today, "User": user}, {"$set": {
          "TipsMadeTotal": tipsTotal,
          "BatteriesSoldTotal": batsTotal,
          "TipsMade": tipsList,
          "BatteriesSold": batList
        }})
      else:
        doc = {
          "Date": today,
          "LogOutTime": "10:00",
          "TipsMadeTotal": tips,
          "BatteriesSoldTotal": 1,
          "TipsMade": [tips],
          "BatteriesSold": [type],
          "User": os.environ.get(self.user)
        }
        self.collection.insert_one(doc)

    else:
      print("[ERROR] Database Not Connected!")

  def log_out(self, givenDate, time):
    if self.connected == True:
      user = os.environ.get(self.user)
      newDate = datetime.strptime(givenDate, "%Y-%m-%d")
      results = self.check_current(newDate)
      if (results):
        self.collection.update_one({"Date": newDate, "User": user}, {"$set": {
          "LogOutTime": time
        }})
      else:
        doc = {
          "Date": newDate,
          "LogOutTime": time,
          "TipsMadeTotal": 0,
          "BatteriesSoldTotal": 0,
          "TipsMade": [],
          "BatteriesSold": [],
          "User": os.environ.get(self.user)
        }
        self.collection.insert_one(doc)
        
    else:
      print("[ERROR] Database Not Connected!")

  def get_timesheets(self, fromdate, todate):
    if self.connected == True:
      user = os.environ.get(self.user)
      fromdate = datetime.strptime(fromdate, "%Y-%m-%d")
      todate = datetime.strptime(todate, "%Y-%m-%d")
      accountHolder = self.user + "Pay"
      hourlyPay = int(os.environ.get(accountHolder))
      hoursWorked = 0
      batSold = 0
      tipsMade = 0
      currPay = 0
      
      results = self.collection.find(
        {"Date": {"$gte": fromdate, "$lt": todate}, "User": user})
      resultsList = []
      for doc in results:
        resultsList.append(doc)
        logoutTime = doc["LogOutTime"]
        tipsMade += doc["TipsMadeTotal"]
        batSold += doc["BatteriesSoldTotal"]
        hoursWorked += 14

        # Calculate extra minutes
        hour1, minute1 = map(int, "10:00".split(":"))
        hour2, minute2 = map(int, logoutTime.split(":"))

        time1Minutes = hour1 * 60 + minute1
        time2Minutes = hour2 * 60 + minute2

        timeDiff = time2Minutes - time1Minutes

        if timeDiff <= 0:
          hoursWorked += 0
        else:
          hoursWorked += timeDiff / 60

      hoursWorked = round(hoursWorked, 1)
      currPay = (hoursWorked * hourlyPay) + tipsMade + (batSold * 15)
      currPay = round(currPay, 2)

      content = {
        "HoursWorked": hoursWorked,
        "BatSold": batSold,
        "TipsMade": tipsMade,
        "CurrPay": currPay,
        "FromDate": fromdate.strftime("%m-%d-%Y"),
        "ToDate": todate.strftime("%m-%d-%Y"),
        "Results": resultsList,
        "User": user
      }
      return content

    else:
      print("[ERROR] Database Not Connected!")

  def check_current(self, date):
    if self.connected == True:
      results = self.collection.find_one({"Date": date, "User": os.environ.get(self.user)})
      return results        
    else:
      print("[ERROR] Database Not Connected!")