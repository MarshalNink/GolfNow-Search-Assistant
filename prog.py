# GolfNow Search Assistant
# A program that utilizes GolfNow.com to gather all available tee times within 25 miles of a designated zipcode. Output is formatted: Total Price | Tee Time | URL"
# Author: Marshal Nink
# July, 2017
# TODO: add option to set range for tee times

import sys, getopt
from geopy.geocoders import Nominatim
import argparse
import requests
import json
import re

def main(argv):
    months = ["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec",]

    # setup search arguments
    parser = argparse.ArgumentParser(description="A program that utilizes GolfNow.com to gather all available tee times within 25 miles of a designated zipcode. Output is formatted: Total Price | Tee Time | URL")
    parser.add_argument("zipcode", help="5 Digit Zipcode center of the search")
    parser.add_argument("radius", help="Maximum distance (in miles) to search for courses around zipcode")
    parser.add_argument("date", help="Date to search within 1 week from today (mmddyyy) ")
    parser.add_argument("players", help="Number of Golfers (1-4)")
    parser.add_argument("holes", help="Number of Holes desired. 1 = 9 Holes, 2 = 18 Holes, 3 = Either")
    parser.add_argument("maxprice", help="The maximum total price of the round for all golfers")
    parser.add_argument("--estimate", help="Set the \"Estimate\" flag to only search based on base price of the round, excluding additional fees (faster)", action="store_true")
    parser.add_argument("--hotdealsonly", help="Search for only Hot Deals", action="store_true")
    args = parser.parse_args()  # returns data from the options specified (echo)

    # set the variables based on input
    ZIPCODE = args.zipcode
    RADIUS = args.radius
    DATE = args.date
    PLAYERS = args.players
    HOLES = args.holes
    MAX_PRICE = args.maxprice

    geolocator = Nominatim()
    LONGITUDE = geolocator.geocode(ZIPCODE).longitude
    LATITUDE = geolocator.geocode(ZIPCODE).latitude
    ADDRESS = geolocator.geocode(ZIPCODE).address

    if args.hotdealsonly:
        HOTDEALSONLY = "True"
    else:
        HOTDEALSONLY = "False"
    # loop for each day of the week and find courses for each day
    # can only search up to 1 week ahead of time
    print "Searching for Golf Courses near " + ADDRESS

    date = months[int(DATE[0:2])] + " " + DATE[3:5] + " " + DATE[-4:]
    print "Date: " + date
    postData = {"Radius": RADIUS, "Latitude": LATITUDE, "Longitude": LONGITUDE, "PageSize": "30", "PageNumber": "0",
                "SearchType": "GeoLocation", "SortBy": "Facilities.Distance", "SortDirection": "0", "Date": date, "HotDealsOnly":HOTDEALSONLY,
                "Players": PLAYERS, "RateType": "all", "TimeMin": "10", "TimeMax": "47",
                "SortByRollup": "Facilities.Distance", "View": "Course", "ExcludeFeaturedFacilities": "false",
                "Q": ZIPCODE, "QC": "GeoLocation"}

    r = requests.post("https://www.golfnow.com/api/tee-times/tee-time-results", data=postData)
    # print(r.status_code, r.reason)

    filename = "result-" + months[int(DATE[0:2])] + DATE[3:5] + ".txt"
    text_file = open(filename, "w")

    # with open(filename) as result_file:
    data = json.loads(r.text.encode("utf-8"))

    # loop through each facility returned as a result
    for item in data['ttResults']['facilities']:
        print "\n" + item.get('name') + " : " + str(item.get('minPrice'))
        facID = item.get('id')
        # print "facID: " + str(facID)

        # get the list of all facilities
        url2 = "https://www.golfnow.com/api/tee-times/tee-time-results"
        postData2 = {"Radius": RADIUS, "PageSize": "30", "PageNumber": "0", "SearchType": "1", "SortBy": "Date", "HotDealsOnly":HOTDEALSONLY,
                     "SortDirection": "0", "Date": date, "Players": PLAYERS, "TimePeriod": "3", "Holes": HOLES,
                     "RateType": "all", "TimeMin": "10", "TimeMax": "47", "FacilityId": facID,
                     "SortByRollup": "Facilities.Distance", "View": "List", "ExcludeFeaturedFacilities": "false",
                     "Q": ZIPCODE, "QC": "GeoLocation"}
        r2 = requests.post(url2, postData2)

        data2 = json.loads(r2.text.encode("utf-8"))

        # loop through all tee times for that facility
        for item2 in data2['ttResults']['teeTimes']:
            teeTime = item2.get("formattedTime") + item2.get("formattedTimeMeridian")

            pricePerGolfer = float(item2['teeTimeRates'][0]['singlePlayerPrice']['greensFees'].get('value'))

            if (int(pricePerGolfer) > (int(MAX_PRICE) / int(PLAYERS))):
                continue

            url = item2.get("detailurl")
            fullUrl = "https://www.golfnow.com" + item2.get("detailUrl")

            # find tee times based on estimate status
            if args.estimate:
                total = int(pricePerGolfer) * int(PLAYERS)
                temp = "\t" + str(total) + " | " + teeTime + " | " + fullUrl
            else:
                response = requests.get(fullUrl)
                html = response.text
                regex = r'"PlayerCount":' + PLAYERS + '.+?"GrandTotal":"\$(\d+\.\d+?)"'
                mo = re.compile(regex)
                res = mo.findall(html)
                price = float(res[0])

                if price < float(MAX_PRICE):
                    temp = "\t" + str(price) + " | " + teeTime + " | " + fullUrl
                else:
                    continue

            print temp
            text_file.write(temp)

    print "\nsuccess for " + filename + "\n\n"
    text_file.close()

    print "All Done!"

if __name__ == "__main__":
   main(sys.argv[1:])