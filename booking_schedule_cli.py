import os
import json
import time
import urllib.request
import urllib.error

from savills import Savills


import sys
import datetime


def send_gotify_message(message, title="Savills Booking", priority=5):
    """Send a text message to the Gotify server.

    Configuration is read from environment variables:
        GOTIFY_URL    - base URL of the Gotify server (e.g. http://gotify.local:80)
        GOTIFY_TOKEN  - application token used to authenticate the message

    Returns the parsed JSON response from Gotify, or None if the server/token
    are not configured or the request fails.
    """
    gotify_url = os.environ.get("GOTIFY_URL", "").rstrip("/")
    gotify_token = os.environ.get("GOTIFY_TOKEN", "").strip()

    if not gotify_url or not gotify_token:
        print("[gotify] skipped: GOTIFY_URL or GOTIFY_TOKEN not set")
        return None

    endpoint = f"{gotify_url}/message?token={gotify_token}"
    payload = json.dumps({
        "message": message,
        "title": title,
        "priority": priority,
    }).encode("utf-8")

    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            print(f"[gotify] sent ({resp.status}): {body}")
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                return None
    except urllib.error.URLError as exc:
        print(f"[gotify] failed: {exc}")
        return None


def thread_worker(instance, a):
    return instance.create_booking(a)
def test_multiple_booking_parallel(hour=13,dayinweek=3,month=10,year=2024):
    from concurrent.futures import ThreadPoolExecutor
    from gettime import get_day_times
    
    lst = get_day_times(dayinweek=dayinweek,month=month,year=year,hour=hour)
    print(lst)
    #return
    with ThreadPoolExecutor(max_workers=len(lst)) as executor:
        futures = [executor.submit(thread_worker, savills, arg) for arg in lst]
        output = [future.result() for future in futures]


            
    print(output)
    send_gotify_message(str(output))
    



# Savills only allow to book 30 days in advance and at exactly 00:00 therefore have to set this call
def savills_booking_schedule(arg):
    import time
    from gettime import get_timezone
    
    if len(arg) != 6:    
        print(f"python savills.py (hour) (day in week Sat is 5) (month) (year=2024) (wait=1)")
        print("If wait = 1 it will wait till 00:00 to start")
        exit()
    hour = int(arg[1])
    dayinweek = int(arg[2])
    month = int(arg[3])
    year = int(arg[4])
    if arg[5] == "1":
        wait = True
    else:
        wait = False
    if wait:
        while True:
            now = datetime.datetime.now(tz=get_timezone())
            print(now)
            if now.hour == 0 and now.minute == 0 and now.second == 0:
                break
            time.sleep(1)
    
    test_multiple_booking_parallel(hour=hour,dayinweek=dayinweek,month=month,year=year)


    
if __name__ == "__main__":

    ## replace with your username and password
    from config import USERNAME,PASSWORD
    start = time.time()
    savills = Savills(USERNAME,PASSWORD)
    print(f"Login time {time.time() - start}")
    start = time.time()


    savills_booking_schedule(sys.argv)
    print('All Done')
    send_gotify_message("Booking run finished (All Done).")
