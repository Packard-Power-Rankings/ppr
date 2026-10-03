if (typeof fixtureSpec === "undefined") {
  throw new Error("fixtureSpec must be defined before loading this script");
}

if (!Array.isArray(fixtureSpec.datasets) || fixtureSpec.datasets.length !== 6) {
  throw new Error("The full fixture must define all six supported datasets");
}

function yearAdjusted(date, yearOffset) {
  return `${Number(date.slice(0, 4)) + yearOffset}${date.slice(4)}`;
}

function buildTeams(dataset, yearOffset = 0) {
  if (dataset.team_names.length !== 10 || dataset.divisions.length !== 10) {
    throw new Error(`${dataset._id} must contain exactly ten teams and divisions`);
  }
  if (dataset.games.length < 9 || dataset.games.length > 11) {
    throw new Error(`${dataset._id} must contain about ten games`);
  }

  const teams = dataset.team_names.map((teamName, index) => ({
    team_id: index + 1,
    team_name: teamName,
    city: `Fixture City ${index + 1}`,
    state: dataset.state,
    division: dataset.divisions[index],
    conference: dataset.conference,
    division_rank: 0,
    overall_rank: 0,
    power_ranking: [{initial: 125 - index * 4}],
    win_ratio: 0,
    wins: 0,
    losses: 0,
    date: "",
    recent_opp: [0, 0, 0, 0, 0],
    season_opp: []
  }));

  for (const game of dataset.games) {
    const [sourceDate, homeId, awayId, homeScore, awayScore] = game;
    const gameDate = yearAdjusted(sourceDate, yearOffset);
    const home = teams[homeId - 1];
    const away = teams[awayId - 1];
    if (!home || !away || homeId === awayId || homeScore === awayScore) {
      throw new Error(`Invalid game in ${dataset._id}: ${JSON.stringify(game)}`);
    }

    const gameId = `${homeId}_${awayId}_${gameDate}`;
    const margin = Number(((homeScore - awayScore) / 10).toFixed(2));
    const shared = {
      home_score: homeScore,
      away_score: awayScore,
      home_z_score: margin,
      away_z_score: -margin,
      game_date: gameDate,
      game_id: gameId
    };
    home.season_opp.push({
      opponent_id: awayId,
      opponent_name: away.team_name,
      home_team: 1,
      ...shared
    });
    away.season_opp.push({
      opponent_id: homeId,
      opponent_name: home.team_name,
      home_team: 0,
      ...shared
    });

    if (homeScore > awayScore) {
      home.wins += 1;
      away.losses += 1;
    } else {
      away.wins += 1;
      home.losses += 1;
    }
  }

  const latestDate = yearAdjusted(
    dataset.games.map((game) => game[0]).sort().at(-1),
    yearOffset
  );
  for (const team of teams) {
    const played = team.wins + team.losses;
    const currentPower = Number(
      (team.power_ranking[0].initial + team.wins * 1.5 - team.losses).toFixed(2)
    );
    team.power_ranking.push({[latestDate]: currentPower});
    team.win_ratio = played ? Number((team.wins / played).toFixed(3)) : 0;
    team.date = latestDate;
    team.recent_opp = team.season_opp
      .slice(-5)
      .map((game) => game.opponent_id);
    while (team.recent_opp.length < 5) {
      team.recent_opp.unshift(0);
    }
  }

  [...teams]
    .sort((left, right) => {
      const leftPower = Object.values(left.power_ranking.at(-1))[0];
      const rightPower = Object.values(right.power_ranking.at(-1))[0];
      return rightPower - leftPower || left.team_name.localeCompare(right.team_name);
    })
    .forEach((team, index) => {
      team.overall_rank = index + 1;
    });

  for (const division of [...new Set(dataset.divisions)]) {
    teams
      .filter((team) => team.division === division)
      .sort((left, right) => left.overall_rank - right.overall_rank)
      .forEach((team, index) => {
        team.division_rank = index + 1;
      });
  }

  return teams;
}

function buildCsv(dataset) {
  return dataset.games
    .map(([date, homeId, awayId, homeScore, awayScore, neutralSite]) => [
      date,
      dataset.team_names[homeId - 1],
      dataset.team_names[awayId - 1],
      homeScore,
      awayScore,
      neutralSite
    ].join(","))
    .join("\n") + "\n";
}

function buildGames(dataset) {
  const slug = `${dataset.sport_type}-${dataset.gender}-${dataset.level}`;
  const uploadId = `fixture-${slug}`;
  return dataset.games.map(
    ([date, homeId, awayId, homeScore, awayScore, neutralSite]) => ({
      sport_type: dataset.sport_type,
      gender: dataset.gender,
      level: dataset.level,
      identity: `${date}|${Math.min(homeId, awayId)}|${Math.max(homeId, awayId)}`,
      game_id: `${homeId}_${awayId}_${date}`,
      game_date: date,
      home_team_id: homeId,
      home_team: dataset.team_names[homeId - 1],
      away_team_id: awayId,
      away_team: dataset.team_names[awayId - 1],
      home_score: homeScore,
      away_score: awayScore,
      neutral_site: neutralSite,
      home_z_score: Number(((homeScore - awayScore) / 10).toFixed(2)),
      away_z_score: Number(((awayScore - homeScore) / 10).toFixed(2)),
      source_upload_id: uploadId,
      source_filename: `${slug}-fixture.csv`,
      created_at: new Date(`${fixtureSpec.season_year}-01-01T00:00:00Z`),
      updated_at: new Date(`${fixtureSpec.season_year}-01-01T00:00:00Z`)
    })
  );
}

const datasetDocuments = fixtureSpec.datasets.map((dataset) => ({
  _id: ObjectId(dataset._id),
  sport_type: dataset.sport_type,
  gender: dataset.gender,
  level: dataset.level,
  teams: buildTeams(dataset)
}));

const csvDocuments = fixtureSpec.datasets.map((dataset) => {
  const slug = `${dataset.sport_type}-${dataset.gender}-${dataset.level}`;
  const uploadId = `fixture-${slug}`;
  return {
    sport_type: dataset.sport_type,
    gender: dataset.gender,
    level: dataset.level,
    csv_files: [{
      upload_id: uploadId,
      filename: `${slug}-fixture.csv`,
      storage_path: `${dataset.sport_type}/${dataset.gender}/${dataset.level}/${uploadId}-${slug}-fixture.csv`,
      upload_date: new Date(`${fixtureSpec.season_year}-01-01T00:00:00Z`),
      sports_week: dataset.games.at(-1)[0],
      game_count: dataset.games.length
    }]
  };
});

const gameDocuments = fixtureSpec.datasets.flatMap(buildGames);

const flaggedDocuments = fixtureSpec.datasets.map((dataset) => {
  const [date, homeId, awayId] = dataset.games[0];
  return {
    sport_type: dataset.sport_type,
    gender: dataset.gender,
    level: dataset.level,
    flagged_games: [{
      issue_id: `fixture-${dataset.sport_type}-${dataset.gender}-${dataset.level}`,
      game_id: `${homeId}_${awayId}_${date}`,
      team1_id: homeId,
      team1_name: dataset.team_names[homeId - 1],
      team2_id: awayId,
      team2_name: dataset.team_names[awayId - 1],
      description: "Fixture report for testing the admin issue review workflow.",
      reported_at: new Date(`${fixtureSpec.season_year}-01-02T00:00:00Z`),
      status: "open"
    }]
  };
});

const previousSeasonDocuments = fixtureSpec.datasets.map((dataset) => ({
  _id: ObjectId(dataset._id),
  sport_type: dataset.sport_type,
  gender: dataset.gender,
  level: dataset.level,
  teams: buildTeams(dataset, -1)
}));

const app = db.getSiblingDB("sports_data");
app.temp2.deleteMany({});
app.csv_files.deleteMany({});
app.games.deleteMany({});
app.flagged_games.deleteMany({});
app.previous_season.deleteMany({});
app.temp2.insertMany(datasetDocuments);
app.csv_files.insertMany(csvDocuments);
app.games.insertMany(gameDocuments);
app.flagged_games.insertMany(flaggedDocuments);
app.previous_season.insertMany(previousSeasonDocuments);

print(JSON.stringify({
  datasets: datasetDocuments.length,
  teams: datasetDocuments.reduce((total, dataset) => total + dataset.teams.length, 0),
  games: gameDocuments.length,
  csv_files: csvDocuments.reduce((total, dataset) => total + dataset.csv_files.length, 0),
  flagged_games: flaggedDocuments.reduce(
    (total, dataset) => total + dataset.flagged_games.length,
    0
  ),
  previous_season_teams: previousSeasonDocuments.reduce(
    (total, dataset) => total + dataset.teams.length,
    0
  )
}));
