from django.shortcuts import render, redirect
from . import dbHandler as DBH

db = DBH.DBHandler()

async def index(request):
  if db.user == None:
    return redirect('signin')
  elif request.method == 'POST':
    submitText = request.POST.get("submitbutton")
    if submitText == "Log Battery Sale":
      batType = request.POST.get("battype")
      batCost = request.POST.get("batcost")
      tipMade = float(request.POST.get("tipmade"))
      db.log_sale(batType, batCost, tipMade)
      content = db.get_information(db.user)
      return render(request, 'index.html', content)
    elif submitText == "Log Tips":
      tipsMade = float(request.POST.get("tiponly"))
      db.log_tips(tipsMade)
      content = db.get_information(db.user)
      return render(request, 'index.html', content)
    elif submitText == "Log Out Time":
      logoutDate = request.POST.get("date")
      logoutTime = request.POST.get("time")
      print(logoutDate)
      print(logoutTime)
      db.log_out(logoutDate, logoutTime)
      content = db.get_information(db.user)
      return render(request, 'index.html', content)
    else:
      content = db.get_information(db.user)
      return render(request, 'index.html', content)
  else: 
    content = db.get_information(db.user)
    return render(request, 'index.html', content)
def timesheets(request):
  if db.user == None:
    return redirect('signin')
  elif request.method == 'POST':
    submitText = request.POST.get("submitbutton")
    print(submitText)
    if submitText == "Get Timesheet":
      fromDate = request.POST.get("fromdate")
      toDate = request.POST.get("todate")
      content = db.get_timesheets(fromDate, toDate)
      return render(request, 'timesheets2.html', content)
  else:
    return render(request, 'timesheets.html')

def signin(request):
  if request.method == "POST":
    username = request.POST.get("username")
    password = request.POST.get("password")

    if(db.get_user(username, password)):
      db.set_user(username)
      return redirect('index')
    else:
      return render(request, 'signin.html')
  return render(request, 'signin.html')