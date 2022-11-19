from twitchio.ext import commands, routines
import requests
import json
import os

class Bot(commands.Bot):

    def __init__(self):
        self.partidas = []
        super().__init__(token=os.environ.get('TOKEN'), prefix='?', initial_channels=[os.environ.get('CHANNEL')])

    def api_get(self, url):
        try:            
            response_API = requests.get(url)
            toText = response_API.text
            parsed = json.loads(toText)
            return parsed
        except:
            return False

    async def event_ready(self):
        self.mainChannel = self.connected_channels[0]
        self.matchesCount = 0
        @routines.routine(seconds=13)
        async def partidas(self):
            teams = self.api_get('https://www.checkmategaming.com/api/core/teamsForMember/ad186933-0ddd-55cd-adc1-a0817d5d5695/null/null/null')
            if (not teams): return;
            teamIds = []
            print("-")
            for i in range(len(teams['teams'])):
                # print(teams['teams'][i]['activeChallengesCount'], teams['teams'][i]['name'], teams['teams'][i]['id'])
                currentTeam = teams['teams'][i]['id']
                teamIds.append(currentTeam)
                matchs = self.api_get(f'https://www.checkmategaming.com/api/core/team/{currentTeam}/match-list?team_id={currentTeam}&offset=0&limit=3')
                if (not matchs or not matchs['data'] or not matchs['data']['ladders']): continue;
                scheduled = len(matchs['data']['ladders'][0]['matches'])>1
                # print(f"Partidas en curso: {len(matchs['data']['ladders'][0]['matches']['scheduled']) if scheduled else 0}")
                if scheduled: 
                    for j in range(len((matchs['data']['ladders'][0]['matches']['scheduled']))):
                        match = (matchs['data']['ladders'][0]['matches']['scheduled'][j])
                        matchId = match['id']
                        if (matchId in self.partidas): continue;
                        mode = teams['teams'][i]["isSingleType"] and "1v1" or "2v2"
                        self.partidas.append(matchId)
                        print(f"Partida #{matchId} contra {match['opponent_team_name']}")
                        self.matchesCount += 1
                        print(self.matchesCount)
                        if self.matchesCount == 1: continue;
                        await self.mainChannel.send(f"Nueva partida {mode} contra {match['opponent_team_name']} [ID #{matchId}]")
        partidas.start(self)

bot = Bot()
bot.run()
