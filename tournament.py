#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def deleteMatches():
    """Remove all the match records from the database."""
    db=connect()
    c=db.cursor()
    c.execute("delete from matches")
    c.execute("update player_stats set wins=0,matches=0,byes=0,ties=0")
    c.close()
    db.commit()
    db.close()



def deletePlayers():
    """Remove all the player records from the database."""
    db=connect()
    c=db.cursor()
    c.execute("delete from matches")
    c.execute("delete from player_stats")
    c.execute("delete from players")
    c.close()
    db.commit()
    db.close()


def countPlayers():
    """Returns the number of players currently registered."""
    db=connect()
    c=db.cursor()
    c.execute("select count(*) from players")
    row = c.fetchone()
    c.close()
    db.close()
    return row[0]


def registerPlayer(name):
    """Adds a player to the tournament database.
  
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)
  
    Args:
      name: the player's full name (need not be unique).
    """
    db=connect()
    c=db.cursor()
    c.execute("insert into players(name) values (%s) returning id",(name,))
    result=c.fetchone()
    if result[0] == None :
        print "Registration failed"
    else :
        c.execute("insert into player_stats(player,wins,matches,byes,ties)values (%s,0,0,0,0)",(result[0],))
    c.close()
    db.commit()
    db.close()


def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches, ties, byes):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played, including byes
        ties: the number of matches the player has tied
        byes: the number of byes a player has received.
    """
    db=connect()
    c=db.cursor()
    c.execute("""select id, name, wins, matches, ties, byes from players,player_stats
		   where players.id=player_stats.player order by wins desc, byes asc, ties desc""")
    standings = c.fetchall()
    db.close()
    return(standings);


def reportMatch(match, player1, result):
    """Records the outcome of a single match between two players.

    Args:
      match:  unique match identifier 
      player1: id of player1 
      result:  result relative to player1, bye, tie, win or loss

    Return True if successfully updated, otherwise False
    """
    db=connect()
    c=db.cursor()
    ret=True
    try:
        c.execute("""select * from matches where id=%s and 
		player1=%s""",(match,player1))
	row=c.fetchone()
	if row[4] != None:
            raise ValueError('Match already reported')
        #update matches table with result
        c.execute("""update matches set result=%s where id=%s and 
			player1=%s""",(result,match,player1))
        # update player_stats  table
        if result == 'win':
            c.execute("""update player_stats set wins=wins+1,
				matches=matches+1 where player=%s""",
				(player1,))
            c.execute("""update player_stats set 
				matches=matches+1 where player=%s""",
				(row[3],))
	elif result == 'loss': 
            c.execute("""update player_stats set wins=wins+1,
				matches=matches+1 where player=%s""",
				(row[3],))
            c.execute("""update player_stats set 
				matches=matches+1 where player=%s""",
				(player1,))
	elif result == 'tie':
            c.execute("""update player_stats set ties=ties+1,
				matches=matches+1 where player=%s""",
				(player1,))
            c.execute("""update player_stats set ties=ties+1,
				matches=matches+1 where player=%s""",
				(row[3],))
        else:
            raise ValueError('Invalid match result')
	db.commit()
    except ValueError as err:
       print err
       ret = False

    c.close()
    db.close()
    return ret
 
 
def swissPairings():
    """Returns a list of pairs of players for the next round of a match.
  
    Players with the same number of wins are paired.  If there are an odd number of players with
    the same number of wins, one player is assigned a bye.  Players should not be assigned more than one bye.
  
    Returns:
      A list of tuples, each of which contains (match, id1, name1, id2, name2)
        match: match number
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id or 'bye'
        name2: the second player's name or null
    """
    db=connect()
    c=db.cursor()
    match_list=[]
    try:
        c.execute("""select max(wins),max(matches) from player_stats""")
	maxes=c.fetchone();
	if maxes[0] == 0:
            """first round, get number of players and assign consecutive players to a match 
               if odd number of players, assign one player a bye
            """
            next_round=1
            count=countPlayers()

            if count < 2:
                raise ValueError('Not enough players')
                
            c.execute("""select * from players""")
            players=c.fetchall()
            start=0
            if count%2 != 0 :
                # uneven number of entries, first player will get bye
                start=1
                c.execute("""insert into matches(round,player1,result)
                                    values (1,%s,%s)""",(players[0][0],'bye'))
                c.execute("""update player_stats set wins=wins+1, matches=matches+1, byes=byes+1 
                                    where player=%s""",(players[0][0],))
            for player in range(start,count,2):
                c.execute("""insert into matches(round,player1,player2)
                             values (1,%s,%s)""",(players[player][0],players[player+1][0]))
              
        else:              
            next_round = maxes[1]+1
            max_win = maxes[0]
            # group players with the same number of wins
            groups=[]
            for num_wins in range(0,max_win+1):
                c.execute("""select player, wins, ties, byes 
                            from player_stats where wins=%s 
                            order by wins desc, byes asc, ties desc""",(num_wins,))
                groups.append(c.fetchall())
            for group in range(0,len(groups)):
                count=len(groups[group])
                start=0
                if count < 2:
                    if group == max_win :
                        raise ValueError('Tournament over')
                    else:
                        continue
                if (count%2) != 0 :
                    """ uneven number of entries, first player will get bye
                              since select order put byes at end.
                    """   
                    start=1
                    c.execute("""insert into matches(round,player1,result)
                                    values (%s,%s,%s)""",(next_round,groups[group][0][0],'bye'))
                    c.execute("""update player_stats set matches=matches+1, wins=wins+1, byes=byes+1
                                    where player=%s""",(groups[group][0][0],))
                # pair the rest of the players in this group
                for player in range(start,count,2):
                    c.execute("""insert into matches(round,player1,player2)
                               values (%s,%s,%s)""",(next_round,groups[group][player][0],groups[group][player+1][0]))
        db.commit()
        # get list to return
        c.execute("""select matches.id, matches.player1 as id1, p1.name as name1,
                                matches.player2 as id2, p2.name as name2 from matches, players p1,players p2
                                where matches.player1=p1.id and matches.player2=p2.id and round=%s""",(next_round,))
        match_list=c.fetchall()
                            
    except psycopg2.Error as err:
        print err
    except ValueError as err:
        print err
    c.close()
    db.close()
    return match_list
