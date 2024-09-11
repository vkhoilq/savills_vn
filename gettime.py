import datetime
import calendar
import pytz

def get_timezone():
    # Create a timezone object for UTC+7
    from dateutil.tz import tzoffset
    tz = tzoffset('UTC+7', 7*3600)  # 7 hours * 3600 seconds/hour
    return tz

def get_day_times(year, month,dayinweek,hour):
    
    """Returns a list of datetime objects for every day in week at hour in the given year and month."""

    # Create a datetime object for the first day of the month

    # Create a timezone object for UTC+7

    tz = get_timezone()
    
    first_day = datetime.datetime(year, month, 1,tzinfo=tz)

    # Find the first Saturday using the weekday() method
    # weekday() returns 0 for Monday, 1 for Tuesday, ..., 6 for Sunday
    while first_day.weekday() != dayinweek:
        first_day += datetime.timedelta(days=1)

    # Create a datetime object for 8:00 AM on the first Saturday
    dest_timeslot = first_day.replace(hour=hour, minute=0, second=0)

    # Calculate the number of days in the month
    days_in_month = calendar.monthrange(year, month)[1]

    # Iterate over the days in the month, adding 7 days each time to get the next Saturday
    dest_timeslots = []
    
    while dest_timeslot.day <= days_in_month and dest_timeslot.month == month:
        dest_timeslots.append(dest_timeslot)
        dest_timeslot += datetime.timedelta(days=7)

    return dest_timeslots

if __name__ == "__main__":
    # Get the Saturday times for December 2024
    december_saturdays = get_day_times(2024, 12,5,8)

    # Convert the datetime objects to strings in the desired format
    saturday_strings = [dt.isoformat() for dt in december_saturdays]

    print(saturday_strings)