import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree
from datetime import datetime

# SNCF Transilien data.
TRANSILIEN_BASE_URL = 'http://api.transilien.com'

# Vault data.
VAULT_BASE_URL = 'http://127.0.0.1:8200'
VAULT_TOKEN    = '53d83fdd-91e9-3107-e66f-845987eddb7e'
VAULT_HEADERS  = { 'X-Vault-Token' : VAULT_TOKEN }


def getStationsReferences( fileName ):
    stationsRef = {}

    with open( fileName, 'rt', encoding='utf-8' ) as f:
        headerPassed = False
        for line in f:
            if headerPassed:
                fields = line.split( ';' )
                if fields[19] != '':
                    stationsRef[int(fields[19])] = fields[1]
            else:
                headerPassed = True

    return stationsRef


def getVaultData( path ):
    resp = requests.get( "%s/v1/secret%s" % (VAULT_BASE_URL, path), headers=VAULT_HEADERS )
    if (resp.status_code / 100) == 2:
        respJson = resp.json()
        return respJson['data']['value']
    else:
        print( "ERROR: Impossible to get Transilien data from Vault (%d: %s)." %
               (resp.status_code, resp.reason) )
        return None


def getTransilienCredentials():
    login    = getVaultData( '/transilien/login' )
    password = getVaultData( '/transilien/password' )

    return ( login, password )


def getNextTrainsFromServer( uic ):
    login, password = getTransilienCredentials()
    if login and password:
        resp = requests.get( "%s/gare/%d/depart/" % (TRANSILIEN_BASE_URL, uic),
                             auth=getTransilienCredentials() )

        if (resp.status_code / 100) == 2:
            return resp.text
        else:
            print( "ERROR: Impossible to get next trains from Transilien (%d: %s)." %
                   (resp.status_code, resp.reason) )
            return None
    else:
        return None


def parseNextTrains( text ):
    trains = []

    doc = xml.etree.ElementTree.fromstring( text )

    for train in doc.findall( 'train' ):
        trainData = {}

        trainData["number"]   = int( train.findtext( 'num' ) )
        trainData["mission"]  = train.findtext( 'miss' )
        trainData["terminus"] = int(train.findtext( 'term' ))

        dateElem = train.find( 'date' )
        trainData["mode"] = dateElem.get( 'mode' )
        trainData["date"] = datetime.strptime( dateElem.text, "%d/%m/%Y %H:%M" )

        state = train.findtext( 'etat' )
        if state:
            trainData["state"] = state

        trains.append( trainData )

    return trains


if __name__ == '__main__':
    stationsRef = getStationsReferences( './referentiel-gares-IdF.csv' )
    rawTrains = getNextTrainsFromServer( 87393306 )
    if rawTrains:
        trains = parseNextTrains( rawTrains )

        for train in trains:
            print( "%d: %s (%s) %s (%s) %s" % (train["number"], train["mission"], stationsRef[train["terminus"]],
                                               train["date"].strftime( "%H:%M" ), train["mode"], train.get("state", "") ) )
