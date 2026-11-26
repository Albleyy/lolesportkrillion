import json, urllib.request, urllib.parse, time, collections, math
API='https://lol.fandom.com/api.php'
def query(**kw):
    params=dict(action='cargoquery',format='json',**kw)
    req=urllib.request.Request(API+'?'+urllib.parse.urlencode(params),headers={'User-Agent':'KrillionEsport/1.0 (personal educational quiz)'})
    with urllib.request.urlopen(req,timeout=60) as r: data=json.load(r)
    if 'error' in data: raise RuntimeError(data['error'])
    return [x['title'] for x in data['cargoquery']]
def main():
    groups=collections.defaultdict(dict)
    offset=0
    while True:
        rows=query(tables='ScoreboardPlayers',fields='Link=Player,Champion,Team,OverviewPage,IngameRole,COUNT(*)=Games',group_by='Link,Champion,Team,OverviewPage,IngameRole',order_by='Link,Champion,Team,OverviewPage,IngameRole',limit=500,offset=offset)
        for r in rows:
            player=r['Player']; champ=r['Champion']; team=r['Team']; event=r['OverviewPage']; role=r['IngameRole']; count=int(r['Games'])
            if not player or not event: continue
            keys=[('Champions',f'Cite un joueur ayant joué {champ} en compétition.') ] if champ else []
            if team: keys.append(('Équipes',f'Cite un joueur ayant joué pour {team}.'))
            keys.append(('Tournois',f'Cite un joueur ayant joué au tournoi {event}.'))
            if champ and role: keys.append(('Postes',f'Cite un joueur ayant joué {champ} au poste {role}.'))
            for key in keys:
                old=groups[key].get(player,(0,event)); groups[key][player]=(old[0]+count,old[1])
        offset+=len(rows); print(offset,flush=True)
        if len(rows)<500: break
        time.sleep(1.5)
    bank=[]
    for (category,q), players in sorted(groups.items()):
        if len(players)<10: continue
        maxn=max(n for n,s in players.values()); entries=[]
        for player,(n,source) in sorted(players.items()):
            name=player.split(' (')[0]; points=round(100-80*math.log(n)/max(1,math.log(maxn)))
            entries.append(dict(names=[player,name],p=points,source=source,games=n))
        bank.append([category,q,entries])
    with open('bank.json','w',encoding='utf8') as f: json.dump(bank,f,ensure_ascii=False)
    print(len(bank),'questions')
if __name__=='__main__': main()
