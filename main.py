from twitchio.ext import commands, routines
import requests
import json
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv()


class Bot(commands.Bot):
    def __init__(self):
        self.partidas = []
        self._uuidList = json.loads(os.environ.get("UUID"))
        self._channelList = json.loads(os.environ.get("CHANNEL"))
        self.debugMode = int(os.environ.get('DEBUGMODE'))
        super().__init__(os.environ.get('TOKEN'), prefix='?', initial_channels=self._channelList)

    def dprint(self, msg):
        if self.debugMode: print("[ DEBUG ]", msg)

    def api_get_json(self, url):
        try:            
            response_API = requests.get(url)
            toText = response_API.text
            parsed = json.loads(toText)
            return parsed
        except Exception as e:
            print("ERROR", e)
            return False

    def api_get_text(self, url):
        try:            
            response_API = requests.get(url)
            toText = response_API.text
            return toText
        except Exception as e:
            print("ERROR", e)
            return False

    def getMatchData(self, url):
        raw = self.api_get_text(url)
        matchData = {}
        if not raw: return
        soup = BeautifulSoup(raw, 'html.parser')
        potRaw = soup.findAll("div", text=lambda x: x and x.startswith('$'))
        titleRaw = soup.find(class_="competition-name")
        title = titleRaw.get_text()
        matchData['pot'] = potRaw[0].get_text()
        matchData['bo'] = title.split()[-1]
        return matchData

    def isChannelLive(self, channel):
        self.dprint(f"Checking {channel}'s channel'.")
        try:
            url = "https://api.twitch.tv/helix/streams"
            querystring = {"user_login":channel}
            headers = {
                "Client-ID": os.environ.get('CLIENT'),
                "Authorization": "Bearer " + os.environ.get('TOKEN')
            }
            response = requests.request("GET", url, headers=headers, params=querystring)
            data = response.json()
            if (len(data['data']) == 0):
                self.dprint(f"{channel} is offline, skiping.")
                return False
            else:
                return data['data'][0]['type'] == "live"
        except Exception as e:
            print("ERROR", e)
            return False


    async def event_ready(self):
        self.mainChannel = self.connected_channels[0]
        self.matchesCount = 0
        @routines.routine(seconds=int(os.environ.get('TIMER')))
        async def partidas(self):
            print("» Waiting «")
            self.matchesCount += 1 # Counter to prevent announce already started matchs before bot is ready
            for channelIndex, uuid in enumerate(self._uuidList):
                channel = self.connected_channels[channelIndex]
                
                isLive = self.isChannelLive(channel.name)
                if not isLive: continue;
                
                # Get teams of player 
                teams = self.api_get_json(f'https://www.checkmategaming.com/api/core/teamsForMember/{uuid}/null/null/null')
                if (not teams): return;

                # Search for matches on each team
                for i in range(len(teams['teams'])):
                    currentTeam = teams['teams'][i]['id']

                    # Get matchs of current team
                    matchs = self.api_get_json(f'https://www.checkmategaming.com/api/core/team/{currentTeam}/match-list?team_id={currentTeam}&offset=0&limit=3')
                    if (not matchs or not 'data' in matchs or not 'ladders' in matchs['data'] or matchs['data']['ladders'] == None): continue;
                    
                    # Check if have scheduled matchs on response
                    scheduled = 'scheduled' in matchs['data']['ladders'][0]['matches']
            
                    # Handle data of scheduled match
                    if scheduled: 
                        for j in range(len((matchs['data']['ladders'][0]['matches']['scheduled']))):
                            # Get match data
                            match = (matchs['data']['ladders'][0]['matches']['scheduled'][j])
                            matchId = match['id']
                            if ((matchId in self.partidas) or match['match_status'] != "Scheduled"): continue; # Continue if match was already announced or status isnt Scheduled
                            mode = teams['teams'][i]["isSingleType"] and "1v1" or "2v2" # Get match mode
                            self.partidas.append(matchId)
                            print("» New match «")
                            if self.matchesCount == 1: continue; # Not announce match on first iteration
                            matchData = self.getMatchData("https://www.checkmategaming.com/es" + match['match_url'])
                            channel = self.connected_channels[channelIndex]
                            print(f"Channel: {channel.name}")
                            print(f"Nueva partida contra {match['opponent_team_name']} por {matchData['pot']} de POT [{mode}] [BO{matchData['bo']}] https://www.checkmategaming.com/es/matchfinder-ladder-500-challenge-{matchId}-match-details")
                            await channel.send(f"Nueva partida contra {match['opponent_team_name']} por {matchData['pot']} de POT [{mode}] [BO{matchData['bo']}] https://www.checkmategaming.com/es/matchfinder-ladder-500-challenge-{matchId}-match-details")
        partidas.start(self)

bot = Bot()
bot.run()


