-- Table definitions for the tournament project.
--
create table players (
	id SERIAL PRIMARY KEY,
	name text
);
create type match_result as ENUM('bye','tie','win','loss');
--match_result is relative to player1, player 2 will be null if result is bye
create table matches (
	id SERIAL PRIMARY KEY,
	round int,
	player1 int references players(id) not null,
	player2 int references players(id),
	result match_result
);

create table player_stats (
	player int references players(id),
	wins int,
	matches int,
	byes int,
	ties int
);
	
	
	

-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.


