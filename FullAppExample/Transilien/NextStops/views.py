from django.shortcuts import render
from django.http import HttpResponse, HttpResponseServerError

import sys
import os.path

from . import transilien

# Some configuration variables and one-shot init code.
WATCHED_STATION = 87393306
STATIONS_REFERENCES = transilien.getStationsReferences(
    os.path.join( os.path.dirname( sys.modules[__name__].__file__ ), "referentiel-gares-IdF.csv" ) )


def nextStops( request ):
    # Get the next trains from Issy Val de Seine train stop.
    rawTrains = transilien.getNextTrainsFromServer( WATCHED_STATION )
    if rawTrains:
        # Convert the Transilien raw data to a Python object.
        trains = transilien.parseNextTrains( rawTrains )

        # Convert the trains model to a pure string model better suited for the HTML template.
        templateTrains = []
        for train in trains:
            templateTrain = {}

            templateTrain['time']     = train['date'].strftime( "%H:%M" )
            templateTrain['number']   = str(train['number'])
            templateTrain['mission']  = train['mission']
            templateTrain['terminus'] = STATIONS_REFERENCES[train['terminus']]
            templateTrain['state']    = train.get('state', '' )

            templateTrains.append( templateTrain )

        # Build a context for the template (templates can only take a dictionary, not a list).
        context = {
            "station" : STATIONS_REFERENCES[WATCHED_STATION],
            "trains"  : templateTrains
        }

        # Render the answer using the HTML template.
        return render( request, 'NextStops/index.html', context )
    else:
        return HttpResponseServerError( "Internal error: impossible to get train list!" )
