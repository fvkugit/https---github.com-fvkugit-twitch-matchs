from twitchio.ext import commands, routines
import requests
import json
import os
from bs4 import BeautifulSoup

class Bot(commands.Bot):
    def __init__(self):
        self.partidas = []
        super().__init__(os.environ.get('TOKEN'), prefix='?', initial_channels=[os.environ.get('CHANNEL')])

    def api_get_json(self, url):
        try:            
            response_API = requests.get(url)
            toText = response_API.text
            parsed = json.loads(toText)
            return parsed
        except:
            return False

    def api_get_text(self, url):
        try:            
            response_API = requests.get(url)
            toText = response_API.text
            return toText
        except:
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


    async def event_ready(self):
        self.mainChannel = self.connected_channels[0]
        self.matchesCount = 0
        @routines.routine(seconds=os.environ.get('TIMER'))
        async def partidas(self):
            print("» Waiting «")

            # Get teams of player 
            teams = self.api_get_json(f'https://www.checkmategaming.com/api/core/teamsForMember/{os.environ.get("UUID")}/null/null/null')
            if (not teams): return;

            # Search for matches on each team
            self.matchesCount += 1 # Counter to prevent announce already started matchs before bot is ready
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
                        if (matchId in self.partidas): continue; # Continue if match was already announced
                        mode = teams['teams'][i]["isSingleType"] and "1v1" or "2v2" # Get match mode
                        self.partidas.append(matchId)
                        if self.matchesCount == 1: continue; # Not announce match on first iteration
                        matchData = self.getMatchData("https://www.checkmategaming.com/es" + match['match_url'])
                        print(f"Nueva partida {mode} BO{matchData['bo']} contra {match['opponent_team_name']} por {matchData['pot']} [ID #{matchId}]")
                        await self.mainChannel.send(f"Nueva partida {mode} BO{matchData['bo']} contra {match['opponent_team_name']} por {matchData['pot']} [ID #{matchId}]")
        partidas.start(self)

bot = Bot()
bot.run()
